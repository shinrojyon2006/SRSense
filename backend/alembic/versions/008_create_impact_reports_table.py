"""Create requirement impact reports table

Revision ID: 008
Revises: 007
Create Date: 2026-08-18 02:50:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers
revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enum type for ChangeType
    change_type_enum = sa.Enum("cosmetic", "metadata", "behavioral", name="changetype")

    # 2. Create requirement_impact_reports table
    op.create_table(
        "requirement_impact_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "requirement_id",
            UUID(as_uuid=True),
            sa.ForeignKey("requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("change_type", change_type_enum, nullable=False, server_default="behavioral"),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("direct_affected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("transitive_affected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conflicts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("report_data", JSON, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(op.f("ix_requirement_impact_reports_project_id"), "requirement_impact_reports", ["project_id"], unique=False)
    op.create_index(op.f("ix_requirement_impact_reports_requirement_id"), "requirement_impact_reports", ["requirement_id"], unique=False)
    op.create_index(
        "ix_requirement_impact_reports_project_req",
        "requirement_impact_reports",
        ["project_id", "requirement_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_requirement_impact_reports_project_req", table_name="requirement_impact_reports")
    op.drop_index(op.f("ix_requirement_impact_reports_requirement_id"), table_name="requirement_impact_reports")
    op.drop_index(op.f("ix_requirement_impact_reports_project_id"), table_name="requirement_impact_reports")
    op.drop_table("requirement_impact_reports")
    op.execute("DROP TYPE IF EXISTS changetype")
