"""
Repository for CodeImprovementEvaluation ORM model operations (AsyncSession).
"""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_improvement_evaluation import CodeImprovementEvaluation


class CodeImprovementEvaluationRepository:
    """Handles CRUD persistence for code improvement evaluation records."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_evaluation(self, evaluation: CodeImprovementEvaluation) -> CodeImprovementEvaluation:
        """Persists a new evaluation record."""
        self.db.add(evaluation)
        await self.db.commit()
        await self.db.refresh(evaluation)
        return evaluation

    async def get_by_proposal_id(self, proposal_id: UUID) -> Optional[CodeImprovementEvaluation]:
        """Retrieves evaluation by improvement proposal ID."""
        res = await self.db.execute(
            select(CodeImprovementEvaluation).where(CodeImprovementEvaluation.proposal_id == proposal_id)
        )
        return res.scalars().first()

    async def get_by_id(self, evaluation_id: UUID) -> Optional[CodeImprovementEvaluation]:
        """Retrieves evaluation by its primary key ID."""
        res = await self.db.execute(
            select(CodeImprovementEvaluation).where(CodeImprovementEvaluation.id == evaluation_id)
        )
        return res.scalars().first()

    async def delete_by_proposal_id(self, proposal_id: UUID) -> bool:
        """Deletes existing evaluation for re-evaluation if needed."""
        existing = await self.get_by_proposal_id(proposal_id)
        if existing:
            await self.db.delete(existing)
            await self.db.commit()
            return True
        return False
