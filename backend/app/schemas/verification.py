"""
Requirement-to-Verification Compiler Pydantic Schemas — Sprint 1.8.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.verification import (
    TestCaseType,
    TestExecutionStatus,
    VerificationReadiness,
    VerificationStatus,
    VerificationType,
)


class UpdateTestCaseExecutionRequest(BaseModel):
    """Payload to update test case execution status."""

    execution_status: TestExecutionStatus


class TestCaseResponse(BaseModel):
    """Generated Test Case Schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    requirement_id: UUID
    verification_spec_id: Optional[UUID] = None
    test_type: TestCaseType
    title: str
    preconditions: Optional[str] = None
    steps: List[str] = Field(default_factory=list, validation_alias="steps_json")
    expected_result: str
    execution_status: TestExecutionStatus
    created_at: datetime
    updated_at: datetime


class VerificationSpecificationResponse(BaseModel):
    """Structured Verification Specification Schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    requirement_id: UUID
    metric: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[str] = None
    unit: Optional[str] = None
    population_sample: Optional[str] = None
    condition: Optional[str] = None
    expected_result: Optional[str] = None
    verification_type: VerificationType
    readiness_status: VerificationReadiness
    verification_status: VerificationStatus
    confidence_score: float
    pass_condition: Optional[str] = None
    missing_elements: List[str] = Field(default_factory=list, validation_alias="missing_elements_json")
    acceptance_criteria: List[Dict[str, Any]] = Field(default_factory=list, validation_alias="acceptance_criteria_json")
    test_cases: List[TestCaseResponse] = []
    created_at: datetime
    updated_at: datetime


class ProjectVerificationSummaryResponse(BaseModel):
    """Project-wide Verification & Coverage Summary Analytics."""

    project_id: UUID
    total_requirements_count: int
    verification_readiness_percentage: float
    test_generation_coverage_percentage: float
    actual_verification_coverage_percentage: float
    status_breakdown: Dict[str, int]
    readiness_breakdown: Dict[str, int]
    unverified_requirements_gaps: List[Dict[str, Any]]
