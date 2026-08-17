"""Create requirement relationships table

Revision ID: 006
Revises: 005
Create Date: 2026-08-18 02:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enum type for relationship type
    rel_type_enum = sa.Enum("depends_on", "conflicts_with", "derived_from", "verified_by", name="relationshiptype")

    # 2. Create requirement_relationships table
    op.create_table(
        "requirement_relationships",
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
        sa.Column("type", rel_type_enum, nullable=False),
        sa.Column("metadata", JSON, nullable=True),
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
        sa.CheckConstraint("source_id != target_id", name="ck_requirement_relationships_no_self_loop"),
        sa.UniqueConstraint("project_id", "source_id", "target_id", "type", name="uq_requirement_relationships_edge"),
    )
    op.create_index(op.f("ix_requirement_relationships_project_id"), "requirement_relationships", ["project_id"], unique=False)
    op.create_index(op.f("ix_requirement_relationships_source_id"), "requirement_relationships", ["source_id"], unique=False)
    op.create_index(op.f("ix_requirement_relationships_target_id"), "requirement_relationships", ["target_id"], unique=False)
    op.create_index(op.f("ix_requirement_relationships_type"), "requirement_relationships", ["type"], unique=False)
    op.create_index(
        "ix_requirement_relationships_project_source",
        "requirement_relationships",
        ["project_id", "source_id", "type"],
        unique=False,
    )
    op.create_index(
        "ix_requirement_relationships_project_target",
        "requirement_relationships",
        ["project_id", "target_id", "type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_requirement_relationships_project_target", table_name="requirement_relationships")
    op.drop_index("ix_requirement_relationships_project_source", table_name="requirement_relationships")
    op.drop_index(op.f("ix_requirement_relationships_type"), table_name="requirement_relationships")
    op.drop_index(op.f("ix_requirement_relationships_target_id"), table_name="requirement_relationships")
    op.drop_index(op.f("ix_requirement_relationships_source_id"), table_name="requirement_relationships")
    op.drop_index(op.f("ix_requirement_relationships_project_id"), table_name="requirement_relationships")
    op.drop_table("requirement_relationships")
    op.execute("DROP TYPE IF EXISTS relationshiptype")
