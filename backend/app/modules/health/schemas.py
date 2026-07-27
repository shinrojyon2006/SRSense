"""
Health Module Pydantic Schemas.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for system health response."""

    status: str = Field(..., example="healthy")
    version: str = Field(..., example="1.0.0")
    database: str = Field(..., example="connected")
