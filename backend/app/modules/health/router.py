"""
Health Module Router.
"""

from fastapi import APIRouter
from app.modules.health.schemas import HealthResponse
from app.modules.health.service import HealthService

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health Check Endpoint.

    Returns status, application version, and database connectivity.
    """
    return await HealthService.get_health_status()
