"""
Project service — business logic for project operations.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.utils.logger import get_logger

logger = get_logger("srsense.project")


class ProjectService:
    """Service layer for project operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepository(db)

    async def create_project(self, user: User, data: ProjectCreate) -> ProjectResponse:
        """Create a new project owned by the current user."""
        status_val = (
            ProjectStatus(data.status.value)
            if data.status
            else ProjectStatus.ACTIVE
        )
        project = Project(
            title=data.title,
            description=data.description or "",
            status=status_val,
            requirement_count=0,
            owner_id=user.id,
        )
        created = await self.repo.create(project)
        logger.info("Project created: %s (id=%s) by user %s", created.title, created.id, user.email)
        return ProjectResponse.model_validate(created)

    async def get_projects(
        self,
        user: User,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[ProjectResponse]:
        """Get all projects belonging to the user."""
        projects = await self.repo.get_all_by_owner(
            owner_id=user.id, skip=skip, limit=limit, search=search
        )
        return [ProjectResponse.model_validate(p) for p in projects]

    async def get_project(self, user: User, project_id: UUID) -> ProjectResponse:
        """Get a specific project by ID for the user."""
        project = await self.repo.get_by_id_and_owner(
            project_id=project_id, owner_id=user.id
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return ProjectResponse.model_validate(project)

    async def update_project(
        self, user: User, project_id: UUID, data: ProjectUpdate
    ) -> ProjectResponse:
        """Update an existing project owned by the user."""
        project = await self.repo.get_by_id_and_owner(
            project_id=project_id, owner_id=user.id
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if data.title is not None:
            project.title = data.title
        if data.description is not None:
            project.description = data.description
        if data.status is not None:
            project.status = ProjectStatus(data.status.value)
        if data.requirement_count is not None:
            project.requirement_count = data.requirement_count

        updated = await self.repo.update(project)
        logger.info("Project updated: %s (id=%s)", updated.title, updated.id)
        return ProjectResponse.model_validate(updated)

    async def delete_project(self, user: User, project_id: UUID) -> None:
        """Delete a project owned by the user."""
        project = await self.repo.get_by_id_and_owner(
            project_id=project_id, owner_id=user.id
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        await self.repo.delete(project)
        logger.info("Project deleted: id=%s by user %s", project_id, user.email)
