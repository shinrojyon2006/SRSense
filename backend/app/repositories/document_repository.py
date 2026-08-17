"""
Document repository — async PostgreSQL CRUD for Document entities.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document


class DocumentRepository:
    """Data access repository for Document entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_project(self, document_id: UUID, project_id: UUID) -> Optional[Document]:
        result = await self.session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.project_id == project_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_project(self, project_id: UUID) -> List[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.project_id == project_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, document: Document) -> Document:
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def delete(self, document: Document) -> None:
        await self.session.delete(document)
        await self.session.commit()
