"""
Verification repository — async PostgreSQL CRUD for verification specifications and test cases.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.verification import (
    VerificationSpecification,
    TestCase,
    TestExecutionStatus,
    VerificationReadiness,
    VerificationStatus,
)


class VerificationRepository:
    """Data access repository for VerificationSpecification and TestCase entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_spec_by_requirement(
        self, requirement_id: UUID
    ) -> Optional[VerificationSpecification]:
        result = await self.session.execute(
            select(VerificationSpecification)
            .options(selectinload(VerificationSpecification.test_cases))
            .where(VerificationSpecification.requirement_id == requirement_id)
        )
        return result.scalar_one_or_none()

    async def get_all_specs_by_project(
        self, project_id: UUID
    ) -> List[VerificationSpecification]:
        result = await self.session.execute(
            select(VerificationSpecification)
            .options(selectinload(VerificationSpecification.test_cases))
            .where(VerificationSpecification.project_id == project_id)
        )
        return list(result.scalars().all())

    async def upsert_spec(
        self, spec: VerificationSpecification
    ) -> VerificationSpecification:
        existing = await self.get_spec_by_requirement(spec.requirement_id)
        if existing:
            existing.metric = spec.metric
            existing.operator = spec.operator
            existing.threshold = spec.threshold
            existing.unit = spec.unit
            existing.population_sample = spec.population_sample
            existing.condition = spec.condition
            existing.expected_result = spec.expected_result
            existing.verification_type = spec.verification_type
            existing.readiness_status = spec.readiness_status
            existing.verification_status = spec.verification_status
            existing.confidence_score = spec.confidence_score
            existing.pass_condition = spec.pass_condition
            existing.missing_elements_json = spec.missing_elements_json
            existing.acceptance_criteria_json = spec.acceptance_criteria_json
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            self.session.add(spec)
            await self.session.commit()
            await self.session.refresh(spec)
            return spec

    async def replace_test_cases_for_spec(
        self, spec_id: UUID, test_cases: List[TestCase]
    ) -> List[TestCase]:
        await self.session.execute(
            delete(TestCase).where(TestCase.verification_spec_id == spec_id)
        )
        for tc in test_cases:
            tc.verification_spec_id = spec_id
            self.session.add(tc)
        await self.session.commit()
        return test_cases

    async def get_test_case_by_id(self, test_case_id: UUID) -> Optional[TestCase]:
        result = await self.session.execute(
            select(TestCase).where(TestCase.id == test_case_id)
        )
        return result.scalar_one_or_none()

    async def update_test_case_status(
        self, test_case: TestCase, new_status: TestExecutionStatus
    ) -> TestCase:
        test_case.execution_status = new_status
        await self.session.commit()
        await self.session.refresh(test_case)

        # Recalculate VerificationStatus for the parent spec!
        if test_case.verification_spec_id:
            spec = await self.session.get(VerificationSpecification, test_case.verification_spec_id)
            if spec:
                all_tcs_res = await self.session.execute(
                    select(TestCase).where(TestCase.verification_spec_id == spec.id)
                )
                all_tcs = list(all_tcs_res.scalars().all())

                if all_tcs and all(tc.execution_status == TestExecutionStatus.PASSED for tc in all_tcs):
                    spec.verification_status = VerificationStatus.VERIFIED
                elif any(tc.execution_status == TestExecutionStatus.PASSED for tc in all_tcs):
                    spec.verification_status = VerificationStatus.PARTIALLY_READY
                elif spec.readiness_status == VerificationReadiness.EXPLICIT_MEASURABLE and all_tcs:
                    spec.verification_status = VerificationStatus.READY_FOR_VERIFICATION
                else:
                    spec.verification_status = VerificationStatus.UNVERIFIED

                await self.session.commit()

        return test_case
