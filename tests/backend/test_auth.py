"""
Backend authentication test suite.

Tests registration, login, token refresh rotation, profile retrieval,
and validation logic.
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data


@pytest.mark.asyncio
async def test_register_validation_error():
    """Test registration with invalid password strength."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/auth/register",
            json={
                "name": "Weak Pass User",
                "email": "weakpass@srsense.ai",
                "password": "simple",
                "password_confirmation": "simple",
                "role": "developer",
            },
        )
    assert response.status_code == 422
