"""
TXT Text Extractor implementation using UTF-8 decoding.
"""

from pathlib import Path
from app.core.extractors.base import BaseTextExtractor, ExtractedDocumentText, TextSegment


class TXTTextExtractor(BaseTextExtractor):
    """Extracts text line-by-line from plain text files."""

    def extract_text(self, file_path: Path) -> ExtractedDocumentText:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        segments = []
        full_text_list = []

        for idx, line in enumerate(lines, 1):
            text_cleaned = line.strip()
            if text_cleaned:
                segments.append(TextSegment(location_label=f"Line {idx}", text=text_cleaned))
                full_text_list.append(text_cleaned)

        raw_text = "\n".join(full_text_list)
        words = raw_text.split()

        return ExtractedDocumentText(
            raw_text=raw_text,
            total_segments=len(lines),
            word_count=len(words),
            segments=segments,
            metadata={"line_count": len(lines)},
        )
