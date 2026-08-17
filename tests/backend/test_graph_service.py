"""
Backend Knowledge Graph Service & API Test Suite.

Verifies relationship edge creation, dependency cycle detection,
symmetric conflict handling, cross-project protection, self-reference rejection,
and graph traversal.
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_knowledge_graph_suite():
    """Test comprehensive knowledge graph operations, cycle prevention, and symmetric conflicts."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Register User A & Create Project
        email_a = f"graph_owner_{int(time.time() * 1000)}@srsense.ai"
        reg_a = await ac.post(
            "/api/auth/register",
            json={
                "name": "Graph Owner",
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
            json={"title": "Graph Knowledge Project", "description": "Testing graph logic", "status": "active"},
            headers=headers_a,
        )
        assert proj_a.status_code == 201
        project_id = proj_a.json()["id"]

        # 2. Create Requirements A, B, C, D
        req_a_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "Req A", "description": "Authentication module", "type": "functional"},
            headers=headers_a,
        )
        req_b_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "Req B", "description": "User database schema", "type": "system"},
            headers=headers_a,
        )
        req_c_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "Req C", "description": "Session cache store", "type": "system"},
            headers=headers_a,
        )
        req_d_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={"title": "Req D", "description": "Token refresher service", "type": "functional"},
            headers=headers_a,
        )
        assert req_a_res.status_code == 201
        assert req_b_res.status_code == 201
        assert req_c_res.status_code == 201
        assert req_d_res.status_code == 201

        req_a = req_a_res.json()["id"]
        req_b = req_b_res.json()["id"]
        req_c = req_c_res.json()["id"]
        req_d = req_d_res.json()["id"]

        # 3. Test Self-referential Loop Rejection (A -> A)
        self_res = await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_a, "target_id": req_a, "type": "depends_on"},
            headers=headers_a,
        )
        assert self_res.status_code == 400
        assert "Self-referential relationships are not allowed" in self_res.json()["detail"]

        # 4. Test Valid Acyclic Dependency Chain (A -> B -> C -> D)
        ab_res = await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_a, "target_id": req_b, "type": "depends_on"},
            headers=headers_a,
        )
        bc_res = await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_b, "target_id": req_c, "type": "depends_on"},
            headers=headers_a,
        )
        cd_res = await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_c, "target_id": req_d, "type": "depends_on"},
            headers=headers_a,
        )
        assert ab_res.status_code == 201
        assert bc_res.status_code == 201
        assert cd_res.status_code == 201

        # 5. Test Direct Cycle Prevention (B -> A)
        direct_cycle_res = await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_b, "target_id": req_a, "type": "depends_on"},
            headers=headers_a,
        )
        assert direct_cycle_res.status_code == 400
        assert "Circular dependency detected" in direct_cycle_res.json()["detail"]

        # 6. Test 3-Node Cycle Prevention (C -> A)
        three_cycle_res = await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_c, "target_id": req_a, "type": "depends_on"},
            headers=headers_a,
        )
        assert three_cycle_res.status_code == 400
        assert "Circular dependency detected" in three_cycle_res.json()["detail"]

        # 7. Test Longer Cycle Prevention (D -> A)
        long_cycle_res = await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_d, "target_id": req_a, "type": "depends_on"},
            headers=headers_a,
        )
        assert long_cycle_res.status_code == 400
        assert "Circular dependency detected" in long_cycle_res.json()["detail"]

        # 8. Test Symmetric Conflict Behavior (A conflicts_with D)
        conf_res1 = await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_a, "target_id": req_d, "type": "conflicts_with"},
            headers=headers_a,
        )
        assert conf_res1.status_code == 201
        conf_id = conf_res1.json()["id"]

        # Attempting reverse direction D conflicts_with A -> 400 Already Exists
        conf_res2 = await ac.post(
            f"/api/projects/{project_id}/graph/relationships",
            json={"source_id": req_d, "target_id": req_a, "type": "conflicts_with"},
            headers=headers_a,
        )
        assert conf_res2.status_code == 400

        # Query A conflicts -> returns D
        a_rel_res = await ac.get(
            f"/api/projects/{project_id}/graph/requirements/{req_a}",
            headers=headers_a,
        )
        assert a_rel_res.status_code == 200
        assert len(a_rel_res.json()["conflicts"]) == 1

        # Query D conflicts -> returns A
        d_rel_res = await ac.get(
            f"/api/projects/{project_id}/graph/requirements/{req_d}",
            headers=headers_a,
        )
        assert d_rel_res.status_code == 200
        assert len(d_rel_res.json()["conflicts"]) == 1

        # 9. Query Complete Graph & Dependency Chain
        graph_res = await ac.get(
            f"/api/projects/{project_id}/graph/relationships",
            headers=headers_a,
        )
        assert graph_res.status_code == 200
        assert graph_res.json()["total_nodes"] == 4
        assert graph_res.json()["total_edges"] == 4  # 3 depends_on + 1 conflicts_with

        dep_chain_res = await ac.get(
            f"/api/projects/{project_id}/graph/requirements/{req_a}/dependencies",
            headers=headers_a,
        )
        assert dep_chain_res.status_code == 200
        assert len(dep_chain_res.json()["upstream_dependencies"]) == 1

        # 10. Delete Conflict Relationship cleanly
        del_conf = await ac.delete(
            f"/api/projects/{project_id}/graph/relationships/{conf_id}",
            headers=headers_a,
        )
        assert del_conf.status_code == 204

        # 11. Test Security / Cross-Project Protection
        email_b = f"unauth_graph_{int(time.time() * 1000)}@srsense.ai"
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

        unauth_graph = await ac.get(
            f"/api/projects/{project_id}/graph/relationships",
            headers=headers_b,
        )
        assert unauth_graph.status_code == 404
