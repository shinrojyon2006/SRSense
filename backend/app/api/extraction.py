"""
Requirement Candidate Extraction & Batch Acceptance REST API router.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import dependencies
from app.models.user import User
from app.schemas.extraction import (
    BatchAcceptRequest,
    BatchAcceptResponse,
    ExtractionResponse,
)
from app.services.extraction_service import ExtractionService

router = APIRouter(tags=["Requirement Extraction Engine"])


@router.post(
    "/projects/{project_id}/documents/{document_id}/extract-candidates",
    response_model=ExtractionResponse,
)
async def extract_candidates(
    project_id: UUID,
    document_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Run requirement identification, classification, and duplicate detection on document text."""
    service = ExtractionService(db)
    return await service.extract_candidates_from_document(
        user=current_user, project_id=project_id, document_id=document_id
    )


@router.post(
    "/projects/{project_id}/extraction/batch-accept",
    response_model=BatchAcceptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def batch_accept_requirements(
    project_id: UUID,
    request: BatchAcceptRequest,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Persist accepted candidate requirements to PostgreSQL and atomically update project requirement_count."""
    service = ExtractionService(db)
    return await service.batch_accept_candidates(
        user=current_user, project_id=project_id, request=request
    )
