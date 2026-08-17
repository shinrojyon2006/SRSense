"""
Storage Manager for SRSense AI Uploaded Documents.

Handles file validation, path traversal protection, maximum size enforcement,
and safe local filesystem persistence under storage/uploads/.
"""

import os
import re
from pathlib import Path
from uuid import UUID
from fastapi import HTTPException, UploadFile, status

# Storage directory configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage" / "uploads"

# Security constraints
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/octet-stream",  # Fallback for plain text uploads on Windows
}


def ensure_storage_dir():
    """Ensure upload storage directory exists."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename preventing path traversal or dangerous characters."""
    filename = os.path.basename(filename)
    filename = re.sub(r"[^\w\.\-]", "_", filename)
    return filename or "document"


def validate_file(file: UploadFile, content: bytes):
    """Validate uploaded file size, extension, and MIME type."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: .pdf, .docx, .txt",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of 10 MB ({len(content)} bytes uploaded).",
        )

    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type '{file.content_type}'.",
        )


def save_uploaded_file(project_id: UUID, document_id: UUID, filename: str, content: bytes) -> Path:
    """Safely save uploaded content to local storage directory."""
    ensure_storage_dir()
    project_dir = STORAGE_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(filename).suffix.lower()
    file_path = (project_dir / f"{document_id}{ext}").resolve()

    # Path traversal protection
    if not file_path.is_relative_to(STORAGE_DIR.resolve()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path detected (path traversal attempt blocked).",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path


def delete_stored_file(storage_path: str):
    """Delete file from storage directory safely."""
    path = Path(storage_path).resolve()
    if path.exists() and path.is_relative_to(STORAGE_DIR.resolve()):
        try:
            os.remove(path)
        except OSError:
            pass
