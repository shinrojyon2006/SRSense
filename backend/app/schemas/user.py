"""
Pydantic schemas for User-related request/response validation.

These schemas enforce type safety and validation at the API boundary.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(str, Enum):
    """Available user roles (mirrors ORM enum)."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    ANALYST = "analyst"


# ── Request Schemas ──────────────────────────────────────────


class UserCreate(BaseModel):
    """Schema for user registration."""

    name: str = Field(..., min_length=2, max_length=100, examples=["Jane Doe"])
    email: EmailStr = Field(..., examples=["jane@srsense.ai"])
    password: str = Field(..., min_length=8, max_length=128)
    password_confirmation: str = Field(..., min_length=8, max_length=128)
    role: UserRole = Field(default=UserRole.DEVELOPER)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("password_confirmation")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        password = info.data.get("password")
        if password and v != password:
            raise ValueError("Passwords do not match")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., examples=["jane@srsense.ai"])
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    """Schema for requesting a new access token using a refresh token."""

    refresh_token: str = Field(..., min_length=1, description="Opaque refresh token")


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None


# ── Response Schemas ─────────────────────────────────────────


class UserResponse(BaseModel):
    """Schema for user data returned to clients."""

    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT access + refresh token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
