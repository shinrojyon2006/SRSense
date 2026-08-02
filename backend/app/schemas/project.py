"""
Pydantic schemas for Project request and response validation.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProjectStatusEnum(str, Enum):
    """Project status enum matching ORM definition."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectCreate(BaseModel):
    """Schema for creating a project."""

    title: str = Field(..., min_length=2, max_length=200, examples=["E-Commerce SRS Platform"])
    description: Optional[str] = Field(default="", max_length=2000)
    status: ProjectStatusEnum = Field(default=ProjectStatusEnum.ACTIVE)


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[ProjectStatusEnum] = None
    requirement_count: Optional[int] = Field(None, ge=0)


class ProjectResponse(BaseModel):
    """Schema for project API response payload."""

    id: uuid.UUID
    title: str
    description: Optional[str] = ""
    status: ProjectStatusEnum
    requirement_count: int
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
