"""Create code improvement proposals table (code_improvement_proposals)

Revision ID: 012
Revises: 011
Create Date: 2026-09-05 00:50:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM as PG_ENUM

# revision identifiers
revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enum idempotently
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE improvement_status AS ENUM ('proposed', 'approved', 'rejected', 'applied', 'failed', 'stale');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    improvement_status_type = PG_ENUM(
        "proposed", "approved", "rejected", "applied", "failed", "stale",
        name="improvement_status", create_type=False
    )

    # 2. Table: code_improvement_proposals
    op.create_table(
        "code_improvement_proposals",
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
        sa.Column(
            "finding_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_review_findings.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "linked_requirement_id",
            UUID(as_uuid=True),
            sa.ForeignKey("requirements.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("rule_id", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("problem_summary", sa.Text(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column(
            "file_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_files.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("current_code", sa.Text(), nullable=False),
        sa.Column("proposed_code", sa.Text(), nullable=False),
        sa.Column("patch_diff", sa.Text(), nullable=False),
        sa.Column("affected_files", JSON, nullable=False, server_default="[]"),
        sa.Column("affected_requirements", JSON, nullable=False, server_default="[]"),
        sa.Column("affected_tests", JSON, nullable=False, server_default="[]"),
        sa.Column("risks", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="85.0"),
        sa.Column("uncertainty", sa.Text(), nullable=True),
        sa.Column("status", improvement_status_type, nullable=False, server_default="proposed", index=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_code_improvements_project_status", "code_improvement_proposals", ["project_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_code_improvements_project_status", table_name="code_improvement_proposals")
    op.drop_table("code_improvement_proposals")
    sa.Enum(name="improvement_status").drop(op.get_bind(), checkfirst=True)
