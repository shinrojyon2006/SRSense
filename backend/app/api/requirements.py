"""
Requirement management API routes.

Handles CRUD operations for software requirement specifications in a project.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.requirement import (
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from app.models.user import User
from app.schemas.requirement import (
    RequirementCreate,
    RequirementResponse,
    RequirementUpdate,
)
from app.services.requirement_service import RequirementService

router = APIRouter(prefix="/projects/{project_id}/requirements", tags=["Requirements"])


@router.get("", response_model=List[RequirementResponse])
@router.get("/", response_model=List[RequirementResponse])
async def list_requirements(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = Query(None, description="Search title or description"),
    type: Optional[RequirementType] = Query(None, description="Filter by requirement type"),
    priority: Optional[RequirementPriority] = Query(None, description="Filter by priority"),
    status: Optional[RequirementStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all requirements in a project belonging to the authenticated user."""
    service = RequirementService(db)
    return await service.get_requirements(
        user=current_user,
        project_id=project_id,
        skip=skip,
        limit=limit,
        search=search,
        req_type=type,
        priority=priority,
        req_status=status,
    )


@router.post("", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    project_id: UUID,
    data: RequirementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new requirement inside a project."""
    service = RequirementService(db)
    return await service.create_requirement(
        user=current_user, project_id=project_id, data=data
    )


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific requirement."""
    service = RequirementService(db)
    return await service.get_requirement(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.put("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    project_id: UUID,
    requirement_id: UUID,
    data: RequirementUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing requirement."""
    service = RequirementService(db)
    return await service.update_requirement(
        user=current_user,
        project_id=project_id,
        requirement_id=requirement_id,
        data=data,
    )


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a requirement from a project."""
    service = RequirementService(db)
    await service.delete_requirement(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )
