"""
Health check test suite for Sprint 1.1 foundation.
"""

import sys
from pathlib import Path
import pytest
from httpx import AsyncClient

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test /api/health endpoint returns status healthy and version 1.0.0."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "database" in data
