"""
User management API routes.

Handles user profile updates and user-related operations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.put("/update", response_model=UserResponse)
async def update_user(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the authenticated user's profile.

    Only provided fields will be updated. Requires a valid JWT Bearer token.
    """
    service = UserService(db)
    return await service.update_user(current_user, data)
