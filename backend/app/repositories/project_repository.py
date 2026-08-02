"""
Project repository — data access layer for Project model.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project database operations."""

    model = Project

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_id_and_owner(
        self, project_id: UUID, owner_id: UUID
    ) -> Optional[Project]:
        """Fetch a project by ID ensuring it belongs to the given owner."""
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id, Project.owner_id == owner_id
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_owner(
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[Project]:
        """Fetch all projects owned by a user, with optional search filter."""
        query = select(Project).where(Project.owner_id == owner_id)
        if search:
            query = query.where(Project.title.ilike(f"%{search}%"))
        query = query.order_by(Project.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_owner(self, owner_id: UUID) -> int:
        """Count total projects owned by a user."""
        result = await self.db.execute(
            select(func.count(Project.id)).where(Project.owner_id == owner_id)
        )
        return result.scalar() or 0
