"""
Backend Requirement-to-Verification Compiler Test Suite.
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_verification_compiler_suite():
    """Test verification compilation, readiness classification, test case generation, execution evidence, and coverage analytics."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Register User & Create Project
        email_a = f"verif_owner_{int(time.time() * 1000)}@srsense.ai"
        reg_a = await ac.post(
            "/api/auth/register",
            json={
                "name": "Verification Engineer",
                "email": email_a,
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        assert reg_a.status_code == 201
        token_a = reg_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        proj_a = await ac.post(
            "/api/projects",
            json={"title": "Verification Test Workspace", "description": "Testing compiler", "status": "active"},
            headers=headers_a,
        )
        assert proj_a.status_code == 201
        project_id = proj_a.json()["id"]

        # 2. Create Measurable Performance Requirement (REQ-001)
        req1_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "REQ-001 API Response Latency", "description": "The system shall respond within 200 ms for 95% of requests.", "type": "non_functional"},
            headers=headers_a,
        )

        # 3. Create Vague Requirement (REQ-002)
        req2_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "REQ-002 User Experience", "description": "The system should be fast and user friendly.", "type": "non_functional"},
            headers=headers_a,
        )

        assert req1_res.status_code == 201
        assert req2_res.status_code == 201
        req1_id = req1_res.json()["id"]
        req2_id = req2_res.json()["id"]

        # 4. Test Compile Measurable Performance Requirement (REQ-001)
        comp1 = await ac.post(
            f"/api/projects/{project_id}/verification/requirements/{req1_id}/compile",
            headers=headers_a,
        )
        assert comp1.status_code == 200
        data1 = comp1.json()

        assert data1["readiness_status"] == "explicit_measurable"
        assert data1["verification_status"] == "ready_for_verification"
        assert data1["metric"] == "Response Time"
        assert data1["threshold"] == "200"
        assert data1["unit"] == "ms"
        assert len(data1["test_cases"]) >= 2

        # 5. Test Compile Vague Requirement (REQ-002)
        comp2 = await ac.post(
            f"/api/projects/{project_id}/verification/requirements/{req2_id}/compile",
            headers=headers_a,
        )
        assert comp2.status_code == 200
        data2 = comp2.json()

        assert data2["readiness_status"] == "verification_gap"
        assert data2["verification_status"] == "unverified"
        assert "quantitative threshold" in data2["missing_elements"]

        # 6. Test Updating Test Execution Evidence Status (Passed) -> VERIFIED state
        tc_id = data1["test_cases"][0]["id"]
        patch_res = await ac.patch(
            f"/api/projects/{project_id}/verification/test-cases/{tc_id}",
            json={"execution_status": "passed"},
            headers=headers_a,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["execution_status"] == "passed"

        # Verify parent spec status recalculated
        get1 = await ac.get(
            f"/api/projects/{project_id}/verification/requirements/{req1_id}",
            headers=headers_a,
        )
        assert get1.status_code == 200
        assert get1.json()["verification_status"] in ("partially_ready", "verified")

        # 7. Test Summary Analytics (Readiness %, Test Gen %, Actual Verified %)
        sum_res = await ac.get(
            f"/api/projects/{project_id}/verification/summary",
            headers=headers_a,
        )
        assert sum_res.status_code == 200
        sum_data = sum_res.json()

        assert sum_data["total_requirements_count"] == 2
        assert "verification_readiness_percentage" in sum_data
        assert "test_generation_coverage_percentage" in sum_data
        assert "actual_verification_coverage_percentage" in sum_data

        # 8. Test Security Isolation
        email_b = f"unauth_verif_{int(time.time() * 1000)}@srsense.ai"
        reg_b = await ac.post(
            "/api/auth/register",
            json={
                "name": "User B",
                "email": email_b,
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

        unauth_res = await ac.get(
            f"/api/projects/{project_id}/verification/summary",
            headers=headers_b,
        )
        assert unauth_res.status_code == 404
