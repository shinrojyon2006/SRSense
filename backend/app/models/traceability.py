"""
SQLAlchemy models for Sprint 2.4 Requirements -> Code -> Tests Traceability.
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
    JSON,
    Float,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class TestType(str, enum.Enum):
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    E2E = "E2E"
    UNKNOWN = "UNKNOWN"


class TestRelationshipType(str, enum.Enum):
    DIRECT = "DIRECT"
    INFERRED = "INFERRED"
    AI_PROPOSED = "AI_PROPOSED"


class CodeTestArtifact(Base):
    """Represents a discovered or registered test artifact in the codebase."""

    __tablename__ = "code_test_artifacts"

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

    file_path = Column(String(1024), nullable=False, index=True)
    test_name = Column(String(255), nullable=False, index=True)
    test_framework = Column(String(50), nullable=True)  # pytest, unittest, jest, vitest, mocha, junit, gtest
    test_type = Column(String(50), nullable=False, default=TestType.UNIT.value)

    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    status = Column(String(50), nullable=True, default="DISCOVERED")
    content_hash = Column(String(64), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project")
    codebase = relationship("Codebase")
    test_links = relationship(
        "RequirementTestLink",
        back_populates="test_artifact",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RequirementTestLink(Base):
    """Represents a link connecting a requirement to a test artifact."""

    __tablename__ = "requirement_test_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requirement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_artifact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_test_artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    relationship_type = Column(
        String(50),
        nullable=False,
        default=TestRelationshipType.DIRECT.value,
    )
    confidence = Column(Float, nullable=False, default=1.0)
    evidence = Column(JSON, nullable=False, default=dict)
    verified = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project")
    requirement = relationship("Requirement", backref="test_links")
    test_artifact = relationship("CodeTestArtifact", back_populates="test_links")


# Composite Index for link queries
Index(
    "ix_req_test_links_project_req",
    RequirementTestLink.project_id,
    RequirementTestLink.requirement_id,
)
