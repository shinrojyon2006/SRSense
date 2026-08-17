"""
Requirement Suggestion ORM model.

Represents automatically discovered conflict and dependency suggestions
awaiting human-in-the-loop review before conversion into Knowledge Graph edges.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.relationship import RelationshipType


class SuggestionStatus(str, enum.Enum):
    """Lifecycle status for an intelligence suggestion."""

    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISMISSED = "dismissed"


class RequirementSuggestion(Base):
    """Requirement Suggestion entity model."""

    __tablename__ = "requirement_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    status: Mapped[SuggestionStatus] = mapped_column(
        Enum(SuggestionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SuggestionStatus.SUGGESTED,
        nullable=False,
        index=True,
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.75)
    conflict_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    evidence_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Material change tracking (Mandatory Adjustment 1)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    target_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    detector_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    dismissal_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", backref="suggestions")
    source_requirement = relationship("Requirement", foreign_keys=[source_id], backref="outgoing_suggestions")
    target_requirement = relationship("Requirement", foreign_keys=[target_id], backref="incoming_suggestions")

    __table_args__ = (
        CheckConstraint("source_id != target_id", name="ck_requirement_suggestions_no_self_loop"),
        UniqueConstraint("project_id", "source_id", "target_id", "relationship_type", name="uq_requirement_suggestions_edge"),
        Index("ix_requirement_suggestions_project_status", "project_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<RequirementSuggestion {self.relationship_type.value} ({self.source_id} -> {self.target_id}) [{self.status.value}]>"
