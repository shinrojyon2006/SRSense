"""
Secure Codebase Ingestion Engine for Sprint 2.0.

Provides safe archive extraction, path traversal / zip-slip protection,
strict size/count limits, ignore list filtering, and static text reading.
"""

import io
import os
import zipfile
from dataclasses import dataclass
from typing import List, Tuple, Optional

from app.core.exceptions import ValidationError


@dataclass
class ExtractedSourceFile:
    rel_path: str
    filename: str
    content: str
    size_bytes: int


class CodebaseIngestionEngine:
    """Safely validates, extracts, and reads source files from archives or directories."""

    # Security limits
    MAX_ARCHIVE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
    MAX_FILE_COUNT = 2000                      # 2,000 files
    MAX_INDIVIDUAL_FILE_SIZE = 2 * 1024 * 1024 # 2 MB

    # Directories to ignore
    IGNORED_DIRS = {
        ".git",
        ".svn",
        ".hg",
        "node_modules",
        ".venv",
        "venv",
        "env",
        "vendor",
        "bower_components",
        "dist",
        "build",
        "target",
        "out",
        ".next",
        ".nuxt",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".idea",
        ".vscode",
    }

    # Binary and non-source extensions to ignore
    IGNORED_EXTENSIONS = {
        ".exe", ".dll", ".so", ".dylib", ".pyc", ".class", ".o", ".obj",
        ".bin", ".zip", ".tar", ".gz", ".7z", ".rar", ".iso", ".jar", ".war",
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".bmp",
        ".mp4", ".mp3", ".wav", ".avi", ".mov",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".woff", ".woff2", ".ttf", ".eot", ".otf",
        ".lock", ".ds_store",
    }

    @classmethod
    def validate_and_extract_zip(
        cls, zip_bytes: bytes, original_filename: str = "repo.zip"
    ) -> List[ExtractedSourceFile]:
        """Validate ZIP archive against security rules and extract text source files."""
        if len(zip_bytes) > cls.MAX_ARCHIVE_SIZE_BYTES:
            raise ValidationError(
                f"Archive size ({len(zip_bytes) / 1024 / 1024:.1f} MB) exceeds maximum allowed limit of 50 MB."
            )

        try:
            zip_buffer = io.BytesIO(zip_bytes)
            with zipfile.ZipFile(zip_buffer, "r") as zf:
                infolist = zf.infolist()

                if len(infolist) > cls.MAX_FILE_COUNT:
                    raise ValidationError(
                        f"Archive contains {len(infolist)} entries, exceeding maximum limit of {cls.MAX_FILE_COUNT} files."
                    )

                extracted_files: List[ExtractedSourceFile] = []

                for info in infolist:
                    # Skip directories
                    if info.is_dir():
                        continue

                    raw_path = info.filename.replace("\\", "/")

                    # 1. Zip-Slip / Path Traversal Protection
                    if cls._is_path_traversal(raw_path):
                        raise ValidationError(
                            f"Security violation: Archive contains malicious path traversal entry '{raw_path}'."
                        )

                    # Normalize path (strip leading slashes or common root folder if present)
                    clean_path = raw_path.lstrip("/")

                    # 2. Check if inside ignored directories
                    if cls._is_ignored_path(clean_path):
                        continue

                    # 3. Check ignored extensions
                    _, ext = os.path.splitext(clean_path.lower())
                    if ext in cls.IGNORED_EXTENSIONS:
                        continue

                    # 4. Check individual file size
                    if info.file_size > cls.MAX_INDIVIDUAL_FILE_SIZE:
                        # Skip oversized files rather than failing entire archive
                        continue

                    # 5. Read file content safely as UTF-8 static text
                    try:
                        with zf.open(info) as file_handle:
                            raw_content = file_handle.read()
                            # Decode as text, replacing invalid characters
                            text_content = raw_content.decode("utf-8", errors="replace")
                            
                            extracted_files.append(
                                ExtractedSourceFile(
                                    rel_path=clean_path,
                                    filename=os.path.basename(clean_path),
                                    content=text_content,
                                    size_bytes=len(raw_content),
                                )
                            )
                    except Exception:
                        # Non-text or corrupted file inside zip, ignore safely
                        continue

                return extracted_files

        except zipfile.BadZipFile:
            raise ValidationError("The uploaded file is not a valid or readable ZIP archive.")

    @classmethod
    def _is_path_traversal(cls, path: str) -> bool:
        """Check if path contains directory traversal patterns or absolute roots."""
        normalized = os.path.normpath(path).replace("\\", "/")
        if normalized.startswith("../") or "/../" in normalized or normalized == "..":
            return True
        if os.path.isabs(path):
            return True
        if ":" in path:  # Windows drive letter (e.g., C:/)
            return True
        return False

    @classmethod
    def _is_ignored_path(cls, path: str) -> bool:
        """Check if path traverses an ignored directory."""
        parts = path.split("/")
        return any(part in cls.IGNORED_DIRS for part in parts)
