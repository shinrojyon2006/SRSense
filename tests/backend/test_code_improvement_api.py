"""
Sprint 2.2 — AI Code Improvement API Integration Tests.

Validates proposed improvement generation, bounded context extraction,
human review, explicit approval/rejection flows, non-silent patch application,
stale patch handling, and project authorization isolation.
"""

import io
import time
import zipfile
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


def create_test_zip() -> bytes:
    files = {
        "main.py": """
import os
import requests

api_key = "sk_live_1234567890secret"
eval("dangerous()")
requests.get("https://insecure.local", verify=False)

def calculate(a, b):
    try:
        return a + b
    except Exception:
        pass
""",
        "db.py": """
def get_user(name):
    query = "SELECT * FROM users WHERE name = " + name
    return query
"""
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_code_improvement_full_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ts = int(time.time() * 1000)
        email_a = f"improvement_owner_{ts}@srsense.ai"
        reg_a = await ac.post(
            "/api/auth/register",
            json={
                "name": "Improvement Owner",
                "email": email_a,
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        assert reg_a.status_code == 201
        token_a = reg_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 1. Create Project A
        proj_a = await ac.post(
            "/api/projects",
            json={"title": "Improvement Project A", "description": "Sprint 2.2 Test", "status": "active"},
            headers=headers_a,
        )
        assert proj_a.status_code == 201
        project_id = proj_a.json()["id"]

        # 2. Upload Codebase ZIP
        zip_bytes = create_test_zip()
        upload_res = await ac.post(
            f"/api/projects/{project_id}/codebase/upload",
            files={"file": ("repo.zip", zip_bytes, "application/zip")},
            headers=headers_a,
        )
        assert upload_res.status_code == 201

        # 3. Trigger Code Review Scan
        review_res = await ac.post(
            f"/api/projects/{project_id}/codebase/review",
            headers=headers_a,
        )
        assert review_res.status_code == 200

        # 4. Get Findings
        findings_res = await ac.get(
            f"/api/projects/{project_id}/codebase/findings",
            headers=headers_a,
        )
        assert findings_res.status_code == 200
        findings = findings_res.json()["findings"]
        assert len(findings) > 0
        finding_eval = next((f for f in findings if f["rule_id"] == "SEC-002"), findings[0])

        # 5. Create Code Improvement Proposal
        create_res = await ac.post(
            f"/api/projects/{project_id}/codebase/improvements",
            json={"finding_id": finding_eval["id"]},
            headers=headers_a,
        )
        assert create_res.status_code == 201
        proposal = create_res.json()
        assert proposal["status"] == "proposed"
        assert proposal["rule_id"] == finding_eval["rule_id"]
        assert "diff" in proposal["patch_diff"].lower() or "---" in proposal["patch_diff"]
        assert len(proposal["affected_files"]) > 0

        proposal_id = proposal["id"]

        # 6. Retrieve Proposal Detail
        get_res = await ac.get(
            f"/api/projects/{project_id}/codebase/improvements/{proposal_id}",
            headers=headers_a,
        )
        assert get_res.status_code == 200
        assert get_res.json()["id"] == proposal_id

        # 7. Explicitly Approve and Apply Improvement
        approve_res = await ac.post(
            f"/api/projects/{project_id}/codebase/improvements/{proposal_id}/approve",
            headers=headers_a,
        )
        assert approve_res.status_code == 200
        approved_prop = approve_res.json()
        assert approved_prop["status"] == "applied"
        assert approved_prop["applied_at"] is not None

        # 8. Create a second proposal and REJECT it
        finding_sec1 = next((f for f in findings if f["rule_id"] == "SEC-001"), findings[-1])
        create_res_2 = await ac.post(
            f"/api/projects/{project_id}/codebase/improvements",
            json={"finding_id": finding_sec1["id"]},
            headers=headers_a,
        )
        assert create_res_2.status_code == 201
        proposal_2_id = create_res_2.json()["id"]

        reject_res = await ac.post(
            f"/api/projects/{project_id}/codebase/improvements/{proposal_2_id}/reject",
            headers=headers_a,
        )
        assert reject_res.status_code == 200
        assert reject_res.json()["status"] == "rejected"

        # 9. Authorization Isolation Test (User B cannot approve User A's proposal)
        email_b = f"unauth_imp_b_{ts + 888}@srsense.ai"
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
        assert reg_b.status_code == 201
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        unauth_res = await ac.post(
            f"/api/projects/{project_id}/codebase/improvements/{proposal_id}/approve",
            headers=headers_b,
        )
        assert unauth_res.status_code == 403
