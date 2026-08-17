"""
Requirement Impact Report repository — async PostgreSQL CRUD for persisted impact reports.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.impact_report import RequirementImpactReport


class ImpactRepository:
    """Data access repository for RequirementImpactReport entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, report: RequirementImpactReport) -> RequirementImpactReport:
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_by_id_and_project(
        self, report_id: UUID, project_id: UUID
    ) -> Optional[RequirementImpactReport]:
        result = await self.session.execute(
            select(RequirementImpactReport).where(
                RequirementImpactReport.id == report_id,
                RequirementImpactReport.project_id == project_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_for_requirement(
        self, project_id: UUID, requirement_id: UUID
    ) -> Optional[RequirementImpactReport]:
        result = await self.session.execute(
            select(RequirementImpactReport)
            .where(
                RequirementImpactReport.project_id == project_id,
                RequirementImpactReport.requirement_id == requirement_id,
            )
            .order_by(RequirementImpactReport.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_all_by_project(self, project_id: UUID) -> List[RequirementImpactReport]:
        result = await self.session.execute(
            select(RequirementImpactReport)
            .where(RequirementImpactReport.project_id == project_id)
            .order_by(RequirementImpactReport.created_at.desc())
        )
        return list(result.scalars().all())
