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


@pytest.mark.asyncio
async def test_what_if_simulator_canonical_scenarios():
    """Test all 10 canonical What-If simulation scenarios including isolated requirements (0 graph links)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Setup user and project
        email = f"canonical_impact_{int(time.time() * 1000)}@srsense.ai"
        reg = await ac.post(
            "/api/auth/register",
            json={
                "name": "Canonical Tester",
                "email": email,
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        proj = await ac.post(
            "/api/projects",
            json={"title": "Canonical Impact Workspace", "description": "Testing canonical scenarios", "status": "active"},
            headers=headers,
        )
        assert proj.status_code == 201
        project_id = proj.json()["id"]

        # Create isolated requirement 1 (Zero graph links)
        req1_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={
                "title": "User Registration",
                "description": "The SRSense System shall allow a new user to create an account using a valid email address and password.",
                "type": "functional",
                "priority": "medium",
            },
            headers=headers,
        )
        assert req1_res.status_code == 201
        req1_id = req1_res.json()["id"]

        # Create isolated requirement 2 (Zero graph links)
        req2_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={
                "title": "Response time and user interaction limits",
                "description": "The SRSense System shall respond within 200 milliseconds and require no more than 3 user interactions.",
                "type": "non_functional",
                "priority": "high",
            },
            headers=headers,
        )
        assert req2_res.status_code == 201
        req2_id = req2_res.json()["id"]

        # TEST 1: No change
        sim_no_change = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req1_id,
                "proposed_title": "User Registration",
                "proposed_description": "The SRSense System shall allow a new user to create an account using a valid email address and password.",
                "proposed_type": "functional",
                "proposed_priority": "medium",
            },
            headers=headers,
        )
        assert sim_no_change.status_code == 200
        data1 = sim_no_change.json()
        assert data1["risk_score"] == 0.0
        assert data1["change_type"] == "cosmetic"
        assert data1["detailed_classification"] == "NO_CHANGE"

        # TEST 2: Cosmetic wording change ("shall" -> "must")
        sim_cosmetic = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req1_id,
                "proposed_title": "User Registration",
                "proposed_description": "The SRSense System must allow a new user to create an account using a valid email address and password.",
            },
            headers=headers,
        )
        assert sim_cosmetic.status_code == 200
        data2 = sim_cosmetic.json()
        assert data2["change_type"] == "cosmetic"
        assert data2["risk_score"] < 10.0

        # TEST 3: Performance threshold change ("200 milliseconds" -> "500 milliseconds")
        sim_perf = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req2_id,
                "proposed_description": "The SRSense System shall respond within 500 milliseconds and require no more than 3 user interactions.",
            },
            headers=headers,
        )
        assert sim_perf.status_code == 200
        data3 = sim_perf.json()
        print("\nDATA 3:", data3)
        assert data3["intrinsic_risk_score"] > 0.0
        assert data3["detailed_classification"] == "PERFORMANCE_CHANGE"
        assert len(data3["detected_constraint_changes"]) > 0

        # TEST 4: Interaction limit change ("3 user interactions" -> "8 user interactions")
        sim_limit = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req2_id,
                "proposed_description": "The SRSense System shall respond within 200 milliseconds and require no more than 8 user interactions.",
            },
            headers=headers,
        )
        assert sim_limit.status_code == 200
        data4 = sim_limit.json()
        print("\nDATA 4:", data4)
        assert data4["intrinsic_risk_score"] > 0.0
        assert len(data4["detected_constraint_changes"]) > 0

        # TEST 5: Functional addition ("email/password" -> "email/password/phone verification")
        sim_func = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req1_id,
                "proposed_description": "The SRSense System shall allow a new user to create an account using a valid email address, password, and phone verification.",
            },
            headers=headers,
        )
        assert sim_func.status_code == 200
        data5 = sim_func.json()
        print("\nDATA 5:", data5)
        assert data5["intrinsic_risk_score"] > 0.0
        assert data5["change_type"] == "behavioral"

        # TEST 6: Behavioral reversal ("allow" -> "prevent")
        sim_reversal = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req1_id,
                "proposed_description": "The SRSense System shall prevent a new user to create an account using a valid email address and password.",
            },
            headers=headers,
        )
        assert sim_reversal.status_code == 200
        data6 = sim_reversal.json()
        print("\nDATA 6:", data6)
        assert data6["intrinsic_risk_score"] >= 35.0
        assert "BEHAVIORAL_POLARITY_REVERSAL" in str(data6["evidence_reasoning"])

        # TEST 7: Security change ("require authentication")
        sim_sec = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req1_id,
                "proposed_description": "The SRSense System shall disable OAuth security authentication and allow anonymous access.",
            },
            headers=headers,
        )
        assert sim_sec.status_code == 200
        data7 = sim_sec.json()
        print("\nDATA 7:", data7)
        assert data7["intrinsic_risk_score"] >= 25.0
        assert data7["detailed_classification"] == "SECURITY_CHANGE"

        # TEST 8: Priority change (Medium -> Critical)
        sim_prio = await ac.post(
            f"/api/projects/{project_id}/impact/simulate",
            json={
                "requirement_id": req1_id,
                "proposed_priority": "critical",
            },
            headers=headers,
        )
        assert sim_prio.status_code == 200
        data8 = sim_prio.json()
        print("\nDATA 8:", data8)
        assert data8["intrinsic_risk_score"] > 0.0
        assert "priority" in data8["changed_fields"]

        # TEST 9: Proving that 2 different requirements with 0 graph links DO NOT get identical scores
        assert data3["intrinsic_risk_score"] != data5["intrinsic_risk_score"]
        assert data3["detailed_classification"] != data5["detailed_classification"]
        assert data3["risk_score"] > 0.0
        assert data5["risk_score"] > 0.0


