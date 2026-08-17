"""Create requirement suggestions table

Revision ID: 007
Revises: 006
Create Date: 2026-08-18 02:40:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, ENUM

# revision identifiers
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enum type for suggestion status
    status_enum = sa.Enum("suggested", "accepted", "rejected", "dismissed", name="suggestionstatus")

    # 2. Reference existing relationshiptype Enum (do not recreate)
    rel_type_enum = ENUM("depends_on", "conflicts_with", "derived_from", "verified_by", name="relationshiptype", create_type=False)

    # 3. Create requirement_suggestions table
    op.create_table(
        "requirement_suggestions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            UUID(as_uuid=True),
            sa.ForeignKey("requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_id",
            UUID(as_uuid=True),
            sa.ForeignKey("requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relationship_type", rel_type_enum, nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default="suggested"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.75"),
        sa.Column("conflict_category", sa.String(100), nullable=True),
        sa.Column("evidence_explanation", sa.Text(), nullable=False),
        sa.Column("suggested_resolution", sa.Text(), nullable=True),

        # Material change tracking (Mandatory Adjustment 1)
        sa.Column("source_hash", sa.String(64), nullable=False, server_default=""),
        sa.Column("target_hash", sa.String(64), nullable=False, server_default=""),
        sa.Column("detector_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("dismissal_reason", sa.Text(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),

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
        sa.CheckConstraint("source_id != target_id", name="ck_requirement_suggestions_no_self_loop"),
        sa.UniqueConstraint("project_id", "source_id", "target_id", "relationship_type", name="uq_requirement_suggestions_edge"),
    )
    op.create_index(op.f("ix_requirement_suggestions_project_id"), "requirement_suggestions", ["project_id"], unique=False)
    op.create_index(op.f("ix_requirement_suggestions_source_id"), "requirement_suggestions", ["source_id"], unique=False)
    op.create_index(op.f("ix_requirement_suggestions_target_id"), "requirement_suggestions", ["target_id"], unique=False)
    op.create_index(op.f("ix_requirement_suggestions_relationship_type"), "requirement_suggestions", ["relationship_type"], unique=False)
    op.create_index(op.f("ix_requirement_suggestions_status"), "requirement_suggestions", ["status"], unique=False)
    op.create_index(
        "ix_requirement_suggestions_project_status",
        "requirement_suggestions",
        ["project_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_requirement_suggestions_project_status", table_name="requirement_suggestions")
    op.drop_index(op.f("ix_requirement_suggestions_status"), table_name="requirement_suggestions")
    op.drop_index(op.f("ix_requirement_suggestions_relationship_type"), table_name="requirement_suggestions")
    op.drop_index(op.f("ix_requirement_suggestions_target_id"), table_name="requirement_suggestions")
    op.drop_index(op.f("ix_requirement_suggestions_source_id"), table_name="requirement_suggestions")
    op.drop_index(op.f("ix_requirement_suggestions_project_id"), table_name="requirement_suggestions")
    op.drop_table("requirement_suggestions")
    op.execute("DROP TYPE IF EXISTS suggestionstatus")
