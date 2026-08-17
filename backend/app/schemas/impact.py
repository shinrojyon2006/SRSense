"""
Requirement Change Impact & Risk Simulator Pydantic schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.impact_report import ChangeType
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType


class WhatIfSimulationRequest(BaseModel):
    """Payload to simulate a proposed requirement change without database mutation."""

    requirement_id: Optional[UUID] = Field(None, description="Optional existing requirement UUID")
    proposed_title: str = Field(..., min_length=2, max_length=200)
    proposed_description: str = Field(..., min_length=5, max_length=5000)
    proposed_type: Optional[RequirementType] = Field(None, description="Proposed requirement type")
    proposed_priority: Optional[RequirementPriority] = Field(None, description="Proposed requirement priority")
    proposed_status: Optional[RequirementStatus] = Field(None, description="Proposed requirement status")
    max_depth: Optional[int] = Field(3, ge=1, le=10, description="Max propagation depth limit")


class ImpactedRequirementItem(BaseModel):
    """Affected requirement specification detail."""

    requirement_id: UUID
    title: str
    type: RequirementType
    priority: RequirementPriority
    depth: int
    path: List[UUID]
    impact_reason: str


class WhatIfSimulationResponse(BaseModel):
    """Result of ephemeral What-If change simulation."""

    project_id: UUID
    target_requirement_id: Optional[UUID] = None
    change_type: ChangeType
    risk_score: float
    risk_level: str
    direct_affected_count: int
    transitive_affected_count: int
    direct_affected_requirements: List[ImpactedRequirementItem]
    transitive_affected_requirements: List[ImpactedRequirementItem]
    new_conflicts_triggered: List[Dict[str, Any]]
    conflicts_resolved: List[Dict[str, Any]]
    evidence_reasoning: List[str]
    is_ephemeral: bool = True


class ImpactReportResponse(BaseModel):
    """Persisted requirement impact report schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    requirement_id: UUID
    change_type: ChangeType
    risk_score: float
    risk_level: str
    direct_affected_count: int
    transitive_affected_count: int
    conflicts_count: int
    report_data_json: Dict[str, Any] = Field(..., alias="report_data")
    created_at: datetime
    updated_at: datetime


class ProjectRiskSummaryResponse(BaseModel):
    """Project-wide risk summary analytics."""

    project_id: UUID
    average_project_risk_score: float
    high_risk_requirements_count: int
    risk_level_breakdown: Dict[str, int]
    top_high_risk_requirements: List[Dict[str, Any]]
