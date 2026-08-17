"""
Requirement Relationship ORM model.

Represents directed and symmetric graph edges between requirement specifications inside a project.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RelationshipType(str, enum.Enum):
    """Available graph relationship types."""

    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    DERIVED_FROM = "derived_from"
    VERIFIED_BY = "verified_by"


class RequirementRelationship(Base):
    """Requirement Relationship entity model (Graph Edge)."""

    __tablename__ = "requirement_relationships"

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
    type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

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
    project = relationship("Project", backref="relationships")
    source_requirement = relationship("Requirement", foreign_keys=[source_id], backref="outgoing_relationships")
    target_requirement = relationship("Requirement", foreign_keys=[target_id], backref="incoming_relationships")

    @property
    def edge_metadata(self) -> Optional[dict]:
        """Accessor for JSON metadata avoiding SQLAlchemy Base.metadata name collision."""
        return self.metadata_json

    __table_args__ = (
        CheckConstraint("source_id != target_id", name="ck_requirement_relationships_no_self_loop"),
        UniqueConstraint("project_id", "source_id", "target_id", "type", name="uq_requirement_relationships_edge"),
        Index("ix_requirement_relationships_project_source", "project_id", "source_id", "type"),
        Index("ix_requirement_relationships_project_target", "project_id", "target_id", "type"),
    )

    def __repr__(self) -> str:
        return f"<RequirementRelationship {self.type.value} ({self.source_id} -> {self.target_id})>"
