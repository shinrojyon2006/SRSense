"""
Pydantic schemas for Requirement request and response validation.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class RequirementTypeEnum(str, Enum):
    """Requirement type enum matching ORM definition."""

    BUSINESS = "business"
    USER = "user"
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    SYSTEM = "system"


class RequirementPriorityEnum(str, Enum):
    """Requirement priority enum matching ORM definition."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementStatusEnum(str, Enum):
    """Requirement status enum matching ORM definition."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class RequirementCreate(BaseModel):
    """Schema for creating a requirement."""

    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=5, max_length=5000)
    type: RequirementTypeEnum = Field(default=RequirementTypeEnum.FUNCTIONAL)
    priority: RequirementPriorityEnum = Field(default=RequirementPriorityEnum.MEDIUM)
    status: RequirementStatusEnum = Field(default=RequirementStatusEnum.DRAFT)
    version: Optional[str] = Field(default="1.0", max_length=20)
    source: Optional[str] = Field(default="User Input", max_length=100)
    parent_id: Optional[uuid.UUID] = None


class RequirementUpdate(BaseModel):
    """Schema for updating an existing requirement."""

    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=5, max_length=5000)
    type: Optional[RequirementTypeEnum] = None
    priority: Optional[RequirementPriorityEnum] = None
    status: Optional[RequirementStatusEnum] = None
    version: Optional[str] = Field(None, max_length=20)
    source: Optional[str] = Field(None, max_length=100)
    quality_score: Optional[int] = Field(None, ge=0, le=100)
    analysis_result: Optional[Dict[str, Any]] = None
    parent_id: Optional[uuid.UUID] = None


class RequirementResponse(BaseModel):
    """Schema for requirement API response payload."""

    id: uuid.UUID
    title: str
    description: str
    type: RequirementTypeEnum
    priority: RequirementPriorityEnum
    status: RequirementStatusEnum
    version: str
    source: str
    quality_score: Optional[int] = None
    analysis_result: Optional[Dict[str, Any]] = None
    project_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
