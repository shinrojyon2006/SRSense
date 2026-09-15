"""
SQLAlchemy models for Sprint 2.3 Before/After Engineering Improvement Verification.
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
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.code_quality import CodeHealthStatus


class EvaluationResultClassification(str, enum.Enum):
    IMPROVED = "improved"
    UNCHANGED = "unchanged"
    REGRESSED = "regressed"
    PARTIALLY_IMPROVED = "partially_improved"
    UNDETERMINED = "undetermined"


class CodeImprovementEvaluation(Base):
    """Stores before/after engineering evaluation and audit records for code improvements."""

    __tablename__ = "code_improvement_evaluations"

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
    proposal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_improvement_proposals.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    before_report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_review_reports.id", ondelete="SET NULL"),
        nullable=True,
    )
    after_report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_review_reports.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Score Metrics & Health Status
    before_score = Column(Integer, nullable=False, default=0)
    after_score = Column(Integer, nullable=False, default=0)
    score_delta = Column(Integer, nullable=False, default=0)

    before_health = Column(
        SQLEnum(
            CodeHealthStatus,
            name="code_health_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=CodeHealthStatus.HEALTHY,
    )
    after_health = Column(
        SQLEnum(
            CodeHealthStatus,
            name="code_health_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=CodeHealthStatus.HEALTHY,
    )

    # Summaries & Findings Comparison
    before_summary = Column(JSON, nullable=False, default=dict)
    after_summary = Column(JSON, nullable=False, default=dict)
    category_scores = Column(JSON, nullable=False, default=dict)

    resolved_findings = Column(JSON, nullable=False, default=list)
    remaining_findings = Column(JSON, nullable=False, default=list)
    new_findings = Column(JSON, nullable=False, default=list)
    unchanged_findings = Column(JSON, nullable=False, default=list)

    # Requirement Compliance & Test Impact
    requirement_compliance_impact = Column(JSON, nullable=False, default=dict)
    test_impact = Column(JSON, nullable=False, default=dict)

    # Regression Detection & Result Classification
    regression_detected = Column(Boolean, nullable=False, default=False)
    regression_details = Column(JSON, nullable=False, default=list)

    result_classification = Column(
        SQLEnum(
            EvaluationResultClassification,
            name="evaluation_result_classification",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=EvaluationResultClassification.UNDETERMINED,
        index=True,
    )

    ai_explanation = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project")
    codebase = relationship("Codebase")
    proposal = relationship("CodeImprovementProposal", backref="evaluation")
    before_report = relationship("CodeReviewReport", foreign_keys=[before_report_id])
    after_report = relationship("CodeReviewReport", foreign_keys=[after_report_id])
