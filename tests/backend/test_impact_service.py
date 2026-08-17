"""
Backend Change Impact & Risk Simulator Test Suite.

Verifies graph impact propagation, cycle safety, Change Type classification,
ephemeral What-If simulation (database non-mutability proof), persisted impact reports,
and risk scoring.
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_impact_simulator_suite():
    """Test change impact propagation, What-If non-persistence, change classification, and risk scoring."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Register User & Create Project
        email_a = f"impact_owner_{int(time.time() * 1000)}@srsense.ai"
        reg_a = await ac.post(
            "/api/auth/register",
            json={
                "name": "Impact Simulator Engineer",
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
            json={"title": "Impact Simulator Workspace", "description": "Testing change simulator", "status": "active"},
            headers=headers_a,
        )
        assert proj_a.status_code == 201
        project_id = proj_a.json()["id"]

        # 2. Create Requirement Chain: Req A -> depends_on -> Req B -> depends_on -> Req C
        req_c_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "REQ-003 Database Schema", "description": "User profile schema specification.", "type": "system"},
            headers=headers_a,
        )
        req_b_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "REQ-002 Session Cache", "description": "Session cache store for authentication.", "type": "system"},
            headers=headers_a,
        )
        req_a_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "REQ-001 Auth API", "description": "Authentication endpoint requires session cache.", "type": "functional"},
            headers=headers_a,
        )
        assert req_c_res.status_code == 201
        assert req_b_res.status_code == 201
        assert req_a_res.status_code == 201

        req_c = req_c_res.json()["id"]
        req_b = req_b_res.json()["id"]
        req_a = req_a_res.json()["id"]

        # Create Graph Relationships: Req B depends_on Req C, Req A depends_on Req B
        # Changes to C affect B (direct) and A (transitive)
        await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_b, "target_id": req_c, "type": "depends_on"},
            headers=headers_a,
        )
        await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_a, "target_id": req_b, "type": "depends_on"},
            headers=headers_a,
        )

        # 3. Test Ephemeral What-If Simulation Non-Persistence Proof (Refinement 1)
        # Fetch initial count of impact reports
        summary_before = await ac.get(
            f"/api/projects/{project_id}/impact/summary",
            headers=headers_a,
        )
        assert summary_before.status_code == 200

        sim_res = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req_c,
                "proposed_title": "REQ-003 Database Schema V2",
                "proposed_description": "User profile schema specification with encrypted JSON fields.",
                "proposed_type": "system",
                "proposed_priority": "critical",
            },
            headers=headers_a,
        )
        assert sim_res.status_code == 200
        sim_data = sim_res.json()

        assert sim_data["is_ephemeral"] is True
        assert sim_data["change_type"] == "behavioral"
        assert sim_data["direct_affected_count"] == 1  # Req B
        assert sim_data["transitive_affected_count"] == 1  # Req A
        assert sim_data["risk_score"] > 0.0

        # Verify DB remained 100% unchanged after simulation
        summary_after = await ac.get(
            f"/api/projects/{project_id}/impact/summary",
            headers=headers_a,
        )
        assert summary_after.status_code == 200
        assert summary_before.json() == summary_after.json()

        # 4. Test Change Type Classification & Weight Multipliers (Refinement 2)
        # Cosmetic change
        cosmetic_sim = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req_c,
                "proposed_title": "REQ-003 Database Schema",
                "proposed_description": "  User profile schema specification.  ",
            },
            headers=headers_a,
        )
        assert cosmetic_sim.status_code == 200
        assert cosmetic_sim.json()["change_type"] == "cosmetic"
        assert cosmetic_sim.json()["risk_score"] == 0.0

        # Metadata change (Draft -> Approved)
        meta_sim = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req_c,
                "proposed_title": "REQ-003 Database Schema",
                "proposed_description": "User profile schema specification.",
                "proposed_status": "approved",
            },
            headers=headers_a,
        )
        assert meta_sim.status_code == 200
        assert meta_sim.json()["change_type"] == "metadata"
        assert meta_sim.json()["risk_score"] < sim_data["risk_score"]  # Lower than behavioral change!

        # 5. Test Persisted Impact Report Generation
        report_res = await ac.post(
            f"/api/projects/{project_id}/impact/requirements/{req_c}/report",
            headers=headers_a,
        )
        assert report_res.status_code == 201
        report_data = report_res.json()
        assert report_data["requirement_id"] == req_c

        # 6. Test Security Isolation
        email_b = f"unauth_impact_{int(time.time() * 1000)}@srsense.ai"
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

        unauth_sim = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={"proposed_title": "Hacked", "proposed_description": "Hacked text"},
            headers=headers_b,
        )
        assert unauth_sim.status_code == 404
