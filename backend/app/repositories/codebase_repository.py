"""
Repository for Sprint 2.0 Code Intelligence.

Handles async database queries for Codebases, Files, Symbols,
Dependencies, and RequirementCodeLinks.
"""

from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, or_, and_
from sqlalchemy.orm import selectinload, joinedload

from app.models.codebase import (
    Codebase,
    CodeFile,
    CodeSymbol,
    CodeDependency,
    RequirementCodeLink,
    CodebaseStatus,
)
from app.models.requirement import Requirement


class CodebaseRepository:
    """Async repository for Codebase data access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_project(self, project_id: UUID) -> Optional[Codebase]:
        """Fetch codebase overview for a project."""
        stmt = (
            select(Codebase)
            .where(Codebase.project_id == project_id)
            .order_by(Codebase.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, codebase: Codebase) -> Codebase:
        self.session.add(codebase)
        await self.session.flush()
        return codebase

    async def update(self, codebase: Codebase) -> Codebase:
        await self.session.flush()
        return codebase

    async def delete_by_project(self, project_id: UUID) -> bool:
        stmt = select(Codebase).where(Codebase.project_id == project_id)
        result = await self.session.execute(stmt)
        cb = result.scalars().first()
        if cb:
            await self.session.delete(cb)
            await self.session.flush()
            return True
        return False

    async def get_files(
        self,
        codebase_id: UUID,
        search: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[CodeFile]:
        stmt = (
            select(CodeFile)
            .where(CodeFile.codebase_id == codebase_id)
            .options(selectinload(CodeFile.symbols))
            .order_by(CodeFile.path.asc())
        )
        if search:
            stmt = stmt.where(
                or_(
                    CodeFile.filename.ilike(f"%{search}%"),
                    CodeFile.path.ilike(f"%{search}%"),
                )
            )
        if language and language.lower() != "all":
            stmt = stmt.where(CodeFile.language == language)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_file_by_id(self, file_id: UUID, project_id: UUID) -> Optional[CodeFile]:
        stmt = (
            select(CodeFile)
            .where(and_(CodeFile.id == file_id, CodeFile.project_id == project_id))
            .options(selectinload(CodeFile.symbols))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def search_symbols(
        self,
        project_id: UUID,
        query: str,
        symbol_type: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 50,
    ) -> List[CodeSymbol]:
        stmt = (
            select(CodeSymbol)
            .join(CodeFile, CodeSymbol.file_id == CodeFile.id)
            .where(CodeSymbol.project_id == project_id)
            .where(CodeSymbol.symbol_name.ilike(f"%{query}%"))
            .options(joinedload(CodeSymbol.file))
            .limit(limit)
        )
        if symbol_type and symbol_type.lower() != "all":
            stmt = stmt.where(CodeSymbol.symbol_type == symbol_type.lower())
        if language and language.lower() != "all":
            stmt = stmt.where(CodeFile.language == language)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_dependencies(self, codebase_id: UUID) -> List[CodeDependency]:
        stmt = (
            select(CodeDependency)
            .where(CodeDependency.codebase_id == codebase_id)
            .options(
                joinedload(CodeDependency.source_file),
                joinedload(CodeDependency.target_file),
            )
            .limit(500)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_link(self, link: RequirementCodeLink) -> RequirementCodeLink:
        self.session.add(link)
        await self.session.flush()
        return link

    async def get_links(
        self, project_id: UUID, requirement_id: Optional[UUID] = None
    ) -> List[RequirementCodeLink]:
        stmt = (
            select(RequirementCodeLink)
            .where(RequirementCodeLink.project_id == project_id)
            .options(
                joinedload(RequirementCodeLink.requirement),
                joinedload(RequirementCodeLink.file),
                joinedload(RequirementCodeLink.symbol),
            )
            .order_by(RequirementCodeLink.created_at.desc())
        )
        if requirement_id:
            stmt = stmt.where(RequirementCodeLink.requirement_id == requirement_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_link(self, link_id: UUID, project_id: UUID) -> bool:
        stmt = select(RequirementCodeLink).where(
            and_(RequirementCodeLink.id == link_id, RequirementCodeLink.project_id == project_id)
        )
        result = await self.session.execute(stmt)
        link = result.scalars().first()
        if link:
            await self.session.delete(link)
            await self.session.flush()
            return True
        return False
