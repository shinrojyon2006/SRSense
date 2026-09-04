"""
Sprint 1.9 — Engineering AI Copilot Schemas

Pydantic schemas for all Copilot API endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class ReviewMode(str, Enum):
    QA = "qa"
    SECURITY = "security"
    PERFORMANCE = "performance"
    PRODUCT = "product"
    ARCHITECTURE = "architecture"


class ConfidenceLevel(str, Enum):
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"
    UNCERTAIN = "UNCERTAIN"


class GapType(str, Enum):
    MISSING_NFR = "missing_nfr"
    MISSING_ERROR_HANDLING = "missing_error_handling"
    MISSING_SECURITY = "missing_security"
    MISSING_PERFORMANCE = "missing_performance"
    INCOMPLETE_USER_STORY = "incomplete_user_story"
    MISSING_ACCEPTANCE_CRITERIA = "missing_acceptance_criteria"


# ── Project Copilot Chat ───────────────────────────────────────────────────────

class CopilotChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context_requirement_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Specific requirement IDs to focus on. If None, uses all project requirements.",
    )


class CopilotChatResponse(BaseModel):
    answer: str
    confidence: ConfidenceLevel
    evidence: List[str]
    referenced_requirement_ids: List[UUID]
    caveats: Optional[str] = None


# ── Requirement Doctor ─────────────────────────────────────────────────────────

class DoctorIssue(BaseModel):
    severity: str  # "critical" | "warning" | "info"
    category: str
    description: str
    suggestion: str


class RequirementDoctorResponse(BaseModel):
    requirement_id: UUID
    requirement_title: str
    overall_health: str  # "healthy" | "needs_attention" | "critical"
    health_score: int  # 0-100
    issues: List[DoctorIssue]
    improvement_hint: Optional[str] = None
    confidence: ConfidenceLevel


# ── AI Review Modes ───────────────────────────────────────────────────────────

class ReviewFinding(BaseModel):
    requirement_id: Optional[UUID] = None
    requirement_title: Optional[str] = None
    severity: str  # "critical" | "warning" | "info"
    finding: str
    recommendation: str
    confidence: ConfidenceLevel


class AIReviewResponse(BaseModel):
    project_id: UUID
    mode: ReviewMode
    total_requirements_reviewed: int
    findings: List[ReviewFinding]
    summary: str
    timestamp: datetime


# ── AI Referee ────────────────────────────────────────────────────────────────

class RefereeVote(BaseModel):
    choice: str  # "accept" | "reject" | "defer" | "modify"
    reasoning: str
    confidence: ConfidenceLevel
    risk_if_accepted: Optional[str] = None
    risk_if_rejected: Optional[str] = None


class AIRefereeResponse(BaseModel):
    suggestion_id: UUID
    referee_vote: RefereeVote
    alternative_suggestion: Optional[str] = None


# ── AI Gap Finder ─────────────────────────────────────────────────────────────

class GapSuggestion(BaseModel):
    gap_type: GapType
    title: str
    description: str
    rationale: str
    confidence: ConfidenceLevel
    related_requirement_ids: List[UUID]


class GapFinderResponse(BaseModel):
    project_id: UUID
    total_gaps_found: int
    gaps: List[GapSuggestion]
    coverage_score: int  # 0-100 (higher = better coverage)
    summary: str


# ── Scenario Generator ────────────────────────────────────────────────────────

class TestScenario(BaseModel):
    scenario_type: str  # "normal" | "failure" | "boundary" | "edge"
    title: str
    given: str
    when: str
    then: str
    priority: str  # "high" | "medium" | "low"
    confidence: ConfidenceLevel


class ScenarioGeneratorResponse(BaseModel):
    requirement_id: UUID
    requirement_title: str
    scenarios: List[TestScenario] = []
    total_scenarios: int = 0
    status: str = "success"  # "success" | "insufficient_information"
    insufficient_info_reason: Optional[str] = None
    missing_information: Optional[List[str]] = None
    clarification_questions: Optional[List[str]] = None


# ── Traceability Assistant ────────────────────────────────────────────────────

class TraceabilityLink(BaseModel):
    from_requirement_id: UUID
    from_title: str
    to_requirement_id: UUID
    to_title: str
    relationship_type: str
    explanation: str
    confidence: ConfidenceLevel


class TraceabilityResponse(BaseModel):
    project_id: UUID
    total_links: int
    links: List[TraceabilityLink]
    orphaned_requirement_ids: List[UUID]
    coverage_percentage: float
    summary: str


# ── Project Memory ────────────────────────────────────────────────────────────

class ProjectMemoryUpdate(BaseModel):
    terminology: Optional[Dict[str, str]] = None
    personas: Optional[List[Dict[str, str]]] = None
    domain_context: Optional[str] = None


class ProjectMemoryResponse(BaseModel):
    project_id: UUID
    terminology: Dict[str, str] = Field(default_factory=dict)
    personas: List[Dict[str, str]] = Field(default_factory=list)
    domain_context: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
