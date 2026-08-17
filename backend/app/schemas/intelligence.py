"""
Requirement Conflict & Dependency Intelligence Pydantic schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.relationship import RelationshipType
from app.models.suggestion import SuggestionStatus


class SuggestionResponse(BaseModel):
    """Intelligence suggestion response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    source_id: UUID
    target_id: UUID
    relationship_type: RelationshipType
    status: SuggestionStatus
    confidence_score: float
    conflict_category: Optional[str] = None
    evidence_explanation: str
    suggested_resolution: Optional[str] = None
    source_hash: str
    target_hash: str
    detector_version: str
    dismissal_reason: Optional[str] = None
    rejected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RejectSuggestionRequest(BaseModel):
    """Payload to reject or dismiss a suggestion."""

    reason: Optional[str] = Field(None, description="Optional dismissal reason")


class IntelligenceSummaryResponse(BaseModel):
    """Project Intelligence Summary DTO."""

    project_id: UUID
    total_conflicts: int
    unresolved_dependency_suggestions: int
    orphan_requirements_count: int
    high_confidence_issues_count: int
    confidence_distribution: Dict[str, int]


class ScanResponse(BaseModel):
    """Response payload for automated conflict and dependency scan."""

    project_id: UUID
    scanned_requirements_count: int
    new_suggestions_created: int
    existing_suggestions_updated: int
    reconsidered_suggestions_count: int
    total_suggestions: int
    suggestions: List[SuggestionResponse]
