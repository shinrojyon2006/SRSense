"""
Requirement ORM model.

Represents software requirement specifications inside a project.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RequirementType(str, enum.Enum):
    """Available requirement types."""

    BUSINESS = "business"
    USER = "user"
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    SYSTEM = "system"


class RequirementPriority(str, enum.Enum):
    """Available requirement priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementStatus(str, enum.Enum):
    """Available requirement lifecycle statuses."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class Requirement(Base):
    """Requirement entity model."""

    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[RequirementType] = mapped_column(
        Enum(RequirementType, values_callable=lambda x: [e.value for e in x]),
        default=RequirementType.FUNCTIONAL,
        nullable=False,
        index=True,
    )
    priority: Mapped[RequirementPriority] = mapped_column(
        Enum(RequirementPriority, values_callable=lambda x: [e.value for e in x]),
        default=RequirementPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    status: Mapped[RequirementStatus] = mapped_column(
        Enum(RequirementStatus, values_callable=lambda x: [e.value for e in x]),
        default=RequirementStatus.DRAFT,
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="User Input", nullable=False)
    quality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    analysis_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Traceability Fields (Sprint 1.4)
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_section: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_req_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirements.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", backref="requirements")
    source_document = relationship("Document", backref="traceable_requirements")

    __table_args__ = (
        Index("ix_requirements_project_type", "project_id", "type"),
        Index("ix_requirements_project_priority", "project_id", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Requirement {self.title} ({self.type.value}) project={self.project_id}>"
