"""
SQLAlchemy models for Sprint 2.2 AI Code Improvement.

Defines schemas for AI-proposed code refactorings, human review states,
unified diffs, and requirement-grounded impact analysis.
"""

from datetime import datetime, timezone
import enum
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class ImprovementStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"
    STALE = "stale"


class CodeImprovementProposal(Base):
    """Represents a reviewable AI-generated code improvement proposal."""

    __tablename__ = "code_improvement_proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codebase_id = Column(
        UUID(as_uuid=True),
        ForeignKey("codebases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    finding_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_review_findings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    linked_requirement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requirements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    rule_id = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    problem_summary = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)

    # Code Artifacts & Patch
    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_files.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_path = Column(String(1024), nullable=False)
    current_code = Column(Text, nullable=False)
    proposed_code = Column(Text, nullable=False)
    patch_diff = Column(Text, nullable=False)

    # Impact Analysis & Test Considerations
    affected_files = Column(JSON, nullable=False, default=list)
    affected_requirements = Column(JSON, nullable=False, default=list)
    affected_tests = Column(JSON, nullable=False, default=list)
    risks = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=85.0)
    uncertainty = Column(Text, nullable=True)

    status = Column(
        SQLEnum(
            ImprovementStatus,
            name="improvement_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ImprovementStatus.PROPOSED,
        index=True,
    )
    error_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", backref="code_improvements")
    codebase = relationship("Codebase", backref="code_improvements")
    finding = relationship("CodeReviewFinding", backref="improvements")
    requirement = relationship("Requirement", backref="code_improvements")
    file = relationship("CodeFile")
