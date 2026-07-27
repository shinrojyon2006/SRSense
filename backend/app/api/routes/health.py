"""
Health check route controller.
"""

from fastapi import APIRouter
from app.core.config import get_settings
from app.db.base import check_db_connection

settings = get_settings()

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with system status and application version.
    """
    db_connected = await check_db_connection()

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": "connected" if db_connected else "disconnected",
    }
