"""
Requirement Conflict & Dependency Intelligence REST API router.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import dependencies
from app.models.relationship import RelationshipType
from app.models.suggestion import SuggestionStatus
from app.models.user import User
from app.schemas.intelligence import (
    IntelligenceSummaryResponse,
    RejectSuggestionRequest,
    ScanResponse,
    SuggestionResponse,
)
from app.services.intelligence_service import IntelligenceService

router = APIRouter(tags=["Requirement Intelligence"])


@router.post(
    "/projects/{project_id}/intelligence/scan",
    response_model=ScanResponse,
)
async def run_intelligence_scan(
    project_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Run automated conflict and dependency discovery scan."""
    service = IntelligenceService(db)
    return await service.run_intelligence_scan(user=current_user, project_id=project_id)


@router.get(
    "/projects/{project_id}/intelligence/summary",
    response_model=IntelligenceSummaryResponse,
)
async def get_intelligence_summary(
    project_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Get project intelligence summary stats (conflicts, unresolved dependencies, orphans)."""
    service = IntelligenceService(db)
    return await service.get_intelligence_summary(user=current_user, project_id=project_id)


@router.get(
    "/projects/{project_id}/intelligence/suggestions",
    response_model=List[SuggestionResponse],
)
async def get_suggestions(
    project_id: UUID,
    status_filter: Optional[SuggestionStatus] = Query(None, alias="status"),
    type_filter: Optional[RelationshipType] = Query(None, alias="type"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Get suggestions for a project with optional status and confidence filtering."""
    service = IntelligenceService(db)
    return await service.get_suggestions(
        user=current_user,
        project_id=project_id,
        status_filter=status_filter,
        rel_type_filter=type_filter,
        min_confidence=min_confidence,
    )


@router.post(
    "/projects/{project_id}/intelligence/suggestions/{suggestion_id}/accept",
    response_model=SuggestionResponse,
)
async def accept_suggestion(
    project_id: UUID,
    suggestion_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Accept suggestion -> creates active Knowledge Graph edge & sets status ACCEPTED."""
    service = IntelligenceService(db)
    return await service.accept_suggestion(
        user=current_user, project_id=project_id, suggestion_id=suggestion_id
    )


@router.post(
    "/projects/{project_id}/intelligence/suggestions/{suggestion_id}/reject",
    response_model=SuggestionResponse,
)
async def reject_suggestion(
    project_id: UUID,
    suggestion_id: UUID,
    payload: Optional[RejectSuggestionRequest] = None,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Reject suggestion -> sets status REJECTED & records dismissal reason."""
    reason = payload.reason if payload else None
    service = IntelligenceService(db)
    return await service.reject_suggestion(
        user=current_user,
        project_id=project_id,
        suggestion_id=suggestion_id,
        reason=reason,
    )
