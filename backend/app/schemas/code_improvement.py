"""
Sprint 2.2 — Pydantic Schemas for AI Code Improvement proposals & review actions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.code_improvement import ImprovementStatus


class CodeImprovementCreateRequest(BaseModel):
    """Payload to request an AI code improvement proposal from a finding or file."""

    finding_id: Optional[UUID] = Field(
        None, description="Optional Sprint 2.1 finding ID to improve"
    )
    file_id: Optional[UUID] = Field(
        None, description="Optional target code file ID if no finding ID provided"
    )
    rule_id: Optional[str] = Field(
        None, description="Optional rule ID to target (e.g. SEC-001, SEC-003, QUAL-001)"
    )


class CodeImprovementResponse(BaseModel):
    """Response DTO representing a reviewable AI code improvement proposal."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    codebase_id: UUID
    finding_id: Optional[UUID] = None
    linked_requirement_id: Optional[UUID] = None

    rule_id: str
    title: str
    problem_summary: str
    root_cause: str
    recommendation: str

    file_id: Optional[UUID] = None
    file_path: str
    current_code: str
    proposed_code: str
    patch_diff: str

    affected_files: List[str] = Field(default_factory=list)
    affected_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    affected_tests: List[Dict[str, Any]] = Field(default_factory=list)
    risks: Optional[str] = None
    confidence: float = 85.0
    uncertainty: Optional[str] = None

    status: ImprovementStatus
    error_message: Optional[str] = None

    created_at: datetime
    reviewed_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None


class CodeImprovementListResponse(BaseModel):
    """Paginated list of code improvement proposals for a project."""

    total: int
    items: List[CodeImprovementResponse]
