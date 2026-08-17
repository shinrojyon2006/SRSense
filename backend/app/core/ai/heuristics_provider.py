"""
Heuristics-based AI Analysis Provider.

Provides fast, deterministic NLP analysis for requirement quality scoring,
ambiguity detection, and EARS specification formatting.
"""

import re
from typing import List

from app.core.ai.provider_interface import (
    AnalysisResult,
    BaseAIProvider,
    ImprovementResult,
)

VAGUE_TERMS = [
    "fast",
    "user-friendly",
    "user friendly",
    "flexible",
    "adequate",
    "etc",
    "as far as possible",
    "real-time",
    "real time",
    "seamless",
    "robust",
    "easy",
    "efficient",
    "state-of-the-art",
    "intuitive",
    "lightweight",
    "scalable",
    "appropriate",
]

PASSIVE_PATTERN = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+([a-z]+ed|[a-z]+en)\b",
    re.IGNORECASE,
)

IMPERATIVE_VERBS = ["shall", "must", "should"]

# Metric patterns for non-functional requirements (units, percentages, times, numbers)
METRIC_PATTERNS = re.compile(
    r"\b(?:\d+(?:\.\d+)?\s*(?:ms|milliseconds?|sec|seconds?|min|minutes?|hrs?|hours?|%|percent|concurrent|req/s|tps|mb|gb|tb|uptime)|24/7)\b",
    re.IGNORECASE,
)


