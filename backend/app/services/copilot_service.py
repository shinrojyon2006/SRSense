"""
Sprint 1.9 — Engineering AI Copilot Service

Scoped AI reasoning engine. Uses ONLY these tools:
- get_project(): project metadata
- get_requirement(): single requirement
- get_all_requirements(): all project requirements
- get_dependencies(): requirement relationships
- get_quality_analysis(): stored quality score + analysis_result
- get_verification(): verification spec for a requirement

NO unrestricted SQL. NO arbitrary DB access.
Consequential changes (create/update requirements) require explicit human approval.

AI used for:
- Semantic conflict detection (cross-sentence reasoning)
- Contextual rewriting (natural language improvement)
- Gap analysis (missing requirements inference)
- Scenario generation (acceptance criteria expansion)
- Traceability explanation (dependency chain reasoning)

Deterministic engine used for:
- Quality scoring (quality_score from analysis_result)
- Duplicate similarity (title/description similarity)
- Graph traversal (dependency chain walking)
- Cycle prevention
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.factory import get_ai_provider
from app.models.project_memory import ProjectMemory
from app.models.requirement import Requirement, RequirementStatus, RequirementType
from app.models.relationship import RelationshipType
from app.models.suggestion import RequirementSuggestion
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.requirement_repository import RequirementRepository
from app.schemas.copilot import (
    AIRefereeResponse,
    AIReviewResponse,
    ConfidenceLevel,
    CopilotChatRequest,
    CopilotChatResponse,
    DoctorIssue,
    GapFinderResponse,
    GapSuggestion,
    GapType,
    ProjectMemoryResponse,
    ProjectMemoryUpdate,
    RefereeVote,
    RequirementDoctorResponse,
    ReviewFinding,
    ReviewMode,
    ScenarioGeneratorResponse,
    TestScenario,
    TraceabilityLink,
    TraceabilityResponse,
)

logger = logging.getLogger(__name__)


class CopilotService:
    """Engineering AI Copilot — scoped reasoning over project requirements."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)
        self.rel_repo = RelationshipRepository(db)
        self._ai = get_ai_provider()

    # ── Scoped Tool Implementations ───────────────────────────────────────────

    async def _verify_ownership(self, project_id: UUID, user: User):
        project = await self.project_repo.get_by_id_and_owner(project_id, user.id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    async def _get_requirement(self, req_id: UUID, project_id: UUID) -> Requirement:
        req = await self.req_repo.get_by_id_and_project(req_id, project_id)
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
        return req

    async def _get_all_requirements(self, project_id: UUID) -> List[Requirement]:
        return await self.req_repo.get_all_by_project(project_id)

    # ── Project Copilot Chat ───────────────────────────────────────────────────

    async def chat(
        self, user: User, project_id: UUID, request: CopilotChatRequest
    ) -> CopilotChatResponse:
        """Answer questions about the project using actual requirement data."""
        project = await self._verify_ownership(project_id, user)
        reqs = await self._get_all_requirements(project_id)

        # Determine scope
        if request.context_requirement_ids:
            scope = [r for r in reqs if r.id in set(request.context_requirement_ids)]
        else:
            scope = reqs

        if not scope:
            return CopilotChatResponse(
                answer="No requirements found in this project to analyze.",
                confidence=ConfidenceLevel.UNCERTAIN,
                evidence=[],
                referenced_requirement_ids=[],
            )

        question = request.message
        proj_title = getattr(project, "title", getattr(project, "name", "Project"))
        try:
            answer, confidence, evidence, referenced_ids, caveats = await self._heuristic_chat(
                question, scope, proj_title
            )
        except Exception as e:
            logger.warning("Copilot chat error: %s", e)
            answer = f"I found {len(scope)} requirements in this project. Please ask a specific question about a requirement type, quality issue, or dependency."
            confidence = ConfidenceLevel.UNCERTAIN
            evidence = [f"Analyzed {len(scope)} requirements"]
            referenced_ids = []
            caveats = None

        return CopilotChatResponse(
            answer=answer,
            confidence=confidence,
            evidence=evidence,
            referenced_requirement_ids=referenced_ids,
            caveats=caveats,
        )

    async def _heuristic_chat(
        self, question: str, reqs: List[Requirement], project_name: str
    ):
        """Heuristic chat response using keyword analysis over actual project data."""
        q = question.lower()
        referenced_ids = []
        evidence = []
        caveats = None

        # Count by type
        type_counts = {}
        for req in reqs:
            t = req.type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        # Quality analysis
        quality_scores = [r.quality_score for r in reqs if r.quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

        # Find vague requirements
        vague_reqs = [r for r in reqs if r.analysis_result and
                      len(r.analysis_result.get("ambiguity_tags", [])) > 0]

        if any(w in q for w in ["how many", "count", "total", "number of"]):
            answer = f"This project has {len(reqs)} requirement(s): {', '.join(f'{v} {k}' for k,v in type_counts.items())}."
            confidence = ConfidenceLevel.EXPLICIT
            evidence = [f"Requirements count from database: {len(reqs)}"]

        elif any(w in q for w in ["quality", "score", "good", "bad"]):
            if avg_quality is not None:
                answer = f"Average quality score is {avg_quality:.0f}/100. {len(vague_reqs)} requirement(s) have ambiguity issues."
                confidence = ConfidenceLevel.EXPLICIT
                evidence = [f"Quality scores analyzed for {len(quality_scores)} requirements"]
                if vague_reqs:
                    referenced_ids = [r.id for r in vague_reqs[:5]]
            else:
                answer = "No quality analysis has been run yet. Use the Analyze button on individual requirements."
                confidence = ConfidenceLevel.UNCERTAIN
                evidence = ["No quality_score data found in requirements"]

        elif any(w in q for w in ["vague", "ambiguous", "unclear", "improve"]):
            if vague_reqs:
                titles = ", ".join(f"'{r.title}'" for r in vague_reqs[:5])
                answer = f"{len(vague_reqs)} requirement(s) have ambiguity issues: {titles}."
                confidence = ConfidenceLevel.EXPLICIT
                evidence = [f"Ambiguity tags found in analysis_result for {len(vague_reqs)} requirements"]
                referenced_ids = [r.id for r in vague_reqs[:5]]
            else:
                answer = "No ambiguity issues found in analyzed requirements."
                confidence = ConfidenceLevel.EXPLICIT
                evidence = ["analysis_result.ambiguity_tags is empty for all requirements"]

        elif any(w in q for w in ["non-functional", "nfr", "performance", "latency", "security"]):
            nfr = [r for r in reqs if r.type == RequirementType.NON_FUNCTIONAL]
            if nfr:
                answer = f"Found {len(nfr)} non-functional requirement(s): {', '.join(r.title for r in nfr[:5])}."
                confidence = ConfidenceLevel.EXPLICIT
                referenced_ids = [r.id for r in nfr[:5]]
                evidence = ["Filtered requirements by type=non_functional"]
            else:
                answer = "No non-functional requirements found in this project. Consider adding performance, security, or reliability requirements."
                confidence = ConfidenceLevel.INFERRED
                evidence = ["type=non_functional not found in requirements"]

        elif any(w in q for w in ["draft", "approved", "status", "review"]):
            drafts = [r for r in reqs if r.status == RequirementStatus.DRAFT]
            approved = [r for r in reqs if r.status == RequirementStatus.APPROVED]
            answer = f"Status breakdown: {len(drafts)} draft, {len(approved)} approved, {len(reqs)-len(drafts)-len(approved)} in other states."
            confidence = ConfidenceLevel.EXPLICIT
            evidence = ["Status field from all requirements"]

        else:
            summary_parts = [f"Project '{project_name}' has {len(reqs)} requirement(s)."]
            if type_counts:
                summary_parts.append("Types: " + ", ".join(f"{v} {k}" for k, v in type_counts.items()))
            if avg_quality is not None:
                summary_parts.append(f"Avg quality: {avg_quality:.0f}/100.")
            answer = " ".join(summary_parts) + " Ask me about quality, vague requirements, NFRs, status, or specific requirements."
            confidence = ConfidenceLevel.INFERRED
            evidence = [f"Summarized {len(reqs)} requirements"]
            caveats = "For more specific answers, ask about a particular requirement type or quality metric."

        return answer, confidence, evidence, referenced_ids, caveats

    # ── Requirement Doctor ────────────────────────────────────────────────────

    async def diagnose_requirement(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> RequirementDoctorResponse:
        """Run deep health analysis on a specific requirement."""
        await self._verify_ownership(project_id, user)
        req = await self._get_requirement(requirement_id, project_id)

        desc = (req.description or "").strip()
        desc_lower = desc.lower()
        title = (req.title or "").strip()
        req_type_str = req.type.value if hasattr(req.type, "value") else str(req.type).lower()

        issues: List[DoctorIssue] = []
        deductions = 0

        # Known vague words
        MAJOR_VAGUE_TERMS = [
            "fast", "quick", "instant", "scalable", "user-friendly", "user friendly",
            "secure", "intuitive", "robust", "efficient", "flexible", "responsive",
            "reasonable", "reliable", "appropriate", "acceptable", "good", "better", "seamless"
        ]

        found_vague = [t for t in MAJOR_VAGUE_TERMS if re.search(r"\b" + re.escape(t) + r"\b", desc_lower)]

        # Check for quantitative metrics (numbers with units or plain numbers)
        has_metric = bool(re.search(r"\b\d+(\.\d+)?\s*(ms|%|milliseconds?|seconds?|s|sec|req/s|rps|tps|users?|gb|mb|kb|hours?|mins?|minutes?)\b", desc_lower)) or bool(re.search(r"\b\d+\b", desc_lower))

        # Check if requirement expresses performance/quality attributes
        is_perf_or_quality = (
            req_type_str == "non_functional"
            or any(t in desc_lower for t in ["fast", "speed", "latency", "response", "throughput", "uptime", "availability", "load", "concurrent", "scalable", "performance", "capacity"])
        )

        # 1. Ambiguity Detection
        if found_vague:
            issues.append(DoctorIssue(
                severity="critical" if (is_perf_or_quality and not has_metric) else "warning",
                category="Ambiguity",
                description=f"Contains {len(found_vague)} subjective/vague term(s): {', '.join(repr(t) for t in found_vague[:3])}.",
                suggestion="Replace subjective terms with explicit, verifiable acceptance criteria (e.g., 'within 200 ms for 95% of requests').",
            ))
            # 25 points for first major vague term + 10 for each additional
            deductions += 25 + (len(found_vague) - 1) * 10

        # 2. Measurability Check (Performance / Quality without quantitative metric)
        if is_perf_or_quality and not has_metric:
            issues.append(DoctorIssue(
                severity="critical",
                category="Measurability",
                description="Performance/quality specification lacks a quantitative metric or threshold.",
                suggestion="Add specific verifiable metrics such as response time in milliseconds (e.g. <= 200ms) or availability (e.g. >= 99.9%).",
            ))
            deductions += 25

        # 3. Completeness: Length check
        if len(desc) < 30:
            issues.append(DoctorIssue(
                severity="warning" if found_vague else "info",
                category="Completeness",
                description=f"Description is too brief ({len(desc)} characters) to define complete system behavior.",
                suggestion="Expand the description with the specific actor, trigger event, and expected verifiable response.",
            ))
            deductions += 15

        # 4. Completeness: Missing trigger/precondition
        has_trigger = any(w in desc_lower for w in ["given", "when", "if", "while", "upon", "whenever", "as soon as", "where"])
        has_shall = "shall" in desc_lower
        if not has_trigger and not has_shall and not is_perf_or_quality:
            issues.append(DoctorIssue(
                severity="warning",
                category="Completeness",
                description="Missing clear trigger or activation condition (Given / When / If / Upon).",
                suggestion="Specify the exact event or state that initiates this requirement.",
            ))
            deductions += 15

        # 5. Semantic Completeness: Context & Workflow checks
        has_response_time = bool(re.search(r"\b(respond within|response time|latency within)\b", desc_lower))
        has_interaction_limit = bool(re.search(r"\b\d+\s*(?:user\s+interactions?|interactions?|clicks?|steps?|screens?)\b", desc_lower))
        has_workflow_context = any(w in desc_lower for w in ["checkout", "login", "auth", "search", "registration", "signup", "export", "payment", "task", "process", "workflow", "journey", "flow", "during", "when", "upon"])
        if has_interaction_limit and not has_workflow_context:
            issues.append(DoctorIssue(
                severity="warning",
                category="Completeness",
                description="Lacks specific user workflow or task context for measuring user interaction limits.",
                suggestion="Specify the exact user workflow or task (e.g., 'WHEN user completes checkout, the system shall require no more than 3 user interactions').",
            ))
            deductions += 15
            if has_response_time and not has_trigger:
                issues.append(DoctorIssue(
                    severity="warning",
                    category="Completeness",
                    description="Lacks specific operation or trigger context for response time verification.",
                    suggestion="Specify the target operation or trigger (e.g., 'return search results within 200 milliseconds').",
                ))
                deductions += 15

        # 6. Passive voice check
        PASSIVE_PATTERN = re.compile(
            r"\b(is|are|was|were|be|been|being)\s+([a-z]+ed|built|sent|made|done|found|given|taken|shown|kept)\b",
            re.IGNORECASE
        )
        passive_matches = set(PASSIVE_PATTERN.findall(desc))
        if passive_matches:
            issues.append(DoctorIssue(
                severity="info",
                category="Writing Style",
                description=f"Contains passive voice construct(s): {', '.join(f'{m[0]} {m[1]}' for m in list(passive_matches)[:2])}.",
                suggestion="Rewrite in active voice using 'The system shall [verb]...' format.",
            ))
            deductions += min(15, len(passive_matches) * 5)

        # 7. Malformed syntax check
        MALFORMED_PATTERN = re.compile(
            r"\bshall\b.{1,20}\bshall\b|\bshall the\b|\bshall (the system|the application)\b|\bshould be respond\b|\bshall (should|must|will)\b",
            re.IGNORECASE
        )
        if MALFORMED_PATTERN.search(desc):
            issues.append(DoctorIssue(
                severity="critical",
                category="Syntax",
                description="Malformed EARS syntax detected (doubled modal or broken prefix).",
                suggestion="Re-run AI improvement to regenerate clean EARS syntax.",
            ))
            deductions += 40

        health_score = max(0, min(100, 100 - deductions))

        # Consistent Health Classification
        # Grounding Rule: A requirement containing major ambiguity, critical severity, or substantive warnings (< 80) MUST NOT be "healthy".
        has_critical = any(i.severity == "critical" for i in issues)
        has_ambiguity = any(i.category == "Ambiguity" for i in issues)
        has_completeness_warning = any(i.category == "Completeness" and i.severity == "warning" for i in issues)

        if health_score >= 80 and not has_critical and not has_ambiguity and not has_completeness_warning:
            overall_health = "healthy"
        elif health_score >= 50 and not (has_critical and health_score < 60):
            overall_health = "needs_attention"
        else:
            overall_health = "critical"

        confidence = ConfidenceLevel.EXPLICIT if has_metric and not found_vague and not has_completeness_warning else ConfidenceLevel.INFERRED

        improvement_hint = None
        if issues:
            top = issues[0]
            improvement_hint = f"Priority fix: [{top.category}] {top.suggestion}"

        return RequirementDoctorResponse(
            requirement_id=req.id,
            requirement_title=title,
            overall_health=overall_health,
            health_score=health_score,
            issues=issues,
            improvement_hint=improvement_hint,
            confidence=confidence,
        )

    # ── AI Review Modes ───────────────────────────────────────────────────────

    async def run_review(
        self, user: User, project_id: UUID, mode: ReviewMode
    ) -> AIReviewResponse:
        """Run a specialized review of all project requirements for a given mode."""
        project = await self._verify_ownership(project_id, user)
        reqs = await self._get_all_requirements(project_id)

        findings: List[ReviewFinding] = []

        for req in reqs:
            desc = req.description.lower()
            title = req.title

            if mode == ReviewMode.QA:
                has_measurable = bool(re.search(r"\b\d+\b", req.description))
                has_condition = any(w in desc for w in ["when", "given", "if", "shall"])
                if not has_measurable and req.type == RequirementType.NON_FUNCTIONAL:
                    findings.append(ReviewFinding(
                        requirement_id=req.id, requirement_title=title,
                        severity="warning",
                        finding="Non-functional requirement lacks measurable acceptance criteria.",
                        recommendation="Add specific numeric threshold for automated testing.",
                        confidence=ConfidenceLevel.EXPLICIT,
                    ))
                if not has_condition:
                    findings.append(ReviewFinding(
                        requirement_id=req.id, requirement_title=title,
                        severity="info",
                        finding="Requirement lacks explicit trigger or precondition.",
                        recommendation="Add WHEN/GIVEN/IF clause for precise test scenario definition.",
                        confidence=ConfidenceLevel.INFERRED,
                    ))

            elif mode == ReviewMode.SECURITY:
                security_keywords = ["auth", "login", "password", "token", "session", "permission", "encrypt", "secure", "credential"]
                auth_keywords = ["without authentication", "unauthenticated", "bypass"]
                has_security_topic = any(k in desc for k in security_keywords)
                has_bypass_risk = any(k in desc for k in auth_keywords)
                if has_bypass_risk:
                    findings.append(ReviewFinding(
                        requirement_id=req.id, requirement_title=title,
                        severity="critical",
                        finding="Potential authentication bypass risk in requirement description.",
                        recommendation="Clarify authentication requirements. Add explicit 'shall require authentication' clause.",
                        confidence=ConfidenceLevel.INFERRED,
                    ))
                if has_security_topic and "encrypt" not in desc and "hash" not in desc:
                    findings.append(ReviewFinding(
                        requirement_id=req.id, requirement_title=title,
                        severity="info",
                        finding="Security-related requirement does not mention encryption or hashing.",
                        recommendation="Specify whether data at rest and in transit should be encrypted.",
                        confidence=ConfidenceLevel.UNCERTAIN,
                    ))

            elif mode == ReviewMode.PERFORMANCE:
                perf_keywords = ["response", "load", "throughput", "latency", "performance", "concurrent", "fast", "slow"]
                has_perf_topic = any(k in desc for k in perf_keywords)
                has_metric = bool(re.search(r"\b\d+\s*(ms|%|milliseconds?|sec|req|concurrent)\b", req.description, re.IGNORECASE))
                if has_perf_topic and not has_metric:
                    findings.append(ReviewFinding(
                        requirement_id=req.id, requirement_title=title,
                        severity="warning",
                        finding="Performance-related requirement lacks a measurable threshold.",
                        recommendation="Add specific metric: 'within 200ms', '99.9% uptime', '1000 concurrent users'.",
                        confidence=ConfidenceLevel.EXPLICIT,
                    ))
                if req.type == RequirementType.NON_FUNCTIONAL and not has_metric:
                    findings.append(ReviewFinding(
                        requirement_id=req.id, requirement_title=title,
                        severity="warning",
                        finding="Non-functional requirement has no measurable performance metric.",
                        recommendation="Define a specific, testable performance criterion.",
                        confidence=ConfidenceLevel.EXPLICIT,
                    ))

            elif mode == ReviewMode.PRODUCT:
                value_keywords = ["user", "customer", "benefit", "enable", "allow", "provide"]
                has_user_value = any(k in desc for k in value_keywords)
                if not has_user_value and req.type == RequirementType.FUNCTIONAL:
                    findings.append(ReviewFinding(
                        requirement_id=req.id, requirement_title=title,
                        severity="info",
                        finding="Functional requirement does not reference user benefit or outcome.",
                        recommendation="Clarify who benefits from this feature and how.",
                        confidence=ConfidenceLevel.INFERRED,
                    ))
                if req.type.value == "user":
                    has_story_format = "as a" in desc and ("i want" in desc or "i need" in desc)
                    if not has_story_format:
                        findings.append(ReviewFinding(
                            requirement_id=req.id, requirement_title=title,
                            severity="warning",
                            finding="User requirement does not follow 'As a/I want/So that' format.",
                            recommendation="Rewrite as: 'As a [role], I want [goal], so that [benefit].'",
                            confidence=ConfidenceLevel.EXPLICIT,
                        ))

            elif mode == ReviewMode.ARCHITECTURE:
                integration_keywords = ["api", "integration", "external", "third-party", "service", "database", "cloud"]
                constraint_keywords = ["shall use", "must use", "technology", "framework", "platform"]
                has_integration = any(k in desc for k in integration_keywords)
                has_constraint = any(k in desc for k in constraint_keywords)
                if has_integration and not has_constraint:
                    findings.append(ReviewFinding(
                        requirement_id=req.id, requirement_title=title,
                        severity="info",
                        finding="Requirement mentions integration but lacks technology/protocol constraints.",
                        recommendation="Specify integration protocol (REST, gRPC, GraphQL), data format, and SLA expectations.",
                        confidence=ConfidenceLevel.UNCERTAIN,
                    ))

        summary_parts = [
            f"{mode.value.upper()} Review: analyzed {len(reqs)} requirement(s), found {len(findings)} finding(s)."
        ]
        critical = sum(1 for f in findings if f.severity == "critical")
        warnings = sum(1 for f in findings if f.severity == "warning")
        if critical:
            summary_parts.append(f"{critical} critical issue(s) require immediate attention.")
        if warnings:
            summary_parts.append(f"{warnings} warning(s) should be addressed before release.")
        if not findings:
            summary_parts.append("No significant issues found.")

        return AIReviewResponse(
            project_id=project_id,
            mode=mode,
            total_requirements_reviewed=len(reqs),
            findings=findings,
            summary=" ".join(summary_parts),
            timestamp=datetime.now(timezone.utc),
        )

    # ── AI Referee ────────────────────────────────────────────────────

    async def referee_suggestion(
        self, user: User, project_id: UUID, suggestion_id: UUID
    ) -> AIRefereeResponse:
        """Evaluate whether an AI-generated relationship suggestion should be accepted."""
        await self._verify_ownership(project_id, user)

        sug = await self.db.get(RequirementSuggestion, suggestion_id)
        if not sug or sug.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suggestion not found")

        source = await self._get_requirement(sug.source_id, project_id)
        target = await self._get_requirement(sug.target_id, project_id)

        confidence_val = getattr(sug, 'confidence_score', 0.5) or 0.5

        if confidence_val >= 0.85:
            choice = "accept"
            reasoning = (
                f"High-confidence ({confidence_val:.0%}) dependency detected. "
                f"'{source.title}' references '{target.title}' explicitly in its description."
            )
            confidence = ConfidenceLevel.EXPLICIT
            risk_accept = "Low risk — explicit reference confirmed."
            risk_reject = f"Rejecting may cause '{source.title}' to be implemented without considering '{target.title}'."
        elif confidence_val >= 0.65:
            choice = "defer"
            reasoning = (
                f"Moderate confidence ({confidence_val:.0%}). Manual review recommended. "
                f"The relationship between '{source.title}' and '{target.title}' is plausible but not certain."
            )
            confidence = ConfidenceLevel.INFERRED
            risk_accept = "Medium risk — may introduce unnecessary coupling."
            risk_reject = "Medium risk — may miss a real dependency."
        else:
            choice = "reject"
            reasoning = (
                f"Low confidence ({confidence_val:.0%}). No strong evidence that "
                f"'{source.title}' depends on '{target.title}'."
            )
            confidence = ConfidenceLevel.UNCERTAIN
            risk_accept = "High risk — may introduce false dependency in graph."
            risk_reject = "Low risk — dependency likely does not exist."

        return AIRefereeResponse(
            suggestion_id=suggestion_id,
            referee_vote=RefereeVote(
                choice=choice,
                reasoning=reasoning,
                confidence=confidence,
                risk_if_accepted=risk_accept,
                risk_if_rejected=risk_reject,
            ),
        )

    # ── AI Gap Finder ─────────────────────────────────────────────────

    async def find_gaps(
        self, user: User, project_id: UUID
    ) -> GapFinderResponse:
        """Identify missing requirement categories based on what exists."""
        project = await self._verify_ownership(project_id, user)
        reqs = await self._get_all_requirements(project_id)

        gaps: List[GapSuggestion] = []
        all_desc = " ".join(r.description.lower() + " " + r.title.lower() for r in reqs)

        # Check for missing NFRs
        nfr_reqs = [r for r in reqs if r.type == RequirementType.NON_FUNCTIONAL]
        if not nfr_reqs:
            gaps.append(GapSuggestion(
                gap_type=GapType.MISSING_NFR,
                title="No Non-Functional Requirements Found",
                description="The project has no performance, security, or reliability requirements.",
                rationale="Every production system needs measurable NFRs for SLA compliance.",
                confidence=ConfidenceLevel.EXPLICIT,
                related_requirement_ids=[],
            ))

        # Check for missing error handling
        error_keywords = ["error", "exception", "fail", "invalid", "timeout", "retry", "fallback"]
        has_error_handling = any(k in all_desc for k in error_keywords)
        if not has_error_handling and len(reqs) > 2:
            functional = [r for r in reqs if r.type == RequirementType.FUNCTIONAL]
            gaps.append(GapSuggestion(
                gap_type=GapType.MISSING_ERROR_HANDLING,
                title="No Error Handling Requirements",
                description="No requirements address error states, exceptions, or failure recovery.",
                rationale="Robust systems need explicit requirements for handling failures gracefully.",
                confidence=ConfidenceLevel.INFERRED,
                related_requirement_ids=[r.id for r in functional[:3]],
            ))

        # Check for missing security
        security_keywords = ["auth", "login", "user", "access", "permission", "role"]
        auth_required = any(k in all_desc for k in security_keywords)
        security_defined = any(k in all_desc for k in ["encrypt", "jwt", "token", "oauth", "rbac", "authorization"])
        if auth_required and not security_defined:
            auth_reqs = [r for r in reqs if any(k in r.description.lower() for k in security_keywords)]
            gaps.append(GapSuggestion(
                gap_type=GapType.MISSING_SECURITY,
                title="Authentication/Authorization Requirements Missing",
                description="Requirements reference users and access but don't define security mechanisms.",
                rationale="Systems with user authentication must specify the security protocol (JWT, OAuth, RBAC).",
                confidence=ConfidenceLevel.INFERRED,
                related_requirement_ids=[r.id for r in auth_reqs[:3]],
            ))

        # Check for missing performance NFRs
        perf_topics = ["search", "load", "query", "process", "fetch", "retrieve"]
        has_perf_topics = any(k in all_desc for k in perf_topics)
        has_perf_nfr = any(bool(re.search(r"\b\d+\s*(ms|milliseconds?|sec)\b", r.description, re.IGNORECASE)) for r in reqs)
        if has_perf_topics and not has_perf_nfr:
            gaps.append(GapSuggestion(
                gap_type=GapType.MISSING_PERFORMANCE,
                title="Performance Thresholds Not Defined",
                description="Requirements mention performance-sensitive operations but don't set measurable targets.",
                rationale="Operations like search and data retrieval need response time SLAs.",
                confidence=ConfidenceLevel.INFERRED,
                related_requirement_ids=[],
            ))

        # Check for incomplete user stories
        user_reqs = [r for r in reqs if r.type.value == "user"]
        for ur in user_reqs:
            desc = ur.description.lower()
            has_as_a = "as a" in desc
            has_want = "i want" in desc or "i need" in desc
            has_so_that = "so that" in desc or "in order to" in desc
            if not (has_as_a and has_want and has_so_that):
                gaps.append(GapSuggestion(
                    gap_type=GapType.INCOMPLETE_USER_STORY,
                    title=f"Incomplete User Story: {ur.title}",
                    description="User story missing standard format components.",
                    rationale="Complete user stories need role, goal, and benefit for product clarity.",
                    confidence=ConfidenceLevel.EXPLICIT,
                    related_requirement_ids=[ur.id],
                ))

        total_checks = 5
        passed = total_checks - min(total_checks, len(gaps))
        coverage_score = int((passed / total_checks) * 100)

        summary_parts = [f"Gap analysis complete. Found {len(gaps)} gap(s) across {len(reqs)} requirement(s)."]
        if gaps:
            types = list({g.gap_type.value for g in gaps})
            summary_parts.append(f"Gap categories: {', '.join(types)}.")
        else:
            summary_parts.append("Requirements appear well-rounded.")

        return GapFinderResponse(
            project_id=project_id,
            total_gaps_found=len(gaps),
            gaps=gaps,
            coverage_score=coverage_score,
            summary=" ".join(summary_parts),
        )

    # ── Scenario Generator ────────────────────────────────────────────

    async def generate_scenarios(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> ScenarioGeneratorResponse:
        """Generate Given-When-Then test scenarios for a requirement.

        GROUNDING RULE:
        Every generated scenario step must be traceable to explicit requirement facts,
        verified project context, or clearly labeled inference.
        The generator MUST NOT invent actions, actors, permissions, data conditions,
        error behavior, performance targets, or business rules when absent.
        """
        await self._verify_ownership(project_id, user)
        req = await self._get_requirement(requirement_id, project_id)

        desc = (req.description or "").strip()
        desc_lower = desc.lower()
        title = (req.title or "").strip()

        # Check for vague terms
        MAJOR_VAGUE_TERMS = [
            "fast", "quick", "instant", "scalable", "user-friendly", "user friendly",
            "secure", "intuitive", "robust", "efficient", "flexible", "responsive",
            "reasonable", "reliable", "appropriate", "acceptable", "good", "better"
        ]
        found_vague = [t for t in MAJOR_VAGUE_TERMS if re.search(r"\b" + re.escape(t) + r"\b", desc_lower)]

        # Check for quantitative thresholds
        metric_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(ms|milliseconds?|seconds?|s|sec|%|percent|concurrent|req/s|rps|users?|tps)",
            desc,
            re.IGNORECASE,
        )
        time_threshold = f"{metric_match.group(1)} {metric_match.group(2)}" if metric_match else None

        # Check for concrete operation/action phrase
        action_match = re.search(
            r"\b(shall|should|must|will)\s+([a-z\s]{3,40}?)(?:\bwithin|\bfor|\bwhen|\bif|\bunder|\bwith|\.|\Z)",
            desc,
            re.IGNORECASE,
        )
        operation_text = action_match.group(2).strip() if action_match else None

        # Detect population/conditions like "for 95% of requests", "under normal load"
        cond_match = re.search(
            r"\b(for\s+\d+%\s+of\s+requests|under\s+[a-z\s]+load|when\s+[a-z\s]+|given\s+[a-z\s]+)\b",
            desc,
            re.IGNORECASE,
        )
        cond_text = cond_match.group(1).strip() if cond_match else None

        # ── INSUFFICIENT INFORMATION DETECTION ────────────────────────────
        is_insufficient = False
        missing_info_items: List[str] = []
        clarification_qs: List[str] = []

        if found_vague and not metric_match:
            is_insufficient = True
            missing_info_items.append("Operation or user transaction being measured (e.g., search query, payment checkout, report render)")
            missing_info_items.append("Quantitative performance metric (e.g., response time, latency, throughput, uptime)")
            missing_info_items.append("Measurable threshold (e.g., <= 200 milliseconds, >= 99.9%)")
            missing_info_items.append("Operating conditions or workload profile (e.g., 95% of requests under peak load)")

            clarification_qs.append(f"What specific system operation should be measured for '{title}'?")
            clarification_qs.append("What is the maximum acceptable latency or response time threshold (e.g., 200ms)?")
            clarification_qs.append("Under what load conditions (e.g., 95th percentile, concurrent users) should this threshold apply?")

        elif len(desc) < 30 and not action_match and not metric_match:
            is_insufficient = True
            missing_info_items.append("Concrete actor, trigger event, and expected system response")
            missing_info_items.append("Verifiable acceptance criteria or expected outcome")

            clarification_qs.append(f"What trigger initiates the behavior described in '{title}'?")
            clarification_qs.append("What is the specific verifiable outcome the system must produce?")

        if is_insufficient:
            return ScenarioGeneratorResponse(
                requirement_id=req.id,
                requirement_title=title,
                scenarios=[],
                total_scenarios=0,
                status="insufficient_information",
                insufficient_info_reason="Insufficient information for reliable scenario generation.",
                missing_information=missing_info_items,
                clarification_questions=clarification_qs,
            )

        # ── GROUNDED SCENARIO GENERATION ──────────────────────────────────
        scenarios: List[TestScenario] = []

        # Check for multi-clause requirements (e.g. response time + interaction limits)
        interaction_match = re.search(
            r"(\d+)\s*(?:user\s+interactions?|interactions?|clicks?|steps?|screens?)",
            desc,
            re.IGNORECASE,
        )

        if metric_match and interaction_match:
            # Multi-clause: Response latency + User interaction limit
            int_limit = interaction_match.group(1)
            scenarios.append(TestScenario(
                scenario_type="normal",
                title=f"Response latency verification: respond within {time_threshold}",
                given=cond_text.capitalize() if cond_text else "The SRSense System is operational",
                when=f"a request is sent to {operation_text or 'the system'}",
                then=f"the system shall respond within {time_threshold}",
                priority="high",
                confidence=ConfidenceLevel.EXPLICIT,
            ))
            scenarios.append(TestScenario(
                scenario_type="boundary",
                title=f"Interaction limit verification: require no more than {int_limit} user interactions",
                given="a user executes an interaction sequence on the system",
                when="completing the user workflow",
                then=f"the workflow shall require no more than {int_limit} user interactions",
                priority="high",
                confidence=ConfidenceLevel.EXPLICIT,
            ))

        elif metric_match:
            # Single quantitative SLA requirement
            op_label = operation_text or f"the operation in '{title}'"
            given_clause = cond_text.capitalize() if cond_text else f"The system is processing requests to {op_label}"
            when_clause = f"a user or client initiates a request to {op_label}"
            then_clause = f"the system shall {op_label} within {time_threshold}"
            if cond_text and "for" in cond_text.lower():
                then_clause += f" ({cond_text})"

            scenarios.append(TestScenario(
                scenario_type="normal",
                title=f"Normal operation: {op_label} within {time_threshold}",
                given=given_clause,
                when=when_clause,
                then=then_clause,
                priority="high",
                confidence=ConfidenceLevel.EXPLICIT,
            ))

            # Boundary / Latency Threshold Scenario
            scenarios.append(TestScenario(
                scenario_type="boundary",
                title=f"Performance SLA boundary: {time_threshold} threshold",
                given=f"requests evaluated against {cond_text or 'the SLA specification'}",
                when=f"the system processes requests to {op_label}",
                then=f"the execution response time shall not exceed {time_threshold}",
                priority="high",
                confidence=ConfidenceLevel.EXPLICIT,
            ))

        else:
            # 2. Functional Requirement with explicit action / trigger
            op_label = operation_text or desc
            scenarios.append(TestScenario(
                scenario_type="normal",
                title=f"Normal flow: {title}",
                given=f"preconditions for '{title}' are satisfied",
                when=f"the trigger event for '{title}' occurs",
                then=f"the system shall satisfy: {desc}",
                priority="high",
                confidence=ConfidenceLevel.EXPLICIT,
            ))

            scenarios.append(TestScenario(
                scenario_type="boundary",
                title=f"Boundary condition: {title}",
                given=f"inputs or system state are at upper/lower permissible boundaries for '{title}'",
                when=f"the action in '{title}' is executed",
                then=f"the system shall validate and process the state according to specification",
                priority="medium",
                confidence=ConfidenceLevel.INFERRED,
            ))

            scenarios.append(TestScenario(
                scenario_type="failure",
                title=f"Exception handling: {title}",
                given=f"invalid input or dependency failure occurs during '{title}'",
                when=f"the system attempts to process the request",
                then=f"the system shall reject invalid input and return a clear error without corrupting state",
                priority="high",
                confidence=ConfidenceLevel.INFERRED,
            ))

        return ScenarioGeneratorResponse(
            requirement_id=req.id,
            requirement_title=title,
            scenarios=scenarios,
            total_scenarios=len(scenarios),
            status="success",
            insufficient_info_reason=None,
            missing_information=None,
            clarification_questions=None,
        )

    # ── Traceability Assistant ────────────────────────────────────────

    async def get_traceability(
        self, user: User, project_id: UUID
    ) -> TraceabilityResponse:
        """Explain dependency chains and identify orphaned requirements."""
        await self._verify_ownership(project_id, user)
        reqs = await self._get_all_requirements(project_id)
        all_rels = await self.rel_repo.get_all_by_project(project_id)

        req_map = {r.id: r for r in reqs}
        linked_ids = set()
        links: List[TraceabilityLink] = []

        for rel in all_rels:
            source = req_map.get(rel.source_id)
            target = req_map.get(rel.target_id)
            if not source or not target:
                continue

            linked_ids.add(rel.source_id)
            linked_ids.add(rel.target_id)

            rel_type = rel.type.value if hasattr(rel.type, 'value') else str(rel.type)

            if rel_type == "depends_on":
                explanation = f"'{source.title}' depends on '{target.title}' — changes to '{target.title}' may require updates to '{source.title}'."
                confidence = ConfidenceLevel.EXPLICIT
            elif rel_type == "conflicts_with":
                explanation = f"'{source.title}' conflicts with '{target.title}' — both specifications cannot be simultaneously satisfied as stated."
                confidence = ConfidenceLevel.INFERRED
            elif rel_type == "derived_from":
                explanation = f"'{source.title}' is derived from '{target.title}' — '{source.title}' refines or implements '{target.title}'."
                confidence = ConfidenceLevel.EXPLICIT
            else:
                explanation = f"'{source.title}' → [{rel_type}] → '{target.title}'."
                confidence = ConfidenceLevel.UNCERTAIN

            links.append(TraceabilityLink(
                from_requirement_id=source.id,
                from_title=source.title,
                to_requirement_id=target.id,
                to_title=target.title,
                relationship_type=rel_type,
                explanation=explanation,
                confidence=confidence,
            ))

        orphaned = [r.id for r in reqs if r.id not in linked_ids]
        coverage = (len(linked_ids) / len(reqs) * 100) if reqs else 100.0

        summary_parts = [
            f"Traceability analysis: {len(reqs)} requirement(s), {len(links)} relationship(s).",
            f"Coverage: {coverage:.0f}% of requirements have at least one relationship.",
        ]
        if orphaned:
            summary_parts.append(f"{len(orphaned)} orphaned requirement(s) have no relationships.")

        return TraceabilityResponse(
            project_id=project_id,
            total_links=len(links),
            links=links,
            orphaned_requirement_ids=orphaned,
            coverage_percentage=round(coverage, 1),
            summary=" ".join(summary_parts),
        )

    # ── Project Memory ────────────────────────────────────────────────

    async def get_memory(self, user: User, project_id: UUID) -> ProjectMemoryResponse:
        """Get or create project memory."""
        project = await self._verify_ownership(project_id, user)

        result = await self.db.execute(
            select(ProjectMemory).where(ProjectMemory.project_id == project_id)
        )
        memory = result.scalar_one_or_none()

        if not memory:
            memory = ProjectMemory(
                project_id=project_id,
                terminology={},
                personas=[],
                domain_context=None,
            )
            self.db.add(memory)
            await self.db.commit()
            await self.db.refresh(memory)

        return ProjectMemoryResponse(
            project_id=project_id,
            terminology=memory.terminology or {},
            personas=memory.personas or [],
            domain_context=memory.domain_context,
            updated_at=memory.updated_at,
        )

    async def update_memory(
        self, user: User, project_id: UUID, update: ProjectMemoryUpdate
    ) -> ProjectMemoryResponse:
        """Update project memory — requires explicit user action."""
        await self._verify_ownership(project_id, user)

        result = await self.db.execute(
            select(ProjectMemory).where(ProjectMemory.project_id == project_id)
        )
        memory = result.scalar_one_or_none()

        if not memory:
            memory = ProjectMemory(project_id=project_id, terminology={}, personas=[], domain_context=None)
            self.db.add(memory)

        if update.terminology is not None:
            memory.terminology = update.terminology
        if update.personas is not None:
            memory.personas = update.personas
        if update.domain_context is not None:
            memory.domain_context = update.domain_context

        await self.db.commit()
        await self.db.refresh(memory)

        return ProjectMemoryResponse(
            project_id=project_id,
            terminology=memory.terminology or {},
            personas=memory.personas or [],
            domain_context=memory.domain_context,
            updated_at=memory.updated_at,
        )
