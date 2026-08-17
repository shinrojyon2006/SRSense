"""
PDF Text Extractor implementation using pypdf.
"""

from pathlib import Path
from pypdf import PdfReader
from app.core.extractors.base import BaseTextExtractor, ExtractedDocumentText, TextSegment


class PDFTextExtractor(BaseTextExtractor):
    """Extracts text page-by-page from PDF files."""

    def extract_text(self, file_path: Path) -> ExtractedDocumentText:
        reader = PdfReader(str(file_path))
        segments = []
        full_text_list = []

        for idx, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            text_cleaned = text.strip()
            if text_cleaned:
                segments.append(TextSegment(location_label=f"Page {idx}", text=text_cleaned))
                full_text_list.append(text_cleaned)

        raw_text = "\n\n".join(full_text_list)
        words = raw_text.split()

        return ExtractedDocumentText(
            raw_text=raw_text,
            total_segments=len(reader.pages),
            word_count=len(words),
            segments=segments,
            metadata={"page_count": len(reader.pages)},
        )
