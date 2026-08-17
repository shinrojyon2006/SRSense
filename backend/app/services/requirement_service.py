"""
Requirement service — business logic for requirement operations.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import (
    Requirement,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_repository import RequirementRepository
from app.schemas.requirement import (
    RequirementCreate,
    RequirementResponse,
    RequirementUpdate,
)
from app.utils.logger import get_logger

logger = get_logger("srsense.requirement")


class RequirementService:
    """Service layer for requirement operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RequirementRepository(db)
        self.project_repo = ProjectRepository(db)

    async def _verify_project_ownership(self, project_id: UUID, user: User):
        """Helper to ensure project exists and belongs to the current user."""
        project = await self.project_repo.get_by_id_and_owner(
            project_id=project_id, owner_id=user.id
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )
        return project

    async def create_requirement(
        self, user: User, project_id: UUID, data: RequirementCreate
    ) -> RequirementResponse:
        """Create a new requirement inside a project and increment project counter atomically."""
        project = await self._verify_project_ownership(project_id, user)

        req_type = RequirementType(data.type.value) if data.type else RequirementType.FUNCTIONAL
        req_priority = RequirementPriority(data.priority.value) if data.priority else RequirementPriority.MEDIUM
        req_status = RequirementStatus(data.status.value) if data.status else RequirementStatus.DRAFT

        requirement = Requirement(
            title=data.title,
            description=data.description,
            type=req_type,
            priority=req_priority,
            status=req_status,
            version=data.version or "1.0",
            source=data.source or "User Input",
            project_id=project_id,
            parent_id=data.parent_id,
        )
        self.db.add(requirement)
        project.requirement_count += 1
        await self.db.commit()
        await self.db.refresh(requirement)

        logger.info(
            "Requirement created: %s (id=%s) in project %s",
            requirement.title,
            requirement.id,
            project_id,
        )
        return RequirementResponse.model_validate(requirement)

    async def get_requirements(
        self,
        user: User,
        project_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        req_type: Optional[RequirementType] = None,
        priority: Optional[RequirementPriority] = None,
        req_status: Optional[RequirementStatus] = None,
    ) -> List[RequirementResponse]:
        """Get all requirements for a project."""
        await self._verify_project_ownership(project_id, user)

        requirements = await self.repo.get_all_by_project(
            project_id=project_id,
            skip=skip,
            limit=limit,
            search=search,
            req_type=req_type,
            priority=priority,
            status=req_status,
        )
        return [RequirementResponse.model_validate(r) for r in requirements]

    async def get_requirement(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> RequirementResponse:
        """Get a single requirement by ID."""
        await self._verify_project_ownership(project_id, user)

        req = await self.repo.get_by_id_and_project(
            requirement_id=requirement_id, project_id=project_id
        )
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found",
            )
        return RequirementResponse.model_validate(req)

    async def update_requirement(
        self,
        user: User,
        project_id: UUID,
        requirement_id: UUID,
        data: RequirementUpdate,
    ) -> RequirementResponse:
        """Update an existing requirement."""
        await self._verify_project_ownership(project_id, user)

        req = await self.repo.get_by_id_and_project(
            requirement_id=requirement_id, project_id=project_id
        )
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found",
            )

        if data.title is not None:
            req.title = data.title
        if data.description is not None:
            req.description = data.description
        if data.type is not None:
            req.type = RequirementType(data.type.value)
        if data.priority is not None:
            req.priority = RequirementPriority(data.priority.value)
        if data.status is not None:
            req.status = RequirementStatus(data.status.value)
        if data.version is not None:
            req.version = data.version
        if data.source is not None:
            req.source = data.source
        if data.quality_score is not None:
            req.quality_score = data.quality_score
        if data.analysis_result is not None:
            req.analysis_result = data.analysis_result
        if data.parent_id is not None:
            req.parent_id = data.parent_id

        updated = await self.repo.update(req)
        logger.info("Requirement updated: %s (id=%s)", updated.title, updated.id)
        return RequirementResponse.model_validate(updated)

    async def delete_requirement(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> None:
        """Delete a requirement and decrement project counter atomically."""
        project = await self._verify_project_ownership(project_id, user)

        req = await self.repo.get_by_id_and_project(
            requirement_id=requirement_id, project_id=project_id
        )
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found",
            )

        if project.requirement_count > 0:
            project.requirement_count -= 1

        await self.db.delete(req)
        await self.db.commit()

        logger.info("Requirement deleted: id=%s from project %s", requirement_id, project_id)
