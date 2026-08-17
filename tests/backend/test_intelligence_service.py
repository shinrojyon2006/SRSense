"""
Backend Conflict & Dependency Intelligence Service & API Test Suite.

Verifies numeric conflict detection, explicit ID dependency discovery,
suggestion lifecycle (accept -> graph edge, reject -> recorded dismissal),
scan idempotency, material change reconsideration, orphan detection, and ownership isolation.
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_intelligence_suite():
    """Test comprehensive intelligence scan, idempotency, material change, accept/reject workflows."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Register User & Create Project
        email_a = f"intel_owner_{int(time.time() * 1000)}@srsense.ai"
        reg_a = await ac.post(
            "/api/auth/register",
            json={
                "name": "Intel Engineer",
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
            json={"title": "Intelligence Test Project", "description": "Testing conflict detection", "status": "active"},
            headers=headers_a,
        )
        assert proj_a.status_code == 201
        project_id = proj_a.json()["id"]

        # 2. Create Requirements:
        # REQ-021: Password exactly 8 characters
        # REQ-087: Password at least 12 characters
        # REQ-030: Explicitly references REQ-021 in description
        # REQ-099: Standalone Orphan requirement
        req21_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "REQ-021 Password Policy", "description": "Password must be exactly 8 characters.", "type": "non_functional"},
            headers=headers_a,
        )
        req87_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "REQ-087 Strong Password Policy", "description": "Password must be at least 12 characters.", "type": "non_functional"},
            headers=headers_a,
        )
        req30_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "REQ-030 Auth Module", "description": "Integrates with REQ-021 for credential validation.", "type": "functional"},
            headers=headers_a,
        )
        req99_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "REQ-099 Standalone Export", "description": "Allows PDF report export.", "type": "functional"},
            headers=headers_a,
        )

        assert req21_res.status_code == 201
        assert req87_res.status_code == 201
        assert req30_res.status_code == 201
        assert req99_res.status_code == 201

        req21_id = req21_res.json()["id"]

        # 3. Run Automated Intelligence Scan 1
        scan1 = await ac.post(
            f"/api/projects/{project_id}/intelligence/scan",
            headers=headers_a,
        )
        assert scan1.status_code == 200
        scan1_data = scan1.json()
        assert scan1_data["scanned_requirements_count"] == 4
        assert scan1_data["new_suggestions_created"] >= 2  # 1 numeric conflict + 1 dependency

        # Verify Numeric Conflict evidence
        suggestions = scan1_data["suggestions"]
        numeric_sug = next(s for s in suggestions if s["relationship_type"] == "conflicts_with")
        assert numeric_sug["confidence_score"] >= 0.90
        assert "exactly 8 characters" in numeric_sug["evidence_explanation"]
        assert "12 characters" in numeric_sug["evidence_explanation"]

        # Verify Dependency discovery
        dep_sug = next(s for s in suggestions if s["relationship_type"] == "depends_on")
        assert dep_sug["confidence_score"] >= 0.85

        # 4. Test Scan Idempotency (Run Scan 2 -> 0 new suggestions created)
        scan2 = await ac.post(
            f"/api/projects/{project_id}/intelligence/scan",
            headers=headers_a,
        )
        assert scan2.status_code == 200
        assert scan2.json()["new_suggestions_created"] == 0
        assert scan2.json()["existing_suggestions_updated"] == len(suggestions)

        # 5. Test Suggestion Rejection Workflow
        sug_to_reject = dep_sug["id"]
        rej_res = await ac.post(
            f"/api/projects/{project_id}/intelligence/suggestions/{sug_to_reject}/reject",
            json={"reason": "Manual override: not a real dependency"},
            headers=headers_a,
        )
        assert rej_res.status_code == 200
        assert rej_res.json()["status"] == "rejected"
        assert rej_res.json()["dismissal_reason"] == "Manual override: not a real dependency"

        # Scan 3 (unaltered requirements) -> Rejected suggestion remains suppressed!
        scan3 = await ac.post(
            f"/api/projects/{project_id}/intelligence/scan",
            headers=headers_a,
        )
        assert scan3.status_code == 200
        assert scan3.json()["reconsidered_suggestions_count"] == 0
        all_sugs_scan3 = scan3.json()["suggestions"]
        rejected_item = next(s for s in all_sugs_scan3 if s["id"] == sug_to_reject)
        assert rejected_item["status"] == "rejected"

        # 6. Test Material Change Reconsideration: Update REQ-030 text!
        update_req30 = await ac.put(
            f"/api/projects/{project_id}/requirements/{req30_res.json()['id']}",
            json={"title": "REQ-030 Auth Module V2", "description": "Requires REQ-021 and token exchange protocol."},
            headers=headers_a,
        )
        assert update_req30.status_code == 200

        # Scan 4 (materially changed requirement) -> Previously rejected suggestion is RECONSIDERED!
        scan4 = await ac.post(
            f"/api/projects/{project_id}/intelligence/scan",
            headers=headers_a,
        )
        assert scan4.status_code == 200
        assert scan4.json()["reconsidered_suggestions_count"] >= 1
        all_sugs_scan4 = scan4.json()["suggestions"]
        reconsidered_item = next(s for s in all_sugs_scan4 if s["id"] == sug_to_reject)
        assert reconsidered_item["status"] == "suggested"
        assert "[Reconsidered after requirement update]" in reconsidered_item["evidence_explanation"]

        # 7. Test Suggestion Acceptance Workflow -> Converts to Knowledge Graph Edge!
        sug_to_accept = numeric_sug["id"]
        acc_res = await ac.post(
            f"/api/projects/{project_id}/intelligence/suggestions/{sug_to_accept}/accept",
            headers=headers_a,
        )
        assert acc_res.status_code == 200
        assert acc_res.json()["status"] == "accepted"

        # Verify edge exists in Graph API
        graph_res = await ac.get(
            f"/api/projects/{project_id}/graph/relationships",
            headers=headers_a,
        )
        assert graph_res.status_code == 200
        assert graph_res.json()["total_edges"] == 1
        assert graph_res.json()["edges"][0]["type"] == "conflicts_with"

        # 8. Test Intelligence Summary API & Orphan Count
        sum_res = await ac.get(
            f"/api/projects/{project_id}/intelligence/summary",
            headers=headers_a,
        )
        assert sum_res.status_code == 200
        summary = sum_res.json()
        assert summary["orphan_requirements_count"] == 2  # req30 and req99 not in graph edges
        assert "high" in summary["confidence_distribution"]

        # 9. Test Security Isolation
        email_b = f"unauth_intel_{int(time.time() * 1000)}@srsense.ai"
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

        unauth_sum = await ac.get(
            f"/api/projects/{project_id}/intelligence/summary",
            headers=headers_b,
        )
        assert unauth_sum.status_code == 404
