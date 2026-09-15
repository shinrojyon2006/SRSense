"""
Sprint 2.2 — AI Code Improvement REST API Router.

Endpoints:
- POST /projects/{project_id}/codebase/improvements           (Generate proposed improvement)
- GET  /projects/{project_id}/codebase/improvements           (List proposals)
- GET  /projects/{project_id}/codebase/improvements/{id}      (Get proposal detail)
- POST /projects/{project_id}/codebase/improvements/{id}/approve (Approve & apply patch)
- POST /projects/{project_id}/codebase/improvements/{id}/reject  (Reject proposal)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.code_improvement import ImprovementStatus
from app.models.user import User
from app.schemas.code_improvement import (
    CodeImprovementCreateRequest,
    CodeImprovementListResponse,
    CodeImprovementResponse,
)
from app.services.code_improvement_service import CodeImprovementService

router = APIRouter(
    prefix="/projects/{project_id}/codebase/improvements",
    tags=["Code Improvement Intelligence"],
)


@router.post("", response_model=CodeImprovementResponse, status_code=status.HTTP_201_CREATED)
async def create_code_improvement(
    project_id: UUID,
    payload: CodeImprovementCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a reviewable AI code improvement proposal for a finding or file."""
    service = CodeImprovementService(db)
    return await service.create_improvement_proposal(
        user=current_user, project_id=project_id, req=payload
    )


@router.get("", response_model=CodeImprovementListResponse)
async def list_code_improvements(
    project_id: UUID,
    status_filter: Optional[ImprovementStatus] = Query(None, alias="status"),
    finding_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List code improvement proposals for a project."""
    service = CodeImprovementService(db)
    return await service.list_improvements(
        user=current_user,
        project_id=project_id,
        status_filter=status_filter,
        finding_id=finding_id,
    )


@router.get("/{improvement_id}", response_model=CodeImprovementResponse)
async def get_code_improvement(
    project_id: UUID,
    improvement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a specific AI code improvement proposal."""
    service = CodeImprovementService(db)
    return await service.get_improvement(
        user=current_user, project_id=project_id, improvement_id=improvement_id
    )


@router.post("/{improvement_id}/approve", response_model=CodeImprovementResponse)
async def approve_and_apply_code_improvement(
    project_id: UUID,
    improvement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Explicitly approve and safely apply a reviewed patch to the codebase."""
    service = CodeImprovementService(db)
    return await service.approve_and_apply_improvement(
        user=current_user, project_id=project_id, improvement_id=improvement_id
    )


@router.post("/{improvement_id}/reject", response_model=CodeImprovementResponse)
async def reject_code_improvement(
    project_id: UUID,
    improvement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Explicitly reject a proposed code improvement."""
    service = CodeImprovementService(db)
    return await service.reject_improvement(
        user=current_user, project_id=project_id, improvement_id=improvement_id
    )
