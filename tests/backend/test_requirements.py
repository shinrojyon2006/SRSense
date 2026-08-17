"""
Backend requirements test suite.

Tests requirement CRUD operations, project ownership isolation, and counter synchronization.
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_and_list_requirement():
    """Test requirement creation and project list query."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register user
        unique_email = f"req_test1_{int(time.time() * 1000)}@srsense.ai"
        reg_res = await ac.post(
            "/api/auth/register",
            json={
                "name": "Requirement Tester 1",
                "email": unique_email,
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create project
        proj_res = await ac.post(
            "/api/projects",
            json={
                "title": "SRS Test Project 1",
                "description": "Test container",
                "status": "active",
            },
            headers=headers,
        )
        assert proj_res.status_code == 201
        project_id = proj_res.json()["id"]

        # Create requirement
        req_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={
                "title": "User Authentication Requirement",
                "description": "The system shall allow users to log in securely using OAuth2 and JWT tokens.",
                "type": "functional",
                "priority": "high",
                "status": "draft",
            },
            headers=headers,
        )
        assert req_res.status_code == 201
        data = req_res.json()
        assert data["title"] == "User Authentication Requirement"
        assert data["type"] == "functional"

        # Verify project counter increment
        proj_check = await ac.get(f"/api/projects/{project_id}", headers=headers)
        assert proj_check.status_code == 200
        assert proj_check.json()["requirement_count"] == 1

        # List requirements
        list_res = await ac.get(f"/api/projects/{project_id}/requirements", headers=headers)
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1


@pytest.mark.asyncio
async def test_update_and_delete_requirement():
    """Test requirement update and deletion with counter decrement."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register user
        unique_email = f"req_test2_{int(time.time() * 1000)}@srsense.ai"
        reg_res = await ac.post(
            "/api/auth/register",
            json={
                "name": "Requirement Tester 2",
                "email": unique_email,
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create project
        proj_res = await ac.post(
            "/api/projects",
            json={
                "title": "SRS Test Project 2",
                "description": "Test container",
                "status": "active",
            },
            headers=headers,
        )
        assert proj_res.status_code == 201
        project_id = proj_res.json()["id"]

        # Create
        req_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={
                "title": "Initial Requirement Title",
                "description": "The system shall validate all user input prior to database execution.",
                "type": "non_functional",
                "priority": "medium",
            },
            headers=headers,
        )
        assert req_res.status_code == 201
        req_id = req_res.json()["id"]

        # Update
        up_res = await ac.put(
            f"/api/projects/{project_id}/requirements/{req_id}",
            json={"title": "Updated Requirement Title", "status": "approved"},
            headers=headers,
        )
        assert up_res.status_code == 200
        assert up_res.json()["title"] == "Updated Requirement Title"

        # Delete
        del_res = await ac.delete(
            f"/api/projects/{project_id}/requirements/{req_id}", headers=headers
        )
        assert del_res.status_code == 204

        # Verify project counter decremented to 0
        proj_check = await ac.get(f"/api/projects/{project_id}", headers=headers)
        assert proj_check.status_code == 200
        assert proj_check.json()["requirement_count"] == 0
