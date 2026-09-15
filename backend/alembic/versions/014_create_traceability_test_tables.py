"""Create traceability test tables (code_test_artifacts, requirement_test_links)

Revision ID: 014
Revises: 013
Create Date: 2026-09-05 01:19:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers
revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: code_test_artifacts
    op.create_table(
        "code_test_artifacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "codebase_id",
            UUID(as_uuid=True),
            sa.ForeignKey("codebases.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("file_path", sa.String(1024), nullable=False, index=True),
        sa.Column("test_name", sa.String(255), nullable=False, index=True),
        sa.Column("test_framework", sa.String(50), nullable=True),
        sa.Column("test_type", sa.String(50), nullable=False, server_default="UNIT"),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(50), nullable=True, server_default="DISCOVERED"),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 2. Table: requirement_test_links
    op.create_table(
        "requirement_test_links",
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
            "test_artifact_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_test_artifacts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("relationship_type", sa.String(50), nullable=False, server_default="DIRECT"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("evidence", JSON, nullable=False, server_default="{}"),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_req_test_links_project_req", "requirement_test_links", ["project_id", "requirement_id"])


def downgrade() -> None:
    op.drop_index("ix_req_test_links_project_req", table_name="requirement_test_links")
    op.drop_table("requirement_test_links")
    op.drop_table("code_test_artifacts")
