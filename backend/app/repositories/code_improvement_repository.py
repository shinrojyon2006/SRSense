"""
Repository for Sprint 2.2 AI Code Improvement.
Handles persistent database queries for improvement proposals and review states.
"""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_improvement import CodeImprovementProposal, ImprovementStatus


class CodeImprovementRepository:
    """Async repository for CodeImprovementProposal database CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, proposal: CodeImprovementProposal) -> CodeImprovementProposal:
        self.session.add(proposal)
        await self.session.flush()
        return proposal

    async def get_by_id(self, proposal_id: UUID) -> Optional[CodeImprovementProposal]:
        stmt = select(CodeImprovementProposal).where(
            CodeImprovementProposal.id == proposal_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_project(
        self,
        project_id: UUID,
        status: Optional[ImprovementStatus] = None,
        finding_id: Optional[UUID] = None,
    ) -> List[CodeImprovementProposal]:
        stmt = (
            select(CodeImprovementProposal)
            .where(CodeImprovementProposal.project_id == project_id)
            .order_by(CodeImprovementProposal.created_at.desc())
        )
        if status:
            stmt = stmt.where(CodeImprovementProposal.status == status)
        if finding_id:
            stmt = stmt.where(CodeImprovementProposal.finding_id == finding_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, proposal: CodeImprovementProposal) -> CodeImprovementProposal:
        await self.session.flush()
        return proposal

    async def delete(self, proposal_id: UUID) -> bool:
        proposal = await self.get_by_id(proposal_id)
        if proposal:
            await self.session.delete(proposal)
            await self.session.flush()
            return True
        return False
