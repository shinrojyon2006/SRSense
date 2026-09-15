"""Create code improvement evaluations table (code_improvement_evaluations)

Revision ID: 013
Revises: 012
Create Date: 2026-09-05 01:10:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM as PG_ENUM

# revision identifiers
revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enum idempotently
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE evaluation_result_classification AS ENUM ('improved', 'unchanged', 'regressed', 'partially_improved', 'undetermined');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    result_classification_type = PG_ENUM(
        "improved", "unchanged", "regressed", "partially_improved", "undetermined",
        name="evaluation_result_classification", create_type=False
    )
    health_status_type = PG_ENUM(
        "healthy", "needs_attention", "at_risk",
        name="code_health_status", create_type=False
    )

    # 2. Table: code_improvement_evaluations
    op.create_table(
        "code_improvement_evaluations",
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
            "proposal_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_improvement_proposals.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column(
            "before_report_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_review_reports.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "after_report_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_review_reports.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("before_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("after_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("before_health", health_status_type, nullable=False, server_default="healthy"),
        sa.Column("after_health", health_status_type, nullable=False, server_default="healthy"),
        sa.Column("before_summary", JSON, nullable=False, server_default="{}"),
        sa.Column("after_summary", JSON, nullable=False, server_default="{}"),
        sa.Column("category_scores", JSON, nullable=False, server_default="{}"),
        sa.Column("resolved_findings", JSON, nullable=False, server_default="[]"),
        sa.Column("remaining_findings", JSON, nullable=False, server_default="[]"),
        sa.Column("new_findings", JSON, nullable=False, server_default="[]"),
        sa.Column("unchanged_findings", JSON, nullable=False, server_default="[]"),
        sa.Column("requirement_compliance_impact", JSON, nullable=False, server_default="{}"),
        sa.Column("test_impact", JSON, nullable=False, server_default="{}"),
        sa.Column("regression_detected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("regression_details", JSON, nullable=False, server_default="[]"),
        sa.Column(
            "result_classification",
            result_classification_type,
            nullable=False,
            server_default="undetermined",
            index=True,
        ),
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_evaluations_project_result", "code_improvement_evaluations", ["project_id", "result_classification"])


def downgrade() -> None:
    op.drop_index("ix_evaluations_project_result", table_name="code_improvement_evaluations")
    op.drop_table("code_improvement_evaluations")
    sa.Enum(name="evaluation_result_classification").drop(op.get_bind(), checkfirst=True)
