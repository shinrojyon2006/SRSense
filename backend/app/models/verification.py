"""
Verification Specification and Test Case ORM models — Sprint 1.8 Requirement-to-Verification Compiler.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class VerificationType(str, enum.Enum):
    """Verification classification type."""

    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    RELIABILITY = "reliability"
    AVAILABILITY = "availability"
    DATA_VALIDATION = "data_validation"
    BOUNDARY_CONSTRAINT = "boundary_constraint"
    INTEGRATION = "integration"


class VerificationReadiness(str, enum.Enum):
    """Quality readiness classification."""

    EXPLICIT_MEASURABLE = "explicit_measurable"
    CONFIDENTLY_INFERRED = "confidently_inferred"
    VERIFICATION_GAP = "verification_gap"


class VerificationStatus(str, enum.Enum):
    """Requirement Verification Status — distinguishes specification readiness from actual test execution evidence."""

    UNVERIFIED = "unverified"
    PARTIALLY_READY = "partially_ready"
    READY_FOR_VERIFICATION = "ready_for_verification"
    VERIFIED = "verified"


class TestCaseType(str, enum.Enum):
    """Generated test case category."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestExecutionStatus(str, enum.Enum):
    """Test case execution state."""

    UNTESTED = "untested"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class VerificationSpecification(Base):
    """Structured Verification Specification for a Requirement."""

    __tablename__ = "verification_specifications"

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
        unique=True,
        index=True,
    )

    metric: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    operator: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    threshold: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    population_sample: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    condition: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    expected_result: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    verification_type: Mapped[VerificationType] = mapped_column(
        Enum(VerificationType, values_callable=lambda x: [e.value for e in x]),
        default=VerificationType.FUNCTIONAL,
        nullable=False,
    )

    readiness_status: Mapped[VerificationReadiness] = mapped_column(
        Enum(VerificationReadiness, values_callable=lambda x: [e.value for e in x]),
        default=VerificationReadiness.EXPLICIT_MEASURABLE,
        nullable=False,
    )

    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, values_callable=lambda x: [e.value for e in x]),
        default=VerificationStatus.UNVERIFIED,
        nullable=False,
    )

    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    pass_condition: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    missing_elements_json: Mapped[dict] = mapped_column("missing_elements", JSON, nullable=False, default=list)
    acceptance_criteria_json: Mapped[dict] = mapped_column("acceptance_criteria", JSON, nullable=False, default=list)

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
    project = relationship("Project", backref="verification_specs")
    requirement = relationship("Requirement", backref="verification_spec")
    test_cases = relationship("TestCase", backref="verification_spec", cascade="all, delete-orphan")

    @property
    def missing_elements(self) -> list:
        return self.missing_elements_json if isinstance(self.missing_elements_json, list) else []

    @property
    def acceptance_criteria(self) -> list:
        return self.acceptance_criteria_json if isinstance(self.acceptance_criteria_json, list) else []

    def __repr__(self) -> str:
        return f"<VerificationSpecification {self.requirement_id} readiness={self.readiness_status} status={self.verification_status}>"


class TestCase(Base):
    """Generated Test Case linked to a Requirement and Verification Specification."""

    __tablename__ = "test_cases"

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
    verification_spec_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verification_specifications.id", ondelete="CASCADE"),
        nullable=True,
    )

    test_type: Mapped[TestCaseType] = mapped_column(
        Enum(TestCaseType, values_callable=lambda x: [e.value for e in x]),
        default=TestCaseType.POSITIVE,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    preconditions: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    steps_json: Mapped[dict] = mapped_column("steps", JSON, nullable=False, default=list)
    expected_result: Mapped[str] = mapped_column(String(500), nullable=False)

    execution_status: Mapped[TestExecutionStatus] = mapped_column(
        Enum(TestExecutionStatus, values_callable=lambda x: [e.value for e in x]),
        default=TestExecutionStatus.UNTESTED,
        nullable=False,
    )

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
    project = relationship("Project", backref="test_cases")
    requirement = relationship("Requirement", backref="test_cases")

    @property
    def steps(self) -> list:
        return self.steps_json if isinstance(self.steps_json, list) else []

    def __repr__(self) -> str:
        return f"<TestCase {self.title} status={self.execution_status}>"