class HeuristicsAIProvider(BaseAIProvider):
    """Deterministic heuristic AI analysis engine."""

    async def analyze_requirement(
        self, title: str, description: str, req_type: str
    ) -> AnalysisResult:
        """Run type-aware deterministic rule-based analysis on requirement description."""
        desc_clean = description.strip()
        desc_lower = desc_clean.lower()
        req_type_clean = (req_type or "functional").lower()

        # 1. Ambiguity Detection (Strictly on Description)
        ambiguity_tags = []
        for term in VAGUE_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", desc_lower):
                ambiguity_tags.append(f"Vague Term: '{term}'")

        # 2. Passive Voice Detection (Strictly on Description)
        passive_matches = PASSIVE_PATTERN.findall(desc_clean)
        passive_instances = [
            f"Passive construct detected: '{match}'" for match in set(passive_matches)
        ]

        # 3. Type-Aware Missing Criteria Check
        missing_criteria = []
        has_imperative = any(v in desc_lower for v in IMPERATIVE_VERBS)

        # Description length check (must be at least 30 characters)
        if len(desc_clean) < 30:
            missing_criteria.append("Description is too brief (< 30 characters)")

        # Mandatory imperative modal verb check for functional, non-functional, system
        if req_type_clean in ("functional", "non_functional", "system") and not has_imperative:
            missing_criteria.append("Lacks imperative modal verb (shall / must / should)")

        # Type-specific rules:
        if req_type_clean == "non_functional":
            # Non-functional requirements prioritize measurability & numbers over event triggers
            has_metric = bool(METRIC_PATTERNS.search(desc_lower)) or bool(re.search(r"\b\d+\b", desc_lower))
            if not has_metric:
                missing_criteria.append(
                    "Non-functional requirement lacks quantitative metric or threshold (e.g., ms, %, concurrent users)"
                )
        elif req_type_clean == "user":
            # User stories evaluate against "As a / I want / So that" template
            has_as_a = "as a" in desc_lower
            has_want = "i want" in desc_lower or "i need" in desc_lower
            has_so_that = "so that" in desc_lower or "in order to" in desc_lower
            if not (has_as_a and has_want and has_so_that):
                missing_criteria.append(
                    "User story does not follow standard format: 'As a [role], I want [goal], so that [benefit]'"
                )
        elif req_type_clean == "business":
            # Business requirements evaluate for business objectives & value
            has_objective = any(
                w in desc_lower for w in ["reduce", "increase", "enable", "achieve", "improve", "provide", "ensure", "allow", "target"]
            )
            if not has_objective:
                missing_criteria.append(
                    "Business requirement lacks clear objective or measurable business outcome"
                )
        else:  # Functional / System
            # Functional requirements recommend triggers when event-driven
            has_trigger = any(w in desc_lower for w in ["given", "when", "if", "while"])
            if not has_trigger and "shall" not in desc_lower:
                missing_criteria.append("Lacks clear trigger or precondition (given / when / if)")

        # 4. Quality Score Calculation (0 - 100)
        deductions = 0
        deductions += min(30, len(ambiguity_tags) * 10)
        deductions += min(20, len(passive_instances) * 10)
        if len(desc_clean) < 30:
            deductions += 15
        if req_type_clean in ("functional", "non_functional", "system") and not has_imperative:
            deductions += 15
        if any("lacks" in c.lower() or "does not follow" in c.lower() for c in missing_criteria):
            deductions += 15

        quality_score = max(0, min(100, 100 - deductions))

        # 5. Feedback Summary
        if quality_score >= 85:
            summary = f"Excellent {req_type_clean.replace('_', '-')} requirement specification! Clear, measurable, and well-structured."
        elif quality_score >= 70:
            summary = f"Good {req_type_clean.replace('_', '-')} requirement, but contains minor ambiguity or structural opportunities."
        else:
            summary = f"Needs improvement. Specification contains ambiguous terminology, passive voice, or lacks key {req_type_clean.replace('_', '-')} criteria."

        return AnalysisResult(
            quality_score=quality_score,
            ambiguity_tags=ambiguity_tags,
            passive_voice_instances=passive_instances,
            missing_criteria=missing_criteria,
            summary_feedback=summary,
        )

    async def suggest_improvement(
        self, title: str, description: str, req_type: str
    ) -> ImprovementResult:
        """Format requirement using EARS (Easy Approach to Requirements Syntax)."""
        raw_desc = description.strip()

        # 1. Detect Trigger / Precondition (e.g. "When ...," or "If ...,")
        trigger = ""
        main_clause = raw_desc

        trigger_match = re.match(
            r"^(when|if|while|given)\s+(.+?),\s*(.+)$", raw_desc, re.IGNORECASE
        )
        if trigger_match:
            keyword = trigger_match.group(1).upper()
            condition = trigger_match.group(2).strip()
            trigger = f"{keyword} {condition}"
            main_clause = trigger_match.group(3).strip()

        # 2. Strip leading subject and modal verb constructs from main clause
        cleaned = re.sub(
            r"^(?:the\s+srsense\s+system|the\s+system|the\s+application|the\s+software|the\s+platform|system|application|software)\s+(?:shall|should|must|will|can|is\s+required\s+to|needs\s+to)\s+(?:be\s+able\s+to|be\s+allowed\s+to|be\s+capable\s+of)?\s*",
            "",
            main_clause,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"^(?:users?)\s+(?:shall|should|must|can|will|is\s+required\s+to|needs\s+to)\s+(?:be\s+able\s+to|be\s+allowed\s+to)?\s*",
            "allow users to ",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"^(?:shall|should|must|will)\s+(?:be\s+able\s+to|be)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        # If it starts with "be ", strip "be "
        cleaned = re.sub(r"^be\s+", "", cleaned, flags=re.IGNORECASE).strip()

        # 3. Perform phrase-level vague term replacements
        cleaned = re.sub(
            r"\bin\s+real[- ]time\b", "within 200 milliseconds", cleaned, flags=re.IGNORECASE
        )
        cleaned = re.sub(
            r"\breal[- ]time\b", "within 200 milliseconds", cleaned, flags=re.IGNORECASE
        )
        cleaned = re.sub(
            r"\b(fast|quick)\b", "respond within 200 milliseconds", cleaned, flags=re.IGNORECASE
        )
        cleaned = re.sub(
            r"\b(user[- ]friendly|intuitive|easy)\b",
            "require no more than 3 user interactions",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\bseamless(?:ly)?\b",
            "without manual user intervention",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\b(robust|scalable)\b",
            "support up to 10,000 concurrent requests without failure",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\b(flexible|adequate|appropriate)\b",
            "conform to defined system policy specifications",
            cleaned,
            flags=re.IGNORECASE,
        )

        # Cleanup double spaces or trailing periods
        cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".")

        # Ensure first character of action verb is lowercase if appropriate
        if cleaned:
            cleaned = cleaned[0].lower() + cleaned[1:]

        # 4. Reconstruct EARS Syntax
        if trigger:
            improved_desc = f"{trigger}, the SRSense System shall {cleaned}."
            ears_template = "Event-Driven: WHEN <trigger>, the <system name> shall <system response>."
        else:
            improved_desc = f"The SRSense System shall {cleaned}."
            ears_template = "Ubiquitous: The <system name> shall <system response>."

        explanation = (
            "Refactored sentence using valid EARS syntax, removing duplicated subjects/modals "
            "and replacing ambiguous terms with quantifiable performance benchmarks."
        )

        return ImprovementResult(
            improved_title=title,
            improved_description=improved_desc,
            ears_template_used=ears_template,
            explanation=explanation,
        )
