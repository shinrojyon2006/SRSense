"""Create verification specifications and test cases tables

Revision ID: 009
Revises: 008
Create Date: 2026-08-18 03:10:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers
revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums
    verification_type_enum = sa.Enum(
        "functional", "performance", "security", "usability",
        "reliability", "availability", "data_validation",
        "boundary_constraint", "integration",
        name="verificationtype"
    )
    readiness_enum = sa.Enum(
        "explicit_measurable", "confidently_inferred", "verification_gap",
        name="verificationreadiness"
    )
    verification_status_enum = sa.Enum(
        "unverified", "partially_ready", "ready_for_verification", "verified",
        name="verificationstatus"
    )
    test_case_type_enum = sa.Enum(
        "positive", "negative", "boundary", "performance", "security",
        name="testcasetype"
    )
    execution_status_enum = sa.Enum(
        "untested", "passed", "failed", "blocked",
        name="testexecutionstatus"
    )

    # 2. Create verification_specifications table
    op.create_table(
        "verification_specifications",
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
            unique=True,
        ),
        sa.Column("metric", sa.String(255), nullable=True),
        sa.Column("operator", sa.String(50), nullable=True),
        sa.Column("threshold", sa.String(255), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("population_sample", sa.String(255), nullable=True),
        sa.Column("condition", sa.String(500), nullable=True),
        sa.Column("expected_result", sa.String(500), nullable=True),
        sa.Column("verification_type", verification_type_enum, nullable=False, server_default="functional"),
        sa.Column("readiness_status", readiness_enum, nullable=False, server_default="explicit_measurable"),
        sa.Column("verification_status", verification_status_enum, nullable=False, server_default="unverified"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("pass_condition", sa.String(500), nullable=True),
        sa.Column("missing_elements", JSON, nullable=False),
        sa.Column("acceptance_criteria", JSON, nullable=False),
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
    op.create_index(op.f("ix_verification_specifications_project_id"), "verification_specifications", ["project_id"], unique=False)
    op.create_index(op.f("ix_verification_specifications_requirement_id"), "verification_specifications", ["requirement_id"], unique=True)

    # 3. Create test_cases table
    op.create_table(
        "test_cases",
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
        sa.Column(
            "verification_spec_id",
            UUID(as_uuid=True),
            sa.ForeignKey("verification_specifications.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("test_type", test_case_type_enum, nullable=False, server_default="positive"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("preconditions", sa.String(500), nullable=True),
        sa.Column("steps", JSON, nullable=False),
        sa.Column("expected_result", sa.String(500), nullable=False),
        sa.Column("execution_status", execution_status_enum, nullable=False, server_default="untested"),
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
    op.create_index(op.f("ix_test_cases_project_id"), "test_cases", ["project_id"], unique=False)
    op.create_index(op.f("ix_test_cases_requirement_id"), "test_cases", ["requirement_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_test_cases_requirement_id"), table_name="test_cases")
    op.drop_index(op.f("ix_test_cases_project_id"), table_name="test_cases")
    op.drop_table("test_cases")

    op.drop_index(op.f("ix_verification_specifications_requirement_id"), table_name="verification_specifications")
    op.drop_index(op.f("ix_verification_specifications_project_id"), table_name="verification_specifications")
    op.drop_table("verification_specifications")

    op.execute("DROP TYPE IF EXISTS testexecutionstatus")
    op.execute("DROP TYPE IF EXISTS testcasetype")
    op.execute("DROP TYPE IF EXISTS verificationstatus")
    op.execute("DROP TYPE IF EXISTS verificationreadiness")
    op.execute("DROP TYPE IF EXISTS verificationtype")
