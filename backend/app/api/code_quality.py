"""
Sprint 2.1 — Code Review & Code Quality Intelligence REST API Router.

Endpoints:
- POST /projects/{project_id}/codebase/review   (Trigger static analysis & quality review)
- GET  /projects/{project_id}/codebase/review   (Get latest code quality report)
- GET  /projects/{project_id}/codebase/findings (Query findings with filter/sort/pagination)
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.code_quality import FindingCategory, FindingSeverity
from app.models.user import User
from app.schemas.code_quality import (
    CodeReviewFindingsListResponse,
    CodeReviewReportResponse,
)
from app.services.code_quality_service import CodeQualityService

router = APIRouter(
    prefix="/projects/{project_id}/codebase", tags=["Code Quality Intelligence"]
)


@router.post("/review", response_model=CodeReviewReportResponse)
async def trigger_code_review(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger automated static code quality analysis and quality review scan."""
    service = CodeQualityService(db)
    return await service.run_code_review(user=current_user, project_id=project_id)


@router.get("/review", response_model=Optional[CodeReviewReportResponse])
async def get_latest_code_review(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest code review report for a project."""
    service = CodeQualityService(db)
    return await service.get_latest_review(user=current_user, project_id=project_id)


@router.get("/findings", response_model=CodeReviewFindingsListResponse)
async def query_code_findings(
    project_id: UUID,
    severity: Optional[FindingSeverity] = Query(None, description="Filter by severity (critical, warning, info)"),
    category: Optional[FindingCategory] = Query(None, description="Filter by category (security, performance, maintainability, compliance, quality)"),
    file_path: Optional[str] = Query(None, description="Filter by file path substring"),
    search: Optional[str] = Query(None, description="Search term for title, description, or rule ID"),
    sort_by: str = Query("severity", description="Sort field (severity, category, rule_id, file_path)"),
    sort_dir: str = Query("desc", description="Sort direction (asc, desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query code review findings with filtering, search, and pagination."""
    service = CodeQualityService(db)
    return await service.get_findings(
        user=current_user,
        project_id=project_id,
        severity=severity,
        category=category,
        file_path=file_path,
        search_query=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
