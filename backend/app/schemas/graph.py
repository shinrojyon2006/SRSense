"""
Requirement Knowledge Graph Pydantic schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.relationship import RelationshipType
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType


class RelationshipCreateRequest(BaseModel):
    """Payload to create a graph relationship edge between two requirements."""

    source_id: UUID = Field(..., description="Source requirement UUID")
    target_id: UUID = Field(..., description="Target requirement UUID")
    type: RelationshipType = Field(..., description="Relationship edge type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional relationship metadata")


class RelationshipResponse(BaseModel):
    """Graph relationship edge response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    source_id: UUID
    target_id: UUID
    type: RelationshipType
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="edge_metadata")
    created_at: datetime
    updated_at: datetime


class GraphNode(BaseModel):
    """Graph Node DTO schema."""

    id: UUID
    title: str
    type: RequirementType
    priority: RequirementPriority
    status: RequirementStatus


class GraphEdge(BaseModel):
    """Graph Edge DTO schema."""

    id: UUID
    source: UUID
    target: UUID
    type: RelationshipType


class ProjectGraphResponse(BaseModel):
    """Complete project knowledge graph response schema."""

    project_id: UUID
    total_nodes: int
    total_edges: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class RequirementRelationshipsResponse(BaseModel):
    """Relationships summary for a specific requirement."""

    requirement_id: UUID
    outgoing: List[RelationshipResponse]
    incoming: List[RelationshipResponse]
    conflicts: List[RelationshipResponse]


class DependencyChainResponse(BaseModel):
    """Dependency tree and impact analysis response schema."""

    root_requirement_id: UUID
    upstream_dependencies: List[RelationshipResponse]
    impacted_downstream: List[RelationshipResponse]


class SuggestedRelationshipItem(BaseModel):
    """Automatically discovered requirement relationship suggestion."""

    source_id: UUID
    target_id: UUID
    type: RelationshipType
    reason: str
    confidence_score: float


class SuggestRelationshipsResponse(BaseModel):
    """Response containing automatically discovered relationship suggestions."""

    project_id: UUID
    total_suggestions: int
    suggestions: List[SuggestedRelationshipItem]
