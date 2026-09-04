"""
OpenAI AI Provider — Phase B Real AI Integration.

Uses OpenAI GPT-4o-mini for semantic requirement analysis and improvement.
Structured JSON output via response_format={"type": "json_object"}.

SECURITY: OPENAI_API_KEY is read exclusively from backend environment.
Never logged, never serialized, never exposed to frontend.

Reliability:
- 30s timeout per request
- 2 retries with exponential backoff
- Schema validation on all LLM responses
- Fallback to HeuristicsAIProvider on any failure
"""

import json
import logging
import re
from typing import Optional

from app.core.ai.provider_interface import AnalysisResult, BaseAIProvider, ImprovementResult
from app.core.ai.heuristics_provider import HeuristicsAIProvider

logger = logging.getLogger(__name__)

# Lazy import — openai may not be installed in all environments
_openai_module = None

def _get_openai():
    global _openai_module
    if _openai_module is None:
        try:
            import openai
            _openai_module = openai
        except ImportError:
            raise ImportError(
                "openai is not installed. Run: pip install openai>=1.0.0"
            )
    return _openai_module


def _validate_no_hallucinated_thresholds(original_desc: str, improved_desc: str) -> bool:
    """Returns True if LLM has NOT injected new numeric thresholds."""
    orig_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", original_desc))
    new_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", improved_desc))
    invented = new_numbers - orig_numbers
    if invented:
        logger.warning(
            "OpenAI hallucination guard: invented values %s — rejecting.", invented
        )
        return False
    return True


class OpenAIAIProvider(BaseAIProvider):
    """OpenAI GPT provider for semantic requirement analysis.

    Uses gpt-4o-mini with JSON mode. Falls back to HeuristicsAIProvider on any error.
    """

    ANALYZE_SYSTEM = """You are a software requirements quality analyst. Your job is to evaluate
software requirements strictly and return structured JSON feedback.

Rules:
- Analyze ONLY the description field. Do NOT flag words from the title.
- Flag genuinely vague terms: fast, user-friendly, scalable, secure, quick, intuitive, reasonable.
- Non-functional requirements without measurable thresholds should score < 70.
- User stories without "As a / I want / so that" format should note the issue.
- Do NOT invent thresholds, business rules, or constraints not in the original text.
- Return only valid JSON."""

    ANALYZE_USER = """Analyze this requirement:
Type: {req_type}
Title: {title}
Description: {description}

Return JSON with: quality_score (0-100), ambiguity_tags (list), passive_voice_instances (list), missing_criteria (list), summary_feedback (string)."""

    IMPROVE_SYSTEM = """You are a software requirements engineer specializing in EARS syntax.

Rules:
- EARS Ubiquitous: "The <system> shall <response>."
- EARS Event-Driven: "WHEN <trigger>, the <system> shall <response>."
- Use "The SRSense System" as the system name.
- Do NOT invent measurable thresholds not present in the original.
- Do NOT change fundamental intent.
- If already in valid EARS format, return unchanged.
- Return only valid JSON."""

    IMPROVE_USER = """Rewrite this requirement in EARS syntax:
Type: {req_type}
Title: {title}
Description: {description}

Return JSON with: improved_title, improved_description, ears_template_used, explanation."""

    def __init__(self, api_key: str, timeout: int = 30, max_retries: int = 2):
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._fallback = HeuristicsAIProvider()
        self._client = None

    def _get_client(self):
        if self._client is None:
            openai = _get_openai()
            self._client = openai.AsyncOpenAI(
                api_key=self._api_key,
                timeout=self._timeout,
                max_retries=self._max_retries,
            )
        return self._client

    async def _call_with_retry(self, system: str, user: str) -> Optional[dict]:
        """Call OpenAI API. Returns parsed JSON or None."""
        import asyncio

        for attempt in range(self._max_retries + 1):
            try:
                client = self._get_client()
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.1,
                )
                text = response.choices[0].message.content or ""
                return json.loads(text)
            except json.JSONDecodeError as e:
                logger.warning("OpenAI returned invalid JSON: %s", e)
                return None
            except Exception as e:
                logger.warning("OpenAI API error on attempt %d: %s", attempt + 1, e)
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** attempt)
        return None

    async def analyze_requirement(
        self, title: str, description: str, req_type: str
    ) -> AnalysisResult:
        """Analyze with OpenAI. Falls back to heuristics on failure."""
        try:
            user = self.ANALYZE_USER.format(req_type=req_type, title=title, description=description)
            data = await self._call_with_retry(self.ANALYZE_SYSTEM, user)
            if data is None:
                raise ValueError("No valid response from OpenAI")

            missing = list(data.get("missing_criteria", []))
            score = max(0, min(100, int(data.get("quality_score", 70))))
            feedback = str(data.get("summary_feedback", "OpenAI analysis complete."))

            MALFORMED_EARS_PATTERNS = [
                r"\bshall the system should\b",
                r"\bshall\b.{1,25}?\b(should|must|will|shall)\b",
                r"\bshall the\b",
                r"\bshall (the system|the application|the service|the user)\b",
                r"\bshould be respond\b",
                r"\bshall (should|must|will)\b",
                r"\bthe srsense system shall the\b",
            ]
            if any(re.search(p, description.lower(), re.IGNORECASE) for p in MALFORMED_EARS_PATTERNS):
                missing.append(
                    "Malformed EARS syntax detected: requirement contains duplicated subject/modal ('shall the system should'). Re-run AI improvement to regenerate."
                )
                score = min(score, 60)
                feedback = "Needs improvement. Malformed EARS syntax detected: specification contains a doubled subject or stacked modal verbs ('shall the system should')."

            return AnalysisResult(
                quality_score=score,
                ambiguity_tags=list(data.get("ambiguity_tags", [])),
                passive_voice_instances=list(data.get("passive_voice_instances", [])),
                missing_criteria=missing,
                summary_feedback=feedback,
            )
        except Exception as e:
            logger.warning("OpenAI analyze_requirement failed, using heuristics: %s", e)
            return await self._fallback.analyze_requirement(title, description, req_type)

    async def suggest_improvement(
        self, title: str, description: str, req_type: str
    ) -> ImprovementResult:
        """Improve with OpenAI. Includes hallucination protection. Falls back to heuristics."""
        try:
            user = self.IMPROVE_USER.format(req_type=req_type, title=title, description=description)
            data = await self._call_with_retry(self.IMPROVE_SYSTEM, user)
            if data is None:
                raise ValueError("No valid response from OpenAI")

            improved_desc = str(data.get("improved_description", description))

            # Hallucination protection
            if not _validate_no_hallucinated_thresholds(description, improved_desc):
                logger.warning("OpenAI hallucination detected for '%s'. Using heuristics.", title)
                return await self._fallback.suggest_improvement(title, description, req_type)

            return ImprovementResult(
                improved_title=str(data.get("improved_title", title)),
                improved_description=improved_desc,
                ears_template_used=str(data.get("ears_template_used", "Ubiquitous")),
                explanation=str(data.get("explanation", "Improved using OpenAI semantic analysis.")),
            )
        except Exception as e:
            logger.warning("OpenAI suggest_improvement failed, using heuristics: %s", e)
            return await self._fallback.suggest_improvement(title, description, req_type)
