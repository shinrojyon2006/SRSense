"""
Authentication service — business logic for auth operations.

Handles registration, login, token rotation, token refresh, logout,
and profile retrieval while enforcing security best practices.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token_string,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger("srsense.auth")


class AuthService:
    """Service layer for authentication and token rotation operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)

    async def _issue_token_pair(self, user: User) -> TokenResponse:
        """Helper to create an access token and a persisted refresh token."""
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token_str = create_refresh_token_string()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=expires_at,
            revoked=False,
        )
        await self.token_repo.create(refresh_token_obj)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            user=UserResponse.model_validate(user),
        )

    async def register(self, data: UserCreate) -> TokenResponse:
        """
        Register a new user account.

        Validates email uniqueness, hashes password, creates user,
        and returns access + refresh tokens.
        """
        if await self.user_repo.email_exists(data.email):
            raise ConflictException("An account with this email already exists")

        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=UserRole(data.role.value),
        )

        user = await self.user_repo.create(user)
        logger.info("User registered: %s", user.email)

        return await self._issue_token_pair(user)

    async def login(self, data: UserLogin) -> TokenResponse:
        """
        Authenticate user credentials and return access + refresh tokens.
        """
        user = await self.user_repo.get_by_email(data.email)

        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        logger.info("User logged in: %s", user.email)
        return await self._issue_token_pair(user)

    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        """
        Secure Token Rotation:
        1. Validates existing refresh token.
        2. If valid, revokes old refresh token.
        3. Issues brand new access + refresh token pair.
        4. If token is invalid/revoked/expired, denies access.
        """
        token_obj = await self.token_repo.get_by_token(refresh_token_str)

        if not token_obj or not token_obj.is_valid():
            logger.warning("Attempted use of invalid/revoked refresh token")
            raise UnauthorizedException("Invalid or expired refresh token")

        # Revoke the used refresh token (Rotation)
        await self.token_repo.revoke_token(token_obj.token)

        user = await self.user_repo.get_by_id(token_obj.user_id)
        if not user:
            raise UnauthorizedException("User no longer exists")

        logger.info("Refresh token rotated for user: %s", user.email)
        return await self._issue_token_pair(user)

    async def logout(self, refresh_token_str: str) -> None:
        """
        Revoke the refresh token on logout.
        """
        if refresh_token_str:
            await self.token_repo.revoke_token(refresh_token_str)
            logger.info("Refresh token revoked during logout")

    @staticmethod
    async def get_profile(user: User) -> UserResponse:
        """Return the authenticated user's profile."""
        return UserResponse.model_validate(user)
