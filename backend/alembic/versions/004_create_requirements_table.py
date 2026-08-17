"""Create requirements table

Revision ID: 004
Revises: 003
Create Date: 2026-08-18 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Enum types for requirement type, priority, and status
    req_type_enum = sa.Enum(
        "business", "user", "functional", "non_functional", "system", name="requirementtype"
    )
    req_priority_enum = sa.Enum(
        "low", "medium", "high", "critical", name="requirementpriority"
    )
    req_status_enum = sa.Enum(
        "draft", "in_review", "approved", "rejected", name="requirementstatus"
    )

    op.create_table(
        "requirements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("type", req_type_enum, nullable=False, server_default="functional"),
        sa.Column("priority", req_priority_enum, nullable=False, server_default="medium"),
        sa.Column("status", req_status_enum, nullable=False, server_default="draft"),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("source", sa.String(100), nullable=False, server_default="User Input"),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("analysis_result", JSON, nullable=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            UUID(as_uuid=True),
            sa.ForeignKey("requirements.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
    op.create_index(op.f("ix_requirements_project_id"), "requirements", ["project_id"], unique=False)
    op.create_index(op.f("ix_requirements_type"), "requirements", ["type"], unique=False)
    op.create_index(op.f("ix_requirements_priority"), "requirements", ["priority"], unique=False)
    op.create_index(op.f("ix_requirements_status"), "requirements", ["status"], unique=False)
    op.create_index(op.f("ix_requirements_created_at"), "requirements", ["created_at"], unique=False)
    op.create_index("ix_requirements_project_type", "requirements", ["project_id", "type"], unique=False)
    op.create_index("ix_requirements_project_priority", "requirements", ["project_id", "priority"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_requirements_project_priority", table_name="requirements")
    op.drop_index("ix_requirements_project_type", table_name="requirements")
    op.drop_index(op.f("ix_requirements_created_at"), table_name="requirements")
    op.drop_index(op.f("ix_requirements_status"), table_name="requirements")
    op.drop_index(op.f("ix_requirements_priority"), table_name="requirements")
    op.drop_index(op.f("ix_requirements_type"), table_name="requirements")
    op.drop_index(op.f("ix_requirements_project_id"), table_name="requirements")
    op.drop_table("requirements")
    op.execute("DROP TYPE IF EXISTS requirementstatus")
    op.execute("DROP TYPE IF EXISTS requirementpriority")
    op.execute("DROP TYPE IF EXISTS requirementtype")
