"""
User service — business logic for user management.

Handles profile updates and user-specific operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdate
from app.utils.logger import get_logger

logger = get_logger("srsense.users")


class UserService:
    """Service layer for user management operations."""

    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def update_user(self, user: User, data: UserUpdate) -> UserResponse:
        """
        Update user profile fields.

        Only updates fields that are explicitly provided (non-None).

        Raises:
            ConflictException: If the new email is already taken.
        """
        if data.email and data.email != user.email:
            if await self.repo.email_exists(data.email):
                raise ConflictException("An account with this email already exists")
            user.email = data.email

        if data.name is not None:
            user.name = data.name

        updated_user = await self.repo.update(user)
        logger.info("User updated: %s", updated_user.email)

        return UserResponse.model_validate(updated_user)
