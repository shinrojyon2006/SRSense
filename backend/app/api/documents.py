"""
Document REST API router.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import dependencies
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentTextResponse
from app.services.document_service import DocumentService

router = APIRouter(tags=["Document Ingestion"])


@router.post(
    "/projects/{project_id}/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Upload an SRS document (PDF, DOCX, TXT up to 10 MB) to project."""
    service = DocumentService(db)
    return await service.upload_document(user=current_user, project_id=project_id, file=file)


@router.get("/projects/{project_id}/documents", response_model=List[DocumentResponse])
async def get_documents(
    project_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """List all documents uploaded to a project."""
    service = DocumentService(db)
    return await service.get_documents(user=current_user, project_id=project_id)


@router.get(
    "/projects/{project_id}/documents/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    project_id: UUID,
    document_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Get single document metadata by ID."""
    service = DocumentService(db)
    return await service.get_document(
        user=current_user, project_id=project_id, document_id=document_id
    )


@router.get(
    "/projects/{project_id}/documents/{document_id}/text",
    response_model=DocumentTextResponse,
)
async def get_extracted_text(
    project_id: UUID,
    document_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Get extracted text preview and page/segment breakdown."""
    service = DocumentService(db)
    return await service.get_extracted_text(
        user=current_user, project_id=project_id, document_id=document_id
    )


@router.delete("/projects/{project_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    project_id: UUID,
    document_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Delete document and stored file."""
    service = DocumentService(db)
    await service.delete_document(
        user=current_user, project_id=project_id, document_id=document_id
    )
