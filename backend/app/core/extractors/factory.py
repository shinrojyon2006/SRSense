"""
Extractor Factory — Instantiates appropriate BaseTextExtractor based on document type.
"""

from fastapi import HTTPException, status
from app.core.extractors.base import BaseTextExtractor
from app.core.extractors.docx_extractor import DOCXTextExtractor
from app.core.extractors.pdf_extractor import PDFTextExtractor
from app.core.extractors.txt_extractor import TXTTextExtractor


class ExtractorFactory:
    """Factory for text extractor instances."""

    @staticmethod
    def get_extractor(file_type: str) -> BaseTextExtractor:
        file_type_clean = file_type.lower().lstrip(".")
        if file_type_clean == "pdf":
            return PDFTextExtractor()
        elif file_type_clean == "docx":
            return DOCXTextExtractor()
        elif file_type_clean == "txt":
            return TXTTextExtractor()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No extractor registered for document type '{file_type}'.",
            )
