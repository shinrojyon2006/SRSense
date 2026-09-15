"""
Pydantic Schemas for Sprint 2.1 Code Review & Code Quality Intelligence API.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.code_quality import CodeHealthStatus, FindingCategory, FindingSeverity


class CodeReviewFindingResponse(BaseModel):
    id: UUID
    report_id: UUID
    file_id: Optional[UUID] = None
    file_path: str
    line_number: Optional[int] = None
    category: FindingCategory
    severity: FindingSeverity
    title: str
    description: str
    rule_id: str
    suggestion: str
    ai_explanation: Optional[str] = None
    snippet: Optional[str] = None
    linked_requirement_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CodeReviewReportResponse(BaseModel):
    id: UUID
    project_id: UUID
    codebase_id: UUID
    overall_score: int
    health_status: CodeHealthStatus
    summary: Optional[str] = None
    total_files_analyzed: int
    total_issues_count: int
    critical_count: int
    warning_count: int
    info_count: int
    category_counts: Dict[str, int]
    created_at: datetime
    findings_preview: Optional[List[CodeReviewFindingResponse]] = None

    class Config:
        from_attributes = True


class CodeReviewFindingsListResponse(BaseModel):
    total_findings: int
    report_id: UUID
    page: int
    page_size: int
    findings: List[CodeReviewFindingResponse]
