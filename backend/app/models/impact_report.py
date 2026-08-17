"""
Requirement Impact Report ORM model.

Represents persisted formal change impact analysis reports for requirements.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ChangeType(str, enum.Enum):
    """Change type classification."""

    COSMETIC = "cosmetic"
    METADATA = "metadata"
    BEHAVIORAL = "behavioral"


class RequirementImpactReport(Base):
    """Requirement Impact Report entity model."""

    __tablename__ = "requirement_impact_reports"

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
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    change_type: Mapped[ChangeType] = mapped_column(
        Enum(ChangeType, values_callable=lambda x: [e.value for e in x]),
        default=ChangeType.BEHAVIORAL,
        nullable=False,
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    direct_affected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transitive_affected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflicts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_data_json: Mapped[dict] = mapped_column("report_data", JSON, nullable=False)

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
    project = relationship("Project", backref="impact_reports")
    requirement = relationship("Requirement", backref="impact_reports")

    @property
    def report_data(self) -> dict:
        """Accessor for JSON report data avoiding name collisions."""
        return self.report_data_json

    __table_args__ = (
        Index("ix_requirement_impact_reports_project_req", "project_id", "requirement_id"),
    )

    def __repr__(self) -> str:
        return f"<RequirementImpactReport {self.requirement_id} risk={self.risk_score} ({self.risk_level})>"
