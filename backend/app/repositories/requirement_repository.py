"""
Requirement repository — data access layer for Requirement model.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import (
    Requirement,
    RequirementType,
    RequirementPriority,
    RequirementStatus,
)
from app.repositories.base import BaseRepository


class RequirementRepository(BaseRepository[Requirement]):
    """Repository for Requirement database operations."""

    model = Requirement

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_id_and_project(
        self, requirement_id: UUID, project_id: UUID
    ) -> Optional[Requirement]:
        """Fetch a requirement by ID ensuring it belongs to the given project."""
        result = await self.db.execute(
            select(Requirement).where(
                Requirement.id == requirement_id,
                Requirement.project_id == project_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_project(
        self,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        req_type: Optional[RequirementType] = None,
        priority: Optional[RequirementPriority] = None,
        status: Optional[RequirementStatus] = None,
    ) -> List[Requirement]:
        """Fetch all requirements in a project with optional filters."""
        query = select(Requirement).where(Requirement.project_id == project_id)

        if search:
            query = query.where(
                or_(
                    Requirement.title.ilike(f"%{search}%"),
                    Requirement.description.ilike(f"%{search}%"),
                )
            )
        if req_type:
            query = query.where(Requirement.type == req_type)
        if priority:
            query = query.where(Requirement.priority == priority)
        if status:
            query = query.where(Requirement.status == status)

        query = query.order_by(Requirement.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_project(self, project_id: UUID) -> int:
        """Count total requirements in a project."""
        result = await self.db.execute(
            select(func.count(Requirement.id)).where(Requirement.project_id == project_id)
        )
        return result.scalar() or 0
