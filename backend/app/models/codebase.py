"""
SQLAlchemy models for Sprint 2.0 Code Intelligence.

Defines schemas for repositories, files, AST symbols, dependencies,
and Requirement-to-Code links.
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


class CodebaseStatus(str, enum.Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class SymbolType(str, enum.Enum):
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    FUNCTION = "function"
    METHOD = "method"
    ENDPOINT = "endpoint"
    TABLE = "table"
    VIEW = "view"
    PROCEDURE = "procedure"


class DependencyType(str, enum.Enum):
    IMPORTS = "imports"
    INCLUDES = "includes"
    CALLS = "calls"
    EXTENDS = "extends"


class LinkType(str, enum.Enum):
    EXPLICIT_MANUAL = "explicit_manual"
    REFERENCED = "referenced"


class Codebase(Base):
    """Represents an imported source code repository for a project."""

    __tablename__ = "codebases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repo_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False, default="zip_upload")
    status = Column(
        SQLEnum(CodebaseStatus, name="codebase_status"),
        nullable=False,
        default=CodebaseStatus.PENDING,
    )
    total_files = Column(Integer, nullable=False, default=0)
    total_lines = Column(Integer, nullable=False, default=0)
    total_classes = Column(Integer, nullable=False, default=0)
    total_functions = Column(Integer, nullable=False, default=0)
    languages_summary = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)

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
    project = relationship("Project", backref="codebases")
    files = relationship(
        "CodeFile",
        back_populates="codebase",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    symbols = relationship(
        "CodeSymbol",
        back_populates="codebase",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    dependencies = relationship(
        "CodeDependency",
        back_populates="codebase",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CodeFile(Base):
    """Represents a single analyzed file in a codebase."""

    __tablename__ = "code_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codebase_id = Column(
        UUID(as_uuid=True),
        ForeignKey("codebases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    path = Column(String(1024), nullable=False)
    filename = Column(String(255), nullable=False)
    language = Column(String(50), nullable=False, default="Unknown / Unsupported")
    confidence = Column(String(20), nullable=False, default="Unknown")
    size_bytes = Column(Integer, nullable=False, default=0)
    line_count = Column(Integer, nullable=False, default=0)
    
    # Structured AST extractions
    imports = Column(JSON, nullable=False, default=list)
    exports = Column(JSON, nullable=False, default=list)
    endpoints = Column(JSON, nullable=False, default=list)
    db_interactions = Column(JSON, nullable=False, default=list)
    metadata_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    codebase = relationship("Codebase", back_populates="files")
    symbols = relationship(
        "CodeSymbol",
        back_populates="file",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CodeSymbol(Base):
    """Represents an extracted code construct (class, function, method, endpoint, table)."""

    __tablename__ = "code_symbols"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codebase_id = Column(
        UUID(as_uuid=True),
        ForeignKey("codebases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol_name = Column(String(255), nullable=False, index=True)
    symbol_type = Column(
        SQLEnum(SymbolType, name="code_symbol_type"),
        nullable=False,
        default=SymbolType.FUNCTION,
    )
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    signature = Column(Text, nullable=True)
    docstring = Column(Text, nullable=True)
    parent_symbol_name = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    codebase = relationship("Codebase", back_populates="symbols")
    file = relationship("CodeFile", back_populates="symbols")


class CodeDependency(Base):
    """Represents a discovered dependency or import between files/modules."""

    __tablename__ = "code_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codebase_id = Column(
        UUID(as_uuid=True),
        ForeignKey("codebases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_module = Column(String(512), nullable=False)
    dependency_type = Column(
        SQLEnum(DependencyType, name="code_dependency_type"),
        nullable=False,
        default=DependencyType.IMPORTS,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    codebase = relationship("Codebase", back_populates="dependencies")
    source_file = relationship("CodeFile", foreign_keys=[source_file_id])
    target_file = relationship("CodeFile", foreign_keys=[target_file_id])


class RequirementCodeLink(Base):
    """Sprint 2.0 Mapping Foundation: Links a requirement to a code artifact."""

    __tablename__ = "requirement_code_links"

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
    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol_id = Column(
        UUID(as_uuid=True),
        ForeignKey("code_symbols.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    link_type = Column(
        SQLEnum(LinkType, name="requirement_code_link_type"),
        nullable=False,
        default=LinkType.EXPLICIT_MANUAL,
    )
    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    requirement = relationship("Requirement", backref="code_links")
    file = relationship("CodeFile")
    symbol = relationship("CodeSymbol")


# Composite indexes for fast symbol & path querying
Index("ix_code_files_project_path", CodeFile.project_id, CodeFile.path)
Index("ix_code_symbols_project_name", CodeSymbol.project_id, CodeSymbol.symbol_name)
