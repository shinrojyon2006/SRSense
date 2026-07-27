"""
Refresh Token repository — data access layer for RefreshToken model.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for RefreshToken operations."""

    model = RefreshToken

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Find a refresh token by string."""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def revoke_token(self, token: str) -> bool:
        """Revoke a specific refresh token."""
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token == token)
            .values(revoked=True)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user (e.g. on logout all devices)."""
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
        await self.db.commit()
        return result.rowcount
