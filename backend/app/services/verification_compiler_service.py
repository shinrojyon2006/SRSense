"""
Requirement-to-Verification Compiler Service — Sprint 1.8.
"""

import re
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement, RequirementPriority, RequirementType
from app.models.user import User
from app.models.verification import (
    TestCase,
    TestCaseType,
    TestExecutionStatus,
    VerificationReadiness,
    VerificationSpecification,
    VerificationStatus,
    VerificationType,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.verification_repository import VerificationRepository
from app.schemas.verification import (
    ProjectVerificationSummaryResponse,
    VerificationSpecificationResponse,
)
from app.services.intelligence_service import IntelligenceService
from app.utils.logger import get_logger

logger = get_logger("srsense.verification_compiler")


class VerificationCompilerService:
    """Service layer for Requirement-to-Verification Compilation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)
        self.verif_repo = VerificationRepository(db)
        self.intel_service = IntelligenceService(db)

    async def _verify_project_ownership(self, project_id: UUID, user: User):
        project = await self.project_repo.get_by_id_and_owner(project_id, user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )
        return project

    def _determine_verification_type(self, req: Requirement) -> VerificationType:
        text = f"{req.title} {req.description}".lower()
        if any(w in text for w in ["ms", "second", "throughput", "latency", "concurrent", "response time"]):
            return VerificationType.PERFORMANCE
        elif any(w in text for w in ["auth", "password", "encrypt", "token", "permission", "role", "jwt"]):
            return VerificationType.SECURITY
        elif any(w in text for w in ["format", "validate", "valid", "regex", "email", "number"]):
            return VerificationType.DATA_VALIDATION
        elif req.type == RequirementType.NON_FUNCTIONAL:
            return VerificationType.BOUNDARY_CONSTRAINT
        return VerificationType.FUNCTIONAL

    def _extract_parameters(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        # Metric, Operator, Threshold, Unit, Population
        metric, operator, threshold, unit, population = None, None, None, None, None

        # Regex for response time / latency
        m_time = re.search(r"(?:respond|response time|latency)\s+(?:within|in)?\s*([<=>]+)?\s*(\d+(?:\.\d+)?)\s*(ms|milliseconds|seconds|sec)", text, re.IGNORECASE)
        if m_time:
            metric = "Response Time"
            operator = m_time.group(1) or "<="
            threshold = m_time.group(2)
            unit = m_time.group(3)

        # Regex for password length
        m_len = re.search(r"password\s+(?:must be|is)?\s*(exactly|at least|minimum|maximum)?\s*(\d+)\s*(characters|chars)", text, re.IGNORECASE)
        if m_len and not metric:
            metric = "Password Length"
            qual = m_len.group(1) or ""
            operator = "==" if "exact" in qual.lower() else (">=" if "at least" in qual.lower() or "min" in qual.lower() else "<=")
            threshold = m_len.group(2)
            unit = m_len.group(3)

        # Regex for population / percentile
        m_pop = re.search(r"(\d+%\s+of\s+\w+)", text, re.IGNORECASE)
        if m_pop:
            population = m_pop.group(1)

        return metric, operator, threshold, unit, population

    async def compile_requirement(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> VerificationSpecificationResponse:
        """Compile a requirement into structured verification specification & test case suite."""
        await self._verify_project_ownership(project_id, user)
        req = await self.req_repo.get_by_id_and_project(requirement_id, project_id)
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")

        text = f"{req.title}. {req.description}"
        verif_type = self._determine_verification_type(req)
        metric, operator, threshold, unit, population = self._extract_parameters(text)

        # Evaluate Quality Readiness & Gaps
        missing_elements: List[str] = []
        is_vague = any(w in text.lower() for w in ["fast", "user friendly", "scalable", "secure enough", "should be quick"])

        if metric and threshold:
            readiness = VerificationReadiness.EXPLICIT_MEASURABLE
            confidence = 0.95
            pass_condition = f"Measured {metric} {operator or '<='} {threshold} {unit or ''}"
        elif is_vague or (req.type == RequirementType.NON_FUNCTIONAL and not threshold):
            readiness = VerificationReadiness.VERIFICATION_GAP
            confidence = 0.30
            missing_elements = ["quantitative threshold", "metric", "unit", "measurable condition"]
            pass_condition = "CANNOT_VERIFY: Requirement lacks quantitative measurable threshold limits."
        else:
            readiness = VerificationReadiness.CONFIDENTLY_INFERRED
            confidence = 0.75
            missing_elements = ["explicit numeric bound"]
            pass_condition = f"System satisfies functional contract for '{req.title}'"

        # Generate Acceptance Criteria (Given-When-Then or Measurable Criteria)
        acceptance_criteria: List[Dict[str, str]] = []
        if verif_type in (VerificationType.FUNCTIONAL, VerificationType.SECURITY, VerificationType.DATA_VALIDATION):
            acceptance_criteria.append({
                "given": f"the system is initialized and user has valid role/context for '{req.title}'",
                "when": f"the action triggering '{req.title}' is invoked",
                "then": f"the system shall execute successfully and return expected result",
            })
        else:
            acceptance_criteria.append({
                "criterion": f"System must satisfy {verif_type.value} threshold limit ({pass_condition})",
            })

        # Generate Test Cases
        spec_id = uuid4()
        test_cases: List[TestCase] = []

        # Positive Test Case
        test_cases.append(TestCase(
            id=uuid4(),
            project_id=project_id,
            requirement_id=requirement_id,
            verification_spec_id=spec_id,
            test_type=TestCaseType.POSITIVE,
            title=f"TC-POS-01: Verify successful execution of {req.title}",
            preconditions="System up and healthy.",
            steps_json=["Submit valid request payload.", "Observe server response status."],
            expected_result=f"HTTP 200 OK. {pass_condition}",
            execution_status=TestExecutionStatus.UNTESTED,
        ))

        # Negative / Boundary Test Case
        if threshold and metric:
            test_cases.append(TestCase(
                id=uuid4(),
                project_id=project_id,
                requirement_id=requirement_id,
                verification_spec_id=spec_id,
                test_type=TestCaseType.BOUNDARY if "Length" in metric else TestCaseType.NEGATIVE,
                title=f"TC-BND-01: Verify boundary condition for {metric}",
                preconditions="System under load/boundary condition.",
                steps_json=[f"Submit request violating limit ({metric} > {threshold}).", "Observe system response."],
                expected_result="System rejects invalid request or flags metric breach.",
                execution_status=TestExecutionStatus.UNTESTED,
            ))

        # Determine Verification Status based on User Refinement Rules
        if readiness == VerificationReadiness.EXPLICIT_MEASURABLE:
            verif_status = VerificationStatus.READY_FOR_VERIFICATION
        elif readiness == VerificationReadiness.CONFIDENTLY_INFERRED:
            verif_status = VerificationStatus.PARTIALLY_READY
        else:
            verif_status = VerificationStatus.UNVERIFIED

        spec = VerificationSpecification(
            id=spec_id,
            project_id=project_id,
            requirement_id=requirement_id,
            metric=metric,
            operator=operator,
            threshold=threshold,
            unit=unit,
            population_sample=population,
            condition="Under standard operational conditions.",
            expected_result=f"System satisfies {req.title}",
            verification_type=verif_type,
            readiness_status=readiness,
            verification_status=verif_status,
            confidence_score=confidence,
            pass_condition=pass_condition,
            missing_elements_json=missing_elements,
            acceptance_criteria_json=acceptance_criteria,
        )

        saved_spec = await self.verif_repo.upsert_spec(spec)
        await self.verif_repo.replace_test_cases_for_spec(saved_spec.id, test_cases)
        full_spec = await self.verif_repo.get_spec_by_requirement(requirement_id)
        return VerificationSpecificationResponse.model_validate(full_spec)

    async def get_verification_for_requirement(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> VerificationSpecificationResponse:
        await self._verify_project_ownership(project_id, user)
        spec = await self.verif_repo.get_spec_by_requirement(requirement_id)
        if not spec:
            # Auto-compile if not yet compiled
            return await self.compile_requirement(user, project_id, requirement_id)
        return VerificationSpecificationResponse.model_validate(spec)

    async def update_test_case_status(
        self, user: User, project_id: UUID, test_case_id: UUID, new_status: TestExecutionStatus
    ) -> TestCase:
        await self._verify_project_ownership(project_id, user)
        tc = await self.verif_repo.get_test_case_by_id(test_case_id)
        if not tc or tc.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
        return await self.verif_repo.update_test_case_status(tc, new_status)

    async def get_project_verification_summary(
        self, user: User, project_id: UUID
    ) -> ProjectVerificationSummaryResponse:
        """Calculate project-wide readiness %, test generation coverage %, and actual verified %."""
        await self._verify_project_ownership(project_id, user)
        reqs = await self.req_repo.get_all_by_project(project_id)
        specs = await self.verif_repo.get_all_specs_by_project(project_id)
        spec_map = {s.requirement_id: s for s in specs}

        total_reqs = len(reqs)
        if total_reqs == 0:
            return ProjectVerificationSummaryResponse(
                project_id=project_id,
                total_requirements_count=0,
                verification_readiness_percentage=0.0,
                test_generation_coverage_percentage=0.0,
                actual_verification_coverage_percentage=0.0,
                status_breakdown={"unverified": 0, "partially_ready": 0, "ready_for_verification": 0, "verified": 0},
                readiness_breakdown={"explicit_measurable": 0, "confidently_inferred": 0, "verification_gap": 0},
                unverified_requirements_gaps=[],
            )

        status_counts = {"unverified": 0, "partially_ready": 0, "ready_for_verification": 0, "verified": 0}
        readiness_counts = {"explicit_measurable": 0, "confidently_inferred": 0, "verification_gap": 0}

        reqs_with_tests = 0
        ready_or_verified = 0
        actually_verified = 0
        gaps_list = []

        for r in reqs:
            s = spec_map.get(r.id)
            if s:
                status_counts[s.verification_status.value] += 1
                readiness_counts[s.readiness_status.value] += 1

                if s.test_cases:
                    reqs_with_tests += 1

                if s.verification_status in (VerificationStatus.READY_FOR_VERIFICATION, VerificationStatus.VERIFIED, VerificationStatus.PARTIALLY_READY):
                    ready_or_verified += 1

                if s.verification_status == VerificationStatus.VERIFIED:
                    actually_verified += 1

                if s.readiness_status == VerificationReadiness.VERIFICATION_GAP:
                    gaps_list.append({
                        "requirement_id": str(r.id),
                        "title": r.title,
                        "missing_elements": s.missing_elements,
                    })
            else:
                status_counts["unverified"] += 1

        readiness_pct = round((ready_or_verified / total_reqs) * 100, 1)
        test_gen_pct = round((reqs_with_tests / total_reqs) * 100, 1)
        actual_verified_pct = round((actually_verified / total_reqs) * 100, 1)

        return ProjectVerificationSummaryResponse(
            project_id=project_id,
            total_requirements_count=total_reqs,
            verification_readiness_percentage=readiness_pct,
            test_generation_coverage_percentage=test_gen_pct,
            actual_verification_coverage_percentage=actual_verified_pct,
            status_breakdown=status_counts,
            readiness_breakdown=readiness_counts,
            unverified_requirements_gaps=gaps_list,
        )
