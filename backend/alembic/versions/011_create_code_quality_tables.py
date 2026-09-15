"""Create code review & quality intelligence tables (code_review_reports, code_review_findings)

Revision ID: 011
Revises: 010
Create Date: 2026-09-05 00:25:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM as PG_ENUM

# revision identifiers
revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums idempotently
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE code_health_status AS ENUM ('healthy', 'needs_attention', 'at_risk');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE finding_category AS ENUM ('security', 'performance', 'maintainability', 'compliance', 'quality');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE finding_severity AS ENUM ('critical', 'warning', 'info');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    code_health_status_type = PG_ENUM("healthy", "needs_attention", "at_risk", name="code_health_status", create_type=False)
    finding_category_type = PG_ENUM("security", "performance", "maintainability", "compliance", "quality", name="finding_category", create_type=False)
    finding_severity_type = PG_ENUM("critical", "warning", "info", name="finding_severity", create_type=False)

    # 2. Table: code_review_reports
    op.create_table(
        "code_review_reports",
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
        sa.Column("overall_score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("health_status", code_health_status_type, nullable=False, server_default="healthy"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("total_files_analyzed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_issues_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("info_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("category_counts", JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 3. Table: code_review_findings
    op.create_table(
        "code_review_findings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "report_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_review_reports.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "file_id",
            UUID(as_uuid=True),
            sa.ForeignKey("code_files.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("file_path", sa.String(1024), nullable=False, index=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("category", finding_category_type, nullable=False, index=True),
        sa.Column("severity", finding_severity_type, nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rule_id", sa.String(50), nullable=False, index=True),
        sa.Column("suggestion", sa.Text(), nullable=False),
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column(
            "linked_requirement_id",
            UUID(as_uuid=True),
            sa.ForeignKey("requirements.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_code_findings_report_severity", "code_review_findings", ["report_id", "severity"])
    op.create_index("ix_code_findings_report_category", "code_review_findings", ["report_id", "category"])


def downgrade() -> None:
    op.drop_index("ix_code_findings_report_category", table_name="code_review_findings")
    op.drop_index("ix_code_findings_report_severity", table_name="code_review_findings")
    op.drop_table("code_review_findings")
    op.drop_table("code_review_reports")

    sa.Enum(name="finding_severity").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="finding_category").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="code_health_status").drop(op.get_bind(), checkfirst=True)
