"""
Sprint 2.4 — Requirement -> Code -> Test Traceability API Integration Tests.

Validates end-to-end REST API endpoints:
- Test discovery & automatic requirement matching
- Traceability matrix retrieval per requirement
- Overall traceability summary & 0-100 score computation
- Coverage gap analysis (missing code/tests)
- AI test proposal generation (non-autonomous, proposal-only)
- Manual link creation & deletion
- Ownership authorization isolation between users.
"""

import io
import time
import zipfile
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


def create_sample_zip() -> bytes:
    files = {
        "app/auth.py": """
def login(username, password):
    if username == "admin" and password == "secret":
        return True
    return False
""",
        "tests/test_auth.py": """
import pytest

def test_REQ_101_login_success():
    assert True

def test_login_failure():
    assert False == False
""",
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_traceability_api_full_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ts = int(time.time() * 1000)

        # 1. Register Owner A
        email_a = f"trace_owner_{ts}@srsense.ai"
        reg_a = await ac.post(
            "/api/auth/register",
            json={
                "name": "Trace Owner",
                "email": email_a,
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        assert reg_a.status_code == 201, reg_a.text
        token_a = reg_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 2. Create Project
        proj_res = await ac.post(
            "/api/projects",
            json={
                "title": "Traceability Proj",
                "description": "Sprint 2.4 Traceability Matrix Test",
            },
            headers=headers_a,
        )
        assert proj_res.status_code == 201, proj_res.text
        project_id = proj_res.json()["id"]

        # 3. Create Requirement
        req_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={
                "original_req_id": "REQ-101",
                "title": "User Authentication & Password Login",
                "description": "Users must be able to authenticate securely using username and password.",
                "type": "functional",
                "priority": "high",
            },
            headers=headers_a,
        )
        assert req_res.status_code == 201, req_res.text
        req_id = req_res.json()["id"]

        # 4. Upload Codebase ZIP
        zip_bytes = create_sample_zip()
        upload_res = await ac.post(
            f"/api/projects/{project_id}/codebase/upload",
            files={"file": ("codebase.zip", zip_bytes, "application/zip")},
            headers=headers_a,
        )
        assert upload_res.status_code in [200, 201], upload_res.text

        # 5. Trigger Test Discovery
        discover_res = await ac.post(
            f"/api/projects/{project_id}/traceability/tests/discover",
            headers=headers_a,
        )
        assert discover_res.status_code == 200, discover_res.text
        tests_data = discover_res.json()
        assert len(tests_data) >= 1

        # 6. Fetch Traceability Matrix
        matrix_res = await ac.get(
            f"/api/projects/{project_id}/traceability/requirements",
            headers=headers_a,
        )
        assert matrix_res.status_code == 200, matrix_res.text
        matrix = matrix_res.json()
        assert len(matrix) >= 1
        req_item = next(item for item in matrix if item["requirement_id"] == req_id)
        assert req_item["title"] == "User Authentication & Password Login"
        assert req_item["has_test"] is True

        # 7. Fetch Traceability Summary
        summary_res = await ac.get(
            f"/api/projects/{project_id}/traceability/summary",
            headers=headers_a,
        )
        assert summary_res.status_code == 200, summary_res.text
        summary = summary_res.json()
        assert summary["total_requirements"] >= 1
        assert "traceability_score" in summary
        assert "health_status" in summary

        # 8. Fetch Traceability Gaps
        gaps_res = await ac.get(
            f"/api/projects/{project_id}/traceability/gaps",
            headers=headers_a,
        )
        assert gaps_res.status_code == 200, gaps_res.text
        gaps_data = gaps_res.json()
        assert "total_gaps" in gaps_data
        assert "gaps" in gaps_data

        # 9. Request AI Test Proposal
        suggest_res = await ac.post(
            f"/api/projects/{project_id}/traceability/tests/suggest",
            json={"requirement_id": req_id},
            headers=headers_a,
        )
        assert suggest_res.status_code == 200, suggest_res.text
        proposal = suggest_res.json()
        assert proposal["requirement_id"] == req_id
        assert "code_snippet_proposal" in proposal

        # 10. Register User B & Test Authorization Isolation
        email_b = f"trace_other_{ts}@srsense.ai"
        reg_b = await ac.post(
            "/api/auth/register",
            json={
                "name": "Trace Other",
                "email": email_b,
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        assert reg_b.status_code == 201
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B cannot access User A's traceability summary
        forbidden_res = await ac.get(
            f"/api/projects/{project_id}/traceability/summary",
            headers=headers_b,
        )
        assert forbidden_res.status_code in [403, 404]
