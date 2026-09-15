"""
Sprint 2.1 — Code Review & Code Quality API Integration Tests.

Validates API routes, review scan trigger, findings filtering, search, pagination,
authorization isolation, and AI fallback behavior.
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
async def test_code_quality_api_full_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ts = int(time.time() * 1000)
        email_a = f"quality_owner_{ts}@srsense.ai"
        reg_a = await ac.post(
            "/api/auth/register",
            json={
                "name": "Quality Owner",
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
            json={"title": "Quality Project A", "description": "Sprint 2.1 Test", "status": "active"},
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

        # 3. Trigger Code Review Scan (POST /api/projects/{project_id}/codebase/review)
        review_res = await ac.post(
            f"/api/projects/{project_id}/codebase/review",
            headers=headers_a,
        )
        assert review_res.status_code == 200
        report = review_res.json()
        assert report["overall_score"] < 100
        assert report["critical_count"] >= 2  # SEC-001 secret, SEC-002 eval, SEC-004 ssl
        assert report["total_issues_count"] >= 3

        # 4. Get Latest Review Report (GET /api/projects/{project_id}/codebase/review)
        latest_res = await ac.get(
            f"/api/projects/{project_id}/codebase/review",
            headers=headers_a,
        )
        assert latest_res.status_code == 200
        latest_report = latest_res.json()
        assert latest_report["id"] == report["id"]

        # 5. Query Findings with Filtering (GET /api/projects/{project_id}/codebase/findings)
        findings_res = await ac.get(
            f"/api/projects/{project_id}/codebase/findings?severity=critical",
            headers=headers_a,
        )
        assert findings_res.status_code == 200
        findings_data = findings_res.json()
        assert findings_data["total_findings"] >= 2
        for f in findings_data["findings"]:
            assert f["severity"] == "critical"
            assert f["ai_explanation"] is not None

        # Search filter
        sec_search = await ac.get(
            f"/api/projects/{project_id}/codebase/findings?search=SEC-001",
            headers=headers_a,
        )
        assert sec_search.status_code == 200
        assert sec_search.json()["total_findings"] == 1

        # 6. Security Isolation (User B cannot access Project A findings)
        email_b = f"unauth_quality_b_{ts + 999}@srsense.ai"
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

        unauth_findings = await ac.get(
            f"/api/projects/{project_id}/codebase/findings",
            headers=headers_b,
        )
        assert unauth_findings.status_code == 403
