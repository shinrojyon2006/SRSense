"""
Pydantic DTO schemas for Sprint 2.4 Traceability.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CodeTestArtifactResponse(BaseModel):
    """Response DTO for discovered test artifact."""

    id: UUID
    project_id: UUID
    codebase_id: UUID
    file_path: str
    test_name: str
    test_framework: Optional[str] = None
    test_type: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    status: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequirementTestLinkResponse(BaseModel):
    """Response DTO for Requirement-to-Test link."""

    id: UUID
    project_id: UUID
    requirement_id: UUID
    test_artifact_id: UUID
    relationship_type: str
    confidence: float
    evidence: Dict[str, Any]
    verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequirementTraceabilityItemResponse(BaseModel):
    """Response DTO for per-requirement traceability state."""

    requirement_id: UUID
    original_req_id: Optional[str] = None
    title: str
    requirement_type: str
    has_code: bool
    has_test: bool
    status: str  # FULLY_TRACED, IMPLEMENTED_NOT_TESTED, TESTED_NOT_LINKED, NO_IMPLEMENTATION, PARTIALLY_TRACED, UNDETERMINED
    confidence: float
    linked_code_files: List[str]
    linked_test_names: List[str]
    evidence: List[Dict[str, Any]]
    risk: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TraceabilitySummaryResponse(BaseModel):
    """Overall project-level traceability metrics and score summary."""

    total_requirements: int
    requirements_with_code: int
    requirements_without_code: int
    requirements_with_tests: int
    requirements_without_tests: int
    fully_traced_count: int
    partially_traced_count: int
    untraced_count: int
    code_coverage_pct: float
    test_coverage_pct: float
    full_traceability_pct: float
    traceability_score: int
    health_status: str


class TraceabilityGapItem(BaseModel):
    """Represents a specific missing implementation or test coverage gap."""

    requirement_id: UUID
    original_req_id: Optional[str] = None
    title: str
    gap_type: str  # NO_IMPLEMENTATION, IMPLEMENTED_NOT_TESTED, WEAK_TRACEABILITY, MISSING_SLA_TEST, MISSING_SECURITY_TEST
    description: str
    severity: str
    recommendation: str


class TraceabilityGapsListResponse(BaseModel):
    """List of all identified traceability gaps in the project."""

    total_gaps: int
    gaps: List[TraceabilityGapItem]


class TestProposalRequest(BaseModel):
    """Payload to request AI test proposal generation."""

    requirement_id: UUID


class TestProposalResponse(BaseModel):
    """Response DTO for AI test suggestion proposal."""

    requirement_id: UUID
    requirement_title: str
    test_title: str
    purpose: str
    test_type: str
    suggested_framework: str
    preconditions: List[str]
    inputs: List[str]
    steps: List[str]
    expected_result: str
    validated_behavior: str
    edge_cases: List[str]
    code_snippet_proposal: str
    confidence: float
    status: str  # PROPOSAL_GENERATED, INSUFFICIENT_CONTEXT
    missing_context_explanation: Optional[str] = None


class CreateTestLinkRequest(BaseModel):
    """Request payload to manually link a requirement to a test artifact."""

    requirement_id: UUID
    test_artifact_id: UUID
