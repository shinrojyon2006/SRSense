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
        has_trigger = any(w in desc_lower for w in ["given", "when", "if", "while", "upon", "whenever"])

        # Description length check (must be at least 30 characters)
        if len(desc_clean) < 30:
            missing_criteria.append("Description is too brief (< 30 characters)")

        # Mandatory imperative modal verb check for functional, non-functional, system
        if req_type_clean in ("functional", "non_functional", "system") and not has_imperative:
            missing_criteria.append("Lacks imperative modal verb (shall / must / should)")

        # Type-specific & Semantic Completeness rules:
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
            if not has_trigger and "shall" not in desc_lower:
                missing_criteria.append("Lacks clear trigger or precondition (given / when / if)")

        # Semantic Completeness & Context Verification:
        # Check interaction limits without workflow context
        has_response_time = bool(re.search(r"\b(respond within|response time|latency within)\b", desc_lower))
        has_interaction_limit = bool(re.search(r"\b\d+\s*(?:user\s+interactions?|interactions?|clicks?|steps?|screens?)\b", desc_lower))
        has_workflow_context = any(w in desc_lower for w in ["checkout", "login", "auth", "search", "registration", "signup", "export", "payment", "task", "process", "workflow", "journey", "flow", "during", "when", "upon"])
        if has_interaction_limit and not has_workflow_context:
            missing_criteria.append("Lacks specific user workflow or task for measuring user interaction limits")
            if has_response_time and not has_trigger:
                missing_criteria.append("Lacks specific operation or trigger context for response time verification")

        # 4. A8 FIX: Detect malformed EARS output (structural corruption indicator).
        # A double-prefixed requirement like "The SRSense System shall the system should be..."
        # is syntactically broken. Detect and penalize heavily — must NOT score 100/100.
        MALFORMED_EARS_PATTERNS = [
            r"\bshall the system should\b",              # exact duplicated subject/modal
            r"\bshall\b.{1,25}?\b(should|must|will|shall)\b",  # modal stacking within same clause
            r"\bshall the\b",                            # "shall the" — prefix-into-subject
            r"\bshall (the system|the application|the service|the user)\b",  # "shall the system ..."
            r"\bshould be respond\b",                   # common malformed artifact
            r"\bshall (should|must|will)\b",             # modal stacking
            r"\bthe srsense system shall the\b",
        ]
        is_malformed_ears = any(
            re.search(p, desc_lower, re.IGNORECASE) for p in MALFORMED_EARS_PATTERNS
        )
        if is_malformed_ears:
            missing_criteria.append(
                "Malformed EARS syntax detected: requirement contains duplicated subject/modal ('shall the system should'). "
                "Re-run AI improvement to regenerate."
            )

        # 5. Quality Score Calculation (0 - 100)
        deductions = 0
        deductions += min(30, len(ambiguity_tags) * 10)
        deductions += min(20, len(passive_instances) * 10)
        if len(desc_clean) < 30:
            deductions += 15
        if req_type_clean in ("functional", "non_functional", "system") and not has_imperative:
            deductions += 15
        
        # Deduct for missing completeness/context criteria (15 pts per missing substantive criteria, max 30)
        substantive_missing = [c for c in missing_criteria if not c.startswith("Malformed")]
        if substantive_missing:
            deductions += min(30, len(substantive_missing) * 15)

        if is_malformed_ears:
            deductions += 40  # Severe penalty for structural corruption

        if is_malformed_ears:
            quality_score = min(max(0, 100 - deductions), 60)
            summary = "Needs improvement. Malformed EARS syntax detected: specification contains a doubled subject or stacked modal verbs ('shall the system should')."
        else:
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
        """Format requirement using EARS (Easy Approach to Requirements Syntax).

        A4/A8 FIX: Idempotent — if the description is already a well-formed EARS statement
        starting with 'The SRSense System shall', return it unchanged to prevent double-prefixing
        and malformed output like 'shall the system should be respond within 200ms'.
        """
        raw_desc = description.strip()

        # ── IDEMPOTENCY GUARD ─────────────────────────────────────────────────────────────
        # If already starts with canonical EARS prefix, return as-is without re-processing.
        ears_prefix = re.compile(
            r"^(?:WHEN\s+.+?,\s+)?[Tt]he\s+SRSense\s+System\s+shall\s+",
            re.IGNORECASE,
        )
        if ears_prefix.match(raw_desc):
            ears_tmpl = (
                "Event-Driven: WHEN <trigger>, the <system name> shall <system response>."
                if raw_desc.upper().startswith("WHEN")
                else "Ubiquitous: The <system name> shall <system response>."
            )
            notes = []
            if "interaction" in raw_desc.lower() and not any(w in raw_desc.lower() for w in ["checkout", "login", "auth", "search", "registration", "signup", "export", "payment", "task", "process", "workflow"]):
                notes.append("specific user workflow context for interaction limit")
            if "respond within" in raw_desc.lower() and not any(w in raw_desc.lower() for w in ["search", "login", "checkout", "auth", "payment", "export", "report", "query", "%"]):
                notes.append("operational trigger and load parameters for response time")

            if notes:
                explanation = (
                    f"Requirement is compliant with EARS syntax. However, semantic completeness requires {' and '.join(notes)}."
                )
            else:
                explanation = "Requirement is already in valid EARS syntax. No structural changes required."

            return ImprovementResult(
                improved_title=title,
                improved_description=raw_desc,
                ears_template_used=ears_tmpl,
                explanation=explanation,
            )
        # ─────────────────────────────────────────────────────────────────────────────────

        # 1. Detect Trigger / Precondition (e.g. "When ...,")
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

        # 2. Strip leading subject + modal constructs from main clause.
        # This regex is applied ONCE — it removes the system subject and modal verb.
        cleaned = re.sub(
            r"^(?:the\s+srsense\s+system|the\s+system|the\s+application|the\s+software|the\s+platform|system|application|software)"
            r"\s+(?:shall|should|must|will|can|is\s+required\s+to|needs\s+to)"
            r"\s+(?:be\s+able\s+to|be\s+allowed\s+to|be\s+capable\s+of)?\s*",
            "",
            main_clause,
            flags=re.IGNORECASE,
        )
        # Strip "user(s) shall/should/must..." patterns
        cleaned = re.sub(
            r"^(?:users?)\s+(?:shall|should|must|can|will|is\s+required\s+to|needs\s+to)\s+(?:be\s+able\s+to|be\s+allowed\s+to)?\s*",
            "allow users to ",
            cleaned,
            flags=re.IGNORECASE,
        )
        # Strip orphaned leading modal verbs left after subject removal
        cleaned = re.sub(
            r"^(?:shall|should|must|will)\s+(?:be\s+able\s+to|be)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        # Strip orphaned leading "be "
        cleaned = re.sub(r"^be\s+", "", cleaned, flags=re.IGNORECASE).strip()

        # 3. Phrase-level vague term substitutions
        # IMPORTANT: these substitutions replace the vague WORD only — never the whole sentence.
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

        # Clean double spaces / trailing punctuation
        cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".")

        # Ensure first character of action verb is lowercase
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
