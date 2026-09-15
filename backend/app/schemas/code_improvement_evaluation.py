"""
Pydantic DTO schemas for Sprint 2.3 Before/After Code Improvement Evaluation.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.models.code_improvement_evaluation import EvaluationResultClassification


class CodeImprovementEvaluationResponse(BaseModel):
    """Response payload representing an evaluated code improvement proposal."""

    id: UUID
    project_id: UUID
    codebase_id: UUID
    proposal_id: UUID
    before_report_id: Optional[UUID] = None
    after_report_id: Optional[UUID] = None

    before_score: int
    after_score: int
    score_delta: int

    before_health: str
    after_health: str

    before_summary: Dict[str, Any]
    after_summary: Dict[str, Any]
    category_scores: Dict[str, Any]

    resolved_findings: List[Dict[str, Any]]
    remaining_findings: List[Dict[str, Any]]
    new_findings: List[Dict[str, Any]]
    unchanged_findings: List[Dict[str, Any]]

    requirement_compliance_impact: Dict[str, Any]
    test_impact: Dict[str, Any]

    regression_detected: bool
    regression_details: List[str]

    result_classification: EvaluationResultClassification
    ai_explanation: Optional[str] = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
