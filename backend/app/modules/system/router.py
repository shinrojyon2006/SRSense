"""
System Module Router.
"""

from fastapi import APIRouter
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/system", tags=["System"])


@router.get("/info")
async def get_system_info():
    """System information endpoint."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
    }
