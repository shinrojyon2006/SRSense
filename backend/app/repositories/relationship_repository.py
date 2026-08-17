"""
Requirement Relationship repository — async PostgreSQL CRUD for graph edges.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.relationship import RequirementRelationship, RelationshipType


class RelationshipRepository:
    """Data access repository for RequirementRelationship entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, relationship: RequirementRelationship) -> RequirementRelationship:
        self.session.add(relationship)
        await self.session.commit()
        await self.session.refresh(relationship)
        return relationship

    async def get_by_id(self, relationship_id: UUID) -> Optional[RequirementRelationship]:
        result = await self.session.execute(
            select(RequirementRelationship).where(RequirementRelationship.id == relationship_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_project(
        self, relationship_id: UUID, project_id: UUID
    ) -> Optional[RequirementRelationship]:
        result = await self.session.execute(
            select(RequirementRelationship).where(
                RequirementRelationship.id == relationship_id,
                RequirementRelationship.project_id == project_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_existing_edge(
        self, project_id: UUID, source_id: UUID, target_id: UUID, rel_type: RelationshipType
    ) -> Optional[RequirementRelationship]:
        result = await self.session.execute(
            select(RequirementRelationship).where(
                RequirementRelationship.project_id == project_id,
                RequirementRelationship.source_id == source_id,
                RequirementRelationship.target_id == target_id,
                RequirementRelationship.type == rel_type,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_project(self, project_id: UUID) -> List[RequirementRelationship]:
        result = await self.session.execute(
            select(RequirementRelationship)
            .where(RequirementRelationship.project_id == project_id)
            .order_by(RequirementRelationship.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_all_depends_on_by_project(self, project_id: UUID) -> List[RequirementRelationship]:
        result = await self.session.execute(
            select(RequirementRelationship).where(
                RequirementRelationship.project_id == project_id,
                RequirementRelationship.type == RelationshipType.DEPENDS_ON,
            )
        )
        return list(result.scalars().all())

    async def get_by_requirement(
        self, project_id: UUID, requirement_id: UUID
    ) -> List[RequirementRelationship]:
        result = await self.session.execute(
            select(RequirementRelationship).where(
                RequirementRelationship.project_id == project_id,
                or_(
                    RequirementRelationship.source_id == requirement_id,
                    RequirementRelationship.target_id == requirement_id,
                ),
            )
        )
        return list(result.scalars().all())

    async def delete(self, relationship: RequirementRelationship) -> None:
        await self.session.delete(relationship)
        await self.session.commit()
