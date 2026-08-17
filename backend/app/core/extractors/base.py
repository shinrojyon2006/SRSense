"""
Base Text Extractor Interface and Extracted Text Data Models.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class TextSegment(BaseModel):
    """Single segment/page/paragraph of extracted text with location metadata."""

    location_label: str = Field(..., description="Page number or section title (e.g., 'Page 1', 'Section 2.1')")
    text: str = Field(..., description="Extracted textual content")


class ExtractedDocumentText(BaseModel):
    """Complete structured text extraction result from a document."""

    raw_text: str = Field(..., description="Full concatenated text content of the document")
    total_segments: int = Field(default=0, description="Total pages or sections extracted")
    word_count: int = Field(default=0, description="Total word count in extracted text")
    segments: List[TextSegment] = Field(default_factory=list, description="Segment breakdown")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class BaseTextExtractor(ABC):
    """Abstract Base Class for document text extractors."""

    @abstractmethod
    def extract_text(self, file_path: Path) -> ExtractedDocumentText:
        """Extract structured text and metadata from file."""
        pass
