"""
Sprint 1.9 — Project Memory Model

Stores per-project terminology, domain vocabulary, and AI conversation history.
Used by the Copilot to maintain context consistency across sessions.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProjectMemory(Base):
    """Per-project AI memory — terminology, domain vocabulary, session context."""

    __tablename__ = "project_memory"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Domain terminology: {"Login": "The act of authenticating a user...", ...}
    terminology: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)

    # Stakeholder personas: [{"role": "Customer", "description": "..."}, ...]
    personas: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)

    # Domain context set by the user/copilot
    domain_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project = relationship("Project", backref="memory", uselist=False)
