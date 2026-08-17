"""
Document Service — business logic for document uploads, ownership verification,
storage management, and text extraction.
"""

from pathlib import Path
from typing import List
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.extractors.base import ExtractedDocumentText
from app.core.extractors.factory import ExtractorFactory
from app.core.storage import (
    delete_stored_file,
    sanitize_filename,
    save_uploaded_file,
    validate_file,
)
from app.models.document import Document, DocumentFileType, DocumentStatus
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.document import DocumentResponse, DocumentTextResponse
from app.utils.logger import get_logger

logger = get_logger("srsense.document_service")


class DocumentService:
    """Service layer for document operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.project_repo = ProjectRepository(db)

    async def _verify_project_ownership(self, project_id: UUID, user: User):
        """Verify project belongs to current authenticated user."""
        project = await self.project_repo.get_by_id_and_owner(
            project_id=project_id, owner_id=user.id
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )
        return project

    async def upload_document(
        self, user: User, project_id: UUID, file: UploadFile
    ) -> DocumentResponse:
        """Validate, store, and process uploaded SRS document."""
        await self._verify_project_ownership(project_id, user)

        filename = sanitize_filename(file.filename or "document.txt")
        ext = Path(filename).suffix.lower().lstrip(".")

        content = await file.read()
        validate_file(file, content)

        doc_id = uuid4()
        file_path = save_uploaded_file(
            project_id=project_id,
            document_id=doc_id,
            filename=filename,
            content=content,
        )

        doc = Document(
            id=doc_id,
            project_id=project_id,
            filename=filename,
            file_type=DocumentFileType(ext),
            file_size=len(content),
            storage_path=str(file_path),
            status=DocumentStatus.EXTRACTING,
        )
        await self.doc_repo.create(doc)

        # Execute Text Extractor
        try:
            extractor = ExtractorFactory.get_extractor(ext)
            extracted: ExtractedDocumentText = extractor.extract_text(file_path)

            doc.status = DocumentStatus.EXTRACTED
            doc.doc_metadata = {
                **extracted.metadata,
                "word_count": extracted.word_count,
                "total_segments": extracted.total_segments,
            }
            updated = await self.doc_repo.update(doc)
            logger.info("Successfully uploaded and extracted text from %s (%d words)", filename, extracted.word_count)
            return DocumentResponse.model_validate(updated)

        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            updated = await self.doc_repo.update(doc)
            logger.error("Text extraction failed for %s: %s", filename, str(e))
            return DocumentResponse.model_validate(updated)

    async def get_documents(self, user: User, project_id: UUID) -> List[DocumentResponse]:
        """List all documents uploaded to project."""
        await self._verify_project_ownership(project_id, user)
        docs = await self.doc_repo.get_all_by_project(project_id)
        return [DocumentResponse.model_validate(d) for d in docs]

    async def get_document(self, user: User, project_id: UUID, document_id: UUID) -> DocumentResponse:
        """Get document details by ID."""
        await self._verify_project_ownership(project_id, user)
        doc = await self.doc_repo.get_by_id_and_project(document_id, project_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return DocumentResponse.model_validate(doc)

    async def get_extracted_text(
        self, user: User, project_id: UUID, document_id: UUID
    ) -> DocumentTextResponse:
        """Retrieve extracted raw text and segment breakdown for preview."""
        await self._verify_project_ownership(project_id, user)
        doc = await self.doc_repo.get_by_id_and_project(document_id, project_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        file_path = Path(doc.storage_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stored document file missing on disk",
            )

        extractor = ExtractorFactory.get_extractor(doc.file_type.value)
        extracted: ExtractedDocumentText = extractor.extract_text(file_path)

        return DocumentTextResponse(
            document_id=doc.id,
            filename=doc.filename,
            raw_text=extracted.raw_text,
            total_segments=extracted.total_segments,
            word_count=extracted.word_count,
            segments=extracted.segments,
            metadata=extracted.metadata,
        )

    async def delete_document(self, user: User, project_id: UUID, document_id: UUID) -> None:
        """Delete document from DB and local storage."""
        await self._verify_project_ownership(project_id, user)
        doc = await self.doc_repo.get_by_id_and_project(document_id, project_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        delete_stored_file(doc.storage_path)
        await self.doc_repo.delete(doc)
        logger.info("Deleted document %s (%s)", document_id, doc.filename)
