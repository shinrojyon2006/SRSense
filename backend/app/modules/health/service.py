"""
Health Module Service.
"""

from app.core.config import get_settings
from app.database.base import check_db_connection
from app.modules.health.schemas import HealthResponse

settings = get_settings()


class HealthService:
    """Service layer for health checks."""

    @staticmethod
    async def get_health_status() -> HealthResponse:
        """Query database connectivity and construct health payload."""
        db_connected = await check_db_connection()
        return HealthResponse(
            status="healthy",
            version=settings.APP_VERSION,
            database="connected" if db_connected else "disconnected",
        )
