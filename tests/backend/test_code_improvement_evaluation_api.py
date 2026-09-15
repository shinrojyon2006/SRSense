"""
Sprint 2.3 — Before/After Code Improvement Evaluation API Integration Tests.

Validates evaluation trigger, post-change re-analysis, finding deltas, score comparison,
authorization isolation, and evaluation retrieval.
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

api_key = "sk_live_1234567890secret"

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
async def test_code_improvement_evaluation_full_api_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ts = int(time.time() * 1000)
        email_a = f"eval_owner_{ts}@srsense.ai"
        reg_a = await ac.post(
            "/api/auth/register",
            json={
                "name": "Eval Owner",
                "email": email_a,
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        assert reg_a.status_code == 201
        token_a = reg_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 1. Create Project
        proj_a = await ac.post(
            "/api/projects",
            json={"title": "Evaluation API Project", "description": "Sprint 2.3 Test", "status": "active"},
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

        # 4. Get Findings & Create Proposal
        findings_res = await ac.get(
            f"/api/projects/{project_id}/codebase/findings",
            headers=headers_a,
        )
        assert findings_res.status_code == 200
        findings = findings_res.json()["findings"]
        assert len(findings) > 0
        finding_eval = findings[0]

        create_res = await ac.post(
            f"/api/projects/{project_id}/codebase/improvements",
            json={"finding_id": finding_eval["id"]},
            headers=headers_a,
        )
        assert create_res.status_code == 201
        proposal_id = create_res.json()["id"]

        # 5. Approve & Apply Improvement
        approve_res = await ac.post(
            f"/api/projects/{project_id}/codebase/improvements/{proposal_id}/approve",
            headers=headers_a,
        )
        assert approve_res.status_code == 200

        # 6. Trigger Evaluation
        eval_res = await ac.post(
            f"/api/projects/{project_id}/codebase/improvements/{proposal_id}/evaluate",
            headers=headers_a,
        )
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        assert eval_data["proposal_id"] == proposal_id
        assert eval_data["result_classification"] in [
            "improved",
            "unchanged",
            "regressed",
            "partially_improved",
            "undetermined",
        ]
        assert "score_delta" in eval_data
        assert eval_data["test_impact"]["execution_status"] == "NOT EXECUTED"

        # 7. Get Evaluation Record
        get_eval_res = await ac.get(
            f"/api/projects/{project_id}/codebase/improvements/{proposal_id}/evaluation",
            headers=headers_a,
        )
        assert get_eval_res.status_code == 200
        assert get_eval_res.json()["id"] == eval_data["id"]

        # 8. Authorization Isolation Test (User B cannot evaluate User A's proposal)
        email_b = f"unauth_eval_{ts + 999}@srsense.ai"
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

        unauth_eval = await ac.post(
            f"/api/projects/{project_id}/codebase/improvements/{proposal_id}/evaluate",
            headers=headers_b,
        )
        assert unauth_eval.status_code == 403
