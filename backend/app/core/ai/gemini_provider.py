"""
Gemini AI Provider — Phase B Real AI Integration.

Uses Google Gemini API for semantic requirement analysis, conflict detection,
and contextual improvement suggestions.

SECURITY: GEMINI_API_KEY is read exclusively from backend environment.
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

# Lazy import — google-generativeai may not be installed in all environments
_genai = None

def _get_genai():
    global _genai
    if _genai is None:
        try:
            import google.generativeai as genai
            _genai = genai
        except ImportError:
            raise ImportError(
                "google-generativeai is not installed. "
                "Run: pip install google-generativeai"
            )
    return _genai


# Hallucination protection — reject any output that invented these
FORBIDDEN_INVENTIONS = [
    r"\b(\d+)\s*(?:ms|milliseconds?)\b",  # numeric thresholds injected by LLM
    r"\b(\d+)\s*(?:concurrent|requests?)\b",
    r"\b(\d+(?:\.\d+)?)\s*%\b",
]


def _validate_no_hallucinated_thresholds(
    original_desc: str, improved_desc: str
) -> bool:
    """Returns True if improved_desc has NOT injected new numeric thresholds
    that did not exist in the original description.

    This prevents the LLM from inventing "200ms", "99.9%", etc. when
    the original requirement had no such numbers.
    """
    orig_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", original_desc))
    new_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", improved_desc))
    invented = new_numbers - orig_numbers
    if invented:
        logger.warning(
            "Gemini hallucination guard: LLM invented numeric values %s — rejecting output.",
            invented,
        )
        return False
    return True


class GeminiAIProvider(BaseAIProvider):
    """Google Gemini AI provider for semantic requirement analysis.

    Falls back to HeuristicsAIProvider on any API failure.
    """

    ANALYZE_PROMPT = """You are a software requirements quality analyst. Analyze the following requirement.

Type: {req_type}
Title: {title}
Description: {description}

Return ONLY a valid JSON object with exactly these fields:
{{
  "quality_score": <integer 0-100>,
  "ambiguity_tags": [<list of strings describing vague terms>],
  "passive_voice_instances": [<list of passive voice constructs found>],
  "missing_criteria": [<list of missing elements>],
  "summary_feedback": "<one sentence feedback>"
}}

Rules:
- Analyze ONLY the description. Do NOT flag words from the title.
- Flag truly vague terms: "fast", "user-friendly", "scalable", "secure", "quick", "intuitive".
- Non-functional requirements without measurable thresholds should score < 70.
- User stories without "As a / I want / so that" format should note the issue.
- Do NOT invent thresholds. Do NOT add business rules not present in the text.
- Return ONLY the JSON object. No markdown, no explanation."""

    IMPROVE_PROMPT = """You are a software requirements engineer. Rewrite the following requirement using EARS syntax.

Type: {req_type}
Title: {title}
Description: {description}

EARS syntax rules:
- Ubiquitous: "The <system> shall <response>."
- Event-Driven: "WHEN <trigger>, the <system> shall <response>."
- Use "The SRSense System" as the system name.

Rules:
- Do NOT invent measurable thresholds (ms, %, concurrent users) not present in the original.
- Do NOT change the fundamental intent of the requirement.
- Do NOT add business rules not implied by the original text.
- Replace genuinely vague terms only if a natural EARS restatement is obvious.
- If already in EARS format, return it unchanged.

Return ONLY a valid JSON object:
{{
  "improved_title": "<title>",
  "improved_description": "<EARS-formatted description>",
  "ears_template_used": "<template name>",
  "explanation": "<one sentence explanation>"
}}"""

    def __init__(self, api_key: str, timeout: int = 30, max_retries: int = 2):
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._fallback = HeuristicsAIProvider()
        self._model = None

    def _get_model(self):
        if self._model is None:
            genai = _get_genai()
            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(
                model_name="gemini-flash-latest",
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
        return self._model

    async def _call_with_retry(self, prompt: str) -> Optional[dict]:
        """Call Gemini API with retry and timeout. Returns parsed JSON or None."""
        import asyncio

        for attempt in range(self._max_retries + 1):
            try:
                model = self._get_model()
                # Run the synchronous Gemini call in a thread executor
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: model.generate_content(prompt)),
                    timeout=self._timeout,
                )
                text = response.text.strip()
                # Strip markdown code fences if present
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
                return json.loads(text)
            except asyncio.TimeoutError:
                logger.warning("Gemini timeout on attempt %d/%d", attempt + 1, self._max_retries + 1)
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** attempt)
            except json.JSONDecodeError as e:
                logger.warning("Gemini returned invalid JSON: %s", e)
                return None
            except Exception as e:
                logger.warning("Gemini API error on attempt %d: %s", attempt + 1, e)
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** attempt)
        return None

    async def analyze_requirement(
        self, title: str, description: str, req_type: str
    ) -> AnalysisResult:
        """Analyze requirement using Gemini. Falls back to heuristics on failure."""
        try:
            prompt = self.ANALYZE_PROMPT.format(
                req_type=req_type, title=title, description=description
            )
            data = await self._call_with_retry(prompt)
            if data is None:
                raise ValueError("No valid response from Gemini")

            missing = list(data.get("missing_criteria", []))
            score = max(0, min(100, int(data.get("quality_score", 70))))
            feedback = str(data.get("summary_feedback", "Gemini analysis complete."))

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
            logger.warning("Gemini analyze_requirement failed, using heuristics fallback: %s", e)
            return await self._fallback.analyze_requirement(title, description, req_type)

    async def suggest_improvement(
        self, title: str, description: str, req_type: str
    ) -> ImprovementResult:
        """Improve requirement using Gemini. Falls back to heuristics on failure.
        Includes hallucination protection: rejects invented numeric thresholds."""
        try:
            prompt = self.IMPROVE_PROMPT.format(
                req_type=req_type, title=title, description=description
            )
            data = await self._call_with_retry(prompt)
            if data is None:
                raise ValueError("No valid response from Gemini")

            improved_desc = str(data.get("improved_description", description))

            # Hallucination protection: reject if LLM invented new numeric thresholds
            if not _validate_no_hallucinated_thresholds(description, improved_desc):
                logger.warning(
                    "Gemini hallucination detected in improvement for '%s'. Using heuristics.", title
                )
                return await self._fallback.suggest_improvement(title, description, req_type)

            return ImprovementResult(
                improved_title=str(data.get("improved_title", title)),
                improved_description=improved_desc,
                ears_template_used=str(data.get("ears_template_used", "Ubiquitous")),
                explanation=str(data.get("explanation", "Improved using Gemini semantic analysis.")),
            )
        except Exception as e:
            logger.warning("Gemini suggest_improvement failed, using heuristics fallback: %s", e)
            return await self._fallback.suggest_improvement(title, description, req_type)
