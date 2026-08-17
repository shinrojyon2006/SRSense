"""
Requirement Suggestion repository — async PostgreSQL CRUD for intelligence suggestions.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.relationship import RelationshipType
from app.models.suggestion import RequirementSuggestion, SuggestionStatus


class SuggestionRepository:
    """Data access repository for RequirementSuggestion entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, suggestion: RequirementSuggestion) -> RequirementSuggestion:
        self.session.add(suggestion)
        await self.session.commit()
        await self.session.refresh(suggestion)
        return suggestion

    async def get_by_id_and_project(
        self, suggestion_id: UUID, project_id: UUID
    ) -> Optional[RequirementSuggestion]:
        result = await self.session.execute(
            select(RequirementSuggestion).where(
                RequirementSuggestion.id == suggestion_id,
                RequirementSuggestion.project_id == project_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_existing_edge(
        self, project_id: UUID, source_id: UUID, target_id: UUID, rel_type: RelationshipType
    ) -> Optional[RequirementSuggestion]:
        result = await self.session.execute(
            select(RequirementSuggestion).where(
                RequirementSuggestion.project_id == project_id,
                RequirementSuggestion.source_id == source_id,
                RequirementSuggestion.target_id == target_id,
                RequirementSuggestion.relationship_type == rel_type,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_project(
        self,
        project_id: UUID,
        status: Optional[SuggestionStatus] = None,
        rel_type: Optional[RelationshipType] = None,
        min_confidence: Optional[float] = None,
    ) -> List[RequirementSuggestion]:
        stmt = select(RequirementSuggestion).where(RequirementSuggestion.project_id == project_id)
        if status:
            stmt = stmt.where(RequirementSuggestion.status == status)
        if rel_type:
            stmt = stmt.where(RequirementSuggestion.relationship_type == rel_type)
        if min_confidence is not None:
            stmt = stmt.where(RequirementSuggestion.confidence_score >= min_confidence)

        stmt = stmt.order_by(RequirementSuggestion.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, suggestion: RequirementSuggestion) -> RequirementSuggestion:
        await self.session.commit()
        await self.session.refresh(suggestion)
        return suggestion
