"""
User repository — data access layer for User model.

Extends the base repository with user-specific queries.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User CRUD and lookup operations."""

    model = User

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Find a user by their email address."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        user = await self.get_by_email(email)
        return user is not None
