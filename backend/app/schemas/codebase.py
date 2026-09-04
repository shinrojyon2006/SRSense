"""
Pydantic Schemas for Sprint 2.0 Code Intelligence.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class CodebaseStatusEnum(str):
    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class CodeSymbolResponse(BaseModel):
    id: UUID
    file_id: UUID
    symbol_name: str
    symbol_type: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent_symbol_name: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class CodeFileSummaryResponse(BaseModel):
    id: UUID
    path: str
    filename: str
    language: str
    confidence: str
    size_bytes: int
    line_count: int
    symbol_count: int = 0
    endpoint_count: int = 0

    class Config:
        from_attributes = True


class CodeFileDetailResponse(BaseModel):
    id: UUID
    codebase_id: UUID
    project_id: UUID
    path: str
    filename: str
    language: str
    confidence: str
    size_bytes: int
    line_count: int
    imports: List[str] = Field(default_factory=list)
    exports: List[str] = Field(default_factory=list)
    endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    db_interactions: List[Dict[str, Any]] = Field(default_factory=list)
    symbols: List[CodeSymbolResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CodeDependencyResponse(BaseModel):
    id: UUID
    source_file_id: UUID
    source_file_path: Optional[str] = None
    target_file_id: Optional[UUID] = None
    target_file_path: Optional[str] = None
    target_module: str
    dependency_type: str

    class Config:
        from_attributes = True


class CodebaseSummaryResponse(BaseModel):
    id: UUID
    project_id: UUID
    repo_name: str
    status: str
    total_files: int
    total_lines: int
    total_classes: int
    total_functions: int
    languages_summary: Dict[str, int] = Field(default_factory=dict)
    supported_files_count: int = 0
    unsupported_files_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequirementCodeLinkCreate(BaseModel):
    requirement_id: UUID
    file_id: UUID
    symbol_id: Optional[UUID] = None
    link_type: str = "explicit_manual"
    notes: Optional[str] = None


class RequirementCodeLinkResponse(BaseModel):
    id: UUID
    project_id: UUID
    requirement_id: UUID
    requirement_title: Optional[str] = None
    requirement_identifier: Optional[str] = None
    file_id: UUID
    file_path: Optional[str] = None
    file_language: Optional[str] = None
    symbol_id: Optional[UUID] = None
    symbol_name: Optional[str] = None
    symbol_type: Optional[str] = None
    link_type: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SymbolSearchQuery(BaseModel):
    query: str
    symbol_type: Optional[str] = None
    language: Optional[str] = None
    limit: int = 50
