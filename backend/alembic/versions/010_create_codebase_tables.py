"""Create codebase intelligence tables (codebases, code_files, code_symbols, code_dependencies, requirement_code_links)

Revision ID: 010
Revises: 009
Create Date: 2026-08-25 03:27:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM as PG_ENUM

# revision identifiers
revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums idempotently
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE codebase_status AS ENUM ('PENDING', 'INDEXING', 'INDEXED', 'FAILED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE code_symbol_type AS ENUM ('CLASS', 'INTERFACE', 'STRUCT', 'FUNCTION', 'METHOD', 'ENDPOINT', 'TABLE', 'VIEW', 'PROCEDURE');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE code_dependency_type AS ENUM ('IMPORTS', 'INCLUDES', 'CALLS', 'EXTENDS');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE requirement_code_link_type AS ENUM ('EXPLICIT_MANUAL', 'REFERENCED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    codebase_status_type = PG_ENUM("PENDING", "INDEXING", "INDEXED", "FAILED", name="codebase_status", create_type=False)
    code_symbol_type = PG_ENUM("CLASS", "INTERFACE", "STRUCT", "FUNCTION", "METHOD", "ENDPOINT", "TABLE", "VIEW", "PROCEDURE", name="code_symbol_type", create_type=False)
    code_dependency_type = PG_ENUM("IMPORTS", "INCLUDES", "CALLS", "EXTENDS", name="code_dependency_type", create_type=False)
    requirement_code_link_type = PG_ENUM("EXPLICIT_MANUAL", "REFERENCED", name="requirement_code_link_type", create_type=False)

    # 2. Table: codebases
    op.create_table(
        "codebases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("repo_name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="zip_upload"),
        sa.Column("status", codebase_status_type, nullable=False, server_default="PENDING"),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_lines", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_classes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_functions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("languages_summary", JSON, nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 3. Table: code_files
    op.create_table(
        "code_files",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "codebase_id",
            UUID(as_uuid=True),
            sa.ForeignKey("codebases.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("path", sa.String(1024), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("language", sa.String(50), nullable=False, server_default="Unknown / Unsupported"),
        sa.Column("confidence", sa.String(20), nullable=False, server_default="Unknown"),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("line_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imports", JSON, nullable=False, server_default="[]"),
        sa.Column("exports", JSON, nullable=False, server_default="[]"),
        sa.Column("endpoints", JSON, nullable=False, server_default="[]"),
        sa.Column("db_interactions", JSON, nullable=False, server_default="[]"),
        sa.Column("metadata_json", JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_code_files_project_path", "code_files", ["project_id", "path"])

    # 4. Table: code_symbols
    op.create_table(
        "code_symbols",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "codebase_id",
            UUID(as_uuid=True),
            sa.ForeignKey("codebases.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "file_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_files.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("symbol_name", sa.String(255), nullable=False, index=True),
        sa.Column(
            "symbol_type",
            code_symbol_type,
            nullable=False,
            server_default="FUNCTION",
        ),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("signature", sa.Text(), nullable=True),
        sa.Column("docstring", sa.Text(), nullable=True),
        sa.Column("parent_symbol_name", sa.String(255), nullable=True),
        sa.Column("metadata_json", JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_code_symbols_project_name", "code_symbols", ["project_id", "symbol_name"])

    # 5. Table: code_dependencies
    op.create_table(
        "code_dependencies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "codebase_id",
            UUID(as_uuid=True),
            sa.ForeignKey("codebases.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "source_file_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_files.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "target_file_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_files.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("target_module", sa.String(512), nullable=False),
        sa.Column(
            "dependency_type",
            code_dependency_type,
            nullable=False,
            server_default="IMPORTS",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 6. Table: requirement_code_links
    op.create_table(
        "requirement_code_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "requirement_id",
            UUID(as_uuid=True),
            sa.ForeignKey("requirements.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "file_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_files.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "symbol_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_symbols.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "link_type",
            requirement_code_link_type,
            nullable=False,
            server_default="EXPLICIT_MANUAL",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("requirement_code_links")
    op.drop_table("code_dependencies")
    op.drop_index("ix_code_symbols_project_name", table_name="code_symbols")
    op.drop_table("code_symbols")
    op.drop_index("ix_code_files_project_path", table_name="code_files")
    op.drop_table("code_files")
    op.drop_table("codebases")

    sa.Enum(name="requirement_code_link_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="code_dependency_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="code_symbol_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="codebase_status").drop(op.get_bind(), checkfirst=True)
