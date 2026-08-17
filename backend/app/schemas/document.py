"""
Document Pydantic schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.core.extractors.base import TextSegment
from app.models.document import DocumentFileType, DocumentStatus


class DocumentResponse(BaseModel):
    """Document entity metadata response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    filename: str
    file_type: DocumentFileType
    file_size: int
    status: DocumentStatus
    error_message: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DocumentTextResponse(BaseModel):
    """Document extracted text response schema."""

    document_id: UUID
    filename: str
    raw_text: str
    total_segments: int
    word_count: int
    segments: List[TextSegment]
    metadata: Dict[str, Any]
