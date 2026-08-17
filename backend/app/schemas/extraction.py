"""
Requirement extraction, candidate classification, and batch acceptance Pydantic schemas.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
from app.schemas.requirement import RequirementResponse


class CandidateRequirement(BaseModel):
    """Structured candidate requirement extracted from an SRS document."""

    candidate_id: str = Field(..., description="Unique temporary candidate identifier")
    original_req_id: Optional[str] = Field(None, description="Original requirement ID if found in source text (e.g. FR-001)")
    title: str = Field(..., description="Extracted specification title")
    description: str = Field(..., description="Extracted specification description text")
    type: RequirementType = Field(default=RequirementType.FUNCTIONAL, description="Heuristically classified requirement type")
    priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Inferred or defaulted requirement priority")
    
    # Traceability Metadata
    source_document_id: UUID = Field(..., description="Source Document ID")
    source_section: str = Field(default="General", description="Source section or paragraph header")
    source_snippet: str = Field(..., description="Raw text snippet from document")
    location_label: Optional[str] = Field(None, description="Location label (Page X, Line Y)")
    
    # Duplicate Detection
    is_duplicate: bool = Field(default=False, description="Whether candidate matches an existing project requirement")
    duplicate_of_id: Optional[UUID] = Field(None, description="ID of existing matching requirement")
    similarity_score: float = Field(default=0.0, description="Token Jaccard similarity score (0.0 - 1.0)")


class ExtractionResponse(BaseModel):
    """Response containing extracted candidate requirements from a document."""

    document_id: UUID
    total_candidates: int
    candidates: List[CandidateRequirement]


class BatchAcceptItem(BaseModel):
    """Single candidate item selected for batch acceptance into project requirements."""

    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=5)
    type: RequirementType = Field(default=RequirementType.FUNCTIONAL)
    priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM)
    status: RequirementStatus = Field(default=RequirementStatus.APPROVED)
    
    # Traceability
    source_document_id: Optional[UUID] = None
    source_section: Optional[str] = None
    source_snippet: Optional[str] = None
    original_req_id: Optional[str] = None


class BatchAcceptRequest(BaseModel):
    """Batch acceptance payload."""

    items: List[BatchAcceptItem] = Field(..., min_items=1)


class BatchAcceptResponse(BaseModel):
    """Response returned after persisting accepted candidate requirements."""

    accepted_count: int
    created_requirements: List[RequirementResponse]
