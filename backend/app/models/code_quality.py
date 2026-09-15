"""
SQLAlchemy ORM models for Sprint 2.1 Code Review & Code Quality Intelligence.
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
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class CodeHealthStatus(str, enum.Enum):
    HEALTHY = "healthy"
    NEEDS_ATTENTION = "needs_attention"
    AT_RISK = "at_risk"


class FindingCategory(str, enum.Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    COMPLIANCE = "compliance"
    QUALITY = "quality"


class FindingSeverity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class CodeReviewReport(Base):
    """Stores persistent, audited static code review scan reports."""

    __tablename__ = "code_review_reports"

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
    overall_score = Column(Integer, nullable=False, default=100)
    health_status = Column(
        SQLEnum(CodeHealthStatus, name="code_health_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CodeHealthStatus.HEALTHY,
    )
    summary = Column(Text, nullable=True)
    total_files_analyzed = Column(Integer, nullable=False, default=0)
    total_issues_count = Column(Integer, nullable=False, default=0)
    critical_count = Column(Integer, nullable=False, default=0)
    warning_count = Column(Integer, nullable=False, default=0)
    info_count = Column(Integer, nullable=False, default=0)
    category_counts = Column(JSON, nullable=False, default=dict)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", backref="code_review_reports")
    codebase = relationship("Codebase", backref="code_review_reports")
    findings = relationship(
        "CodeReviewFinding",
        back_populates="report",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CodeReviewFinding(Base):
    """Represents an individual code analysis issue or finding."""

    __tablename__ = "code_review_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_review_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    file_path = Column(String(1024), nullable=False, index=True)
    line_number = Column(Integer, nullable=True)
    category = Column(
        SQLEnum(FindingCategory, name="finding_category", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    severity = Column(
        SQLEnum(FindingSeverity, name="finding_severity", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    rule_id = Column(String(50), nullable=False, index=True)
    suggestion = Column(Text, nullable=False)
    ai_explanation = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    linked_requirement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requirements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    report = relationship("CodeReviewReport", back_populates="findings")
    file = relationship("CodeFile")
    linked_requirement = relationship("Requirement")


# Composite indexes for fast queries
Index("ix_code_findings_report_severity", CodeReviewFinding.report_id, CodeReviewFinding.severity)
Index("ix_code_findings_report_category", CodeReviewFinding.report_id, CodeReviewFinding.category)
