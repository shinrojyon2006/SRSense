"""
Async Repository for CodeTestArtifact and RequirementTestLink models.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.traceability import CodeTestArtifact, RequirementTestLink


class TraceabilityRepository:
    """Handles database persistence for discovered tests and requirement-test links."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_test_artifacts(
        self, artifacts: List[CodeTestArtifact]
    ) -> List[CodeTestArtifact]:
        """Bulk creates discovered test artifacts."""
        self.session.add_all(artifacts)
        await self.session.commit()
        for artifact in artifacts:
            await self.session.refresh(artifact)
        return artifacts

    async def get_test_artifacts_by_project(
        self, project_id: UUID
    ) -> List[CodeTestArtifact]:
        """Retrieves all test artifacts for a project."""
        result = await self.session.execute(
            select(CodeTestArtifact).where(CodeTestArtifact.project_id == project_id)
        )
        return list(result.scalars().all())

    async def clear_test_artifacts_by_codebase(self, codebase_id: UUID) -> None:
        """Removes existing test artifacts for a codebase before re-discovery."""
        await self.session.execute(
            delete(CodeTestArtifact).where(CodeTestArtifact.codebase_id == codebase_id)
        )
        await self.session.commit()

    async def create_requirement_test_links(
        self, links: List[RequirementTestLink]
    ) -> List[RequirementTestLink]:
        """Bulk creates requirement-test links."""
        self.session.add_all(links)
        await self.session.commit()
        for link in links:
            await self.session.refresh(link)
        return links

    async def get_test_links_by_project(
        self, project_id: UUID
    ) -> List[RequirementTestLink]:
        """Retrieves all requirement-test links for a project."""
        result = await self.session.execute(
            select(RequirementTestLink)
            .where(RequirementTestLink.project_id == project_id)
            .options(
                selectinload(RequirementTestLink.test_artifact),
                selectinload(RequirementTestLink.requirement),
            )
        )
        return list(result.scalars().all())

    async def get_test_link_by_id(
        self, link_id: UUID
    ) -> Optional[RequirementTestLink]:
        """Retrieves a single link by ID."""
        result = await self.session.execute(
            select(RequirementTestLink).where(RequirementTestLink.id == link_id)
        )
        return result.scalar_one_or_none()

    async def delete_link(self, link_id: UUID) -> bool:
        """Deletes a requirement-test link."""
        link = await self.get_test_link_by_id(link_id)
        if link:
            await self.session.delete(link)
            await self.session.commit()
            return True
        return False
