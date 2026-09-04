"""
API Router for Sprint 2.0 Code Intelligence.

Endpoints:
- POST   /api/projects/{project_id}/codebase/upload
- GET    /api/projects/{project_id}/codebase/
- GET    /api/projects/{project_id}/codebase/files
- GET    /api/projects/{project_id}/codebase/files/{file_id}
- GET    /api/projects/{project_id}/codebase/symbols
- GET    /api/projects/{project_id}/codebase/dependencies
- GET    /api/projects/{project_id}/codebase/links
- POST   /api/projects/{project_id}/codebase/links
- DELETE /api/projects/{project_id}/codebase/links/{link_id}
- DELETE /api/projects/{project_id}/codebase/
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.codebase_service import CodebaseService
from app.schemas.codebase import (
    CodebaseSummaryResponse,
    CodeFileSummaryResponse,
    CodeFileDetailResponse,
    CodeSymbolResponse,
    CodeDependencyResponse,
    RequirementCodeLinkCreate,
    RequirementCodeLinkResponse,
)

router = APIRouter(prefix="/projects/{project_id}/codebase", tags=["Code Intelligence"])


@router.post(
    "/upload",
    response_model=CodebaseSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index source code ZIP archive",
)
async def upload_codebase(
    project_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a ZIP archive containing source code, safely analyze AST, and index."""
    zip_bytes = await file.read()
    service = CodebaseService(db)
    return await service.ingest_zip_archive(
        user=current_user,
        project_id=project_id,
        zip_bytes=zip_bytes,
        filename=file.filename or "repository.zip",
    )


@router.get(
    "/",
    response_model=Optional[CodebaseSummaryResponse],
    summary="Get codebase overview and metrics",
)
async def get_codebase_summary(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get high-level statistics, detected languages, and indexing status."""
    service = CodebaseService(db)
    return await service.get_summary(user=current_user, project_id=project_id)


@router.get(
    "/files",
    response_model=List[CodeFileSummaryResponse],
    summary="List analyzed files with languages and line counts",
)
async def list_code_files(
    project_id: UUID,
    search: Optional[str] = Query(None, description="Search by file path or name"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List analyzed files in repository with language badges and symbol counts."""
    service = CodebaseService(db)
    return await service.list_files(
        user=current_user, project_id=project_id, search=search, language=language
    )


@router.get(
    "/files/{file_id}",
    response_model=CodeFileDetailResponse,
    summary="Get detailed AST symbols, imports, and endpoints for a file",
)
async def get_file_detail(
    project_id: UUID,
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full AST symbols, classes, functions, methods, and endpoints for a single file."""
    service = CodebaseService(db)
    return await service.get_file_detail(
        user=current_user, project_id=project_id, file_id=file_id
    )


@router.get(
    "/symbols",
    response_model=List[CodeSymbolResponse],
    summary="Search code symbols (classes, functions, endpoints, tables)",
)
async def search_symbols(
    project_id: UUID,
    q: str = Query(..., min_length=1, description="Symbol name substring query"),
    symbol_type: Optional[str] = Query(None, description="Filter by symbol type"),
    language: Optional[str] = Query(None, description="Filter by language"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search extracted code symbols across the entire indexed repository."""
    service = CodebaseService(db)
    return await service.search_symbols(
        user=current_user,
        project_id=project_id,
        query=q,
        symbol_type=symbol_type,
        language=language,
        limit=limit,
    )


@router.get(
    "/dependencies",
    response_model=List[CodeDependencyResponse],
    summary="Get discovered dependency and import relationships",
)
async def get_dependencies(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get import and dependency graph edges for the repository."""
    service = CodebaseService(db)
    return await service.get_dependencies(user=current_user, project_id=project_id)


@router.get(
    "/links",
    response_model=List[RequirementCodeLinkResponse],
    summary="List Requirement ↔ Code links",
)
async def list_requirement_code_links(
    project_id: UUID,
    requirement_id: Optional[UUID] = Query(None, description="Filter links for specific requirement"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List Requirement ↔ Code links for the project."""
    service = CodebaseService(db)
    return await service.list_links(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.post(
    "/links",
    response_model=RequirementCodeLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a manual Requirement ↔ Code link",
)
async def create_requirement_code_link(
    project_id: UUID,
    data: RequirementCodeLinkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a requirement to a discovered code file or symbol."""
    service = CodebaseService(db)
    return await service.create_link(
        user=current_user, project_id=project_id, data=data
    )


@router.delete(
    "/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Requirement ↔ Code link",
)
async def delete_requirement_code_link(
    project_id: UUID,
    link_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a Requirement ↔ Code link."""
    service = CodebaseService(db)
    await service.delete_link(user=current_user, project_id=project_id, link_id=link_id)


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete codebase and reset index for project",
)
async def delete_codebase(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear indexed codebase for this project."""
    service = CodebaseService(db)
    await service.delete_codebase(user=current_user, project_id=project_id)
