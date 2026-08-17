"""Create documents table and requirement traceability columns

Revision ID: 005
Revises: 004
Create Date: 2026-08-18 01:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enum types for document file_type and status
    doc_filetype_enum = sa.Enum("pdf", "docx", "txt", name="documentfiletype")
    doc_status_enum = sa.Enum("uploaded", "extracting", "extracted", "failed", name="documentstatus")

    # 2. Create documents table
    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", doc_filetype_enum, nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("status", doc_status_enum, nullable=False, server_default="uploaded"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("doc_metadata", JSON, nullable=True),
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
    op.create_index(op.f("ix_documents_project_id"), "documents", ["project_id"], unique=False)
    op.create_index(op.f("ix_documents_status"), "documents", ["status"], unique=False)
    op.create_index("ix_documents_project_status", "documents", ["project_id", "status"], unique=False)

    # 3. Add traceability columns to requirements table
    op.add_column(
        "requirements",
        sa.Column(
            "source_document_id",
            UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("requirements", sa.Column("source_section", sa.String(200), nullable=True))
    op.add_column("requirements", sa.Column("source_snippet", sa.Text(), nullable=True))
    op.add_column("requirements", sa.Column("original_req_id", sa.String(50), nullable=True))
    op.create_index(
        op.f("ix_requirements_source_document_id"),
        "requirements",
        ["source_document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_requirements_source_document_id"), table_name="requirements")
    op.drop_column("requirements", "original_req_id")
    op.drop_column("requirements", "source_snippet")
    op.drop_column("requirements", "source_section")
    op.drop_column("requirements", "source_document_id")

    op.drop_index("ix_documents_project_status", table_name="documents")
    op.drop_index(op.f("ix_documents_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_project_id"), table_name="documents")
    op.drop_table("documents")

    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS documentfiletype")
