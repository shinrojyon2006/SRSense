"""
Backend Requirement Extraction, Classification, Duplicate Detection, and Batch Acceptance Test Suite.
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_extraction_classification_duplicate_and_batch_accept():
    """Test candidate extraction, classification rules, Jaccard duplicate detection, and batch acceptance."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Register User A & Create Project
        email_a = f"extractor_owner_{int(time.time() * 1000)}@srsense.ai"
        reg_a = await ac.post(
            "/api/auth/register",
            json={
                "name": "Extractor Owner",
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
            json={"title": "SRS Extraction Project", "description": "Candidate testing", "status": "active"},
            headers=headers_a,
        )
        assert proj_a.status_code == 201
        project_id = proj_a.json()["id"]

        # 2. Seed an existing requirement in PostgreSQL for duplicate testing
        seed_req = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={
                "title": "Existing Speed Requirement",
                "description": "The SRSense System shall process requests within 200 milliseconds.",
                "type": "non_functional",
                "priority": "high",
            },
            headers=headers_a,
        )
        assert seed_req.status_code == 201
        seed_req_id = seed_req.json()["id"]

        # 3. Upload a sample SRS text document containing candidates
        srs_text = (
            "Section 1. Functional Requirements\n"
            "FR-101: The SRSense System shall allow users to log in securely.\n"
            "NFR-02: The SRSense System shall process requests within 200 milliseconds.\n"
            "As a developer, I want to filter requirements by type, so that I can inspect workspace quality.\n"
            "The system must increase revenue and business market share.\n"
            "1. The database architecture schema shall use PostgreSQL 18.\n"
            "* Critical: The system must have urgent mandatory data backup capability."
        )

        doc_upload = await ac.post(
            f"/api/projects/{project_id}/documents/upload",
            files={"file": ("sample_srs.txt", srs_text.encode("utf-8"), "text/plain")},
            headers=headers_a,
        )
        assert doc_upload.status_code == 201
        doc_id = doc_upload.json()["id"]

        # 4. Extract Candidates
        ext_res = await ac.post(
            f"/api/projects/{project_id}/documents/{doc_id}/extract-candidates",
            headers=headers_a,
        )
        assert ext_res.status_code == 200
        ext_data = ext_res.json()
        assert ext_data["total_candidates"] >= 5
        candidates = ext_data["candidates"]

        # Verify candidate classification & IDs
        fr_cand = next((c for c in candidates if c["original_req_id"] == "FR-101"), None)
        assert fr_cand is not None
        assert fr_cand["type"] == "functional"

        nfr_cand = next((c for c in candidates if c["original_req_id"] == "NFR-02"), None)
        assert nfr_cand is not None
        assert nfr_cand["type"] == "non_functional"
        assert nfr_cand["is_duplicate"] is True  # Matches seed requirement
        assert nfr_cand["duplicate_of_id"] == seed_req_id
        assert nfr_cand["similarity_score"] >= 0.75

        user_cand = next((c for c in candidates if "As a developer" in c["description"]), None)
        assert user_cand is not None
        assert user_cand["type"] == "user"

        bus_cand = next((c for c in candidates if "increase revenue" in c["description"]), None)
        assert bus_cand is not None
        assert bus_cand["type"] == "business"

        sys_cand = next((c for c in candidates if "database architecture" in c["description"]), None)
        assert sys_cand is not None
        assert sys_cand["type"] == "system"

        crit_cand = next((c for c in candidates if "urgent mandatory" in c["description"]), None)
        assert crit_cand is not None
        assert crit_cand["priority"] in ("critical", "high")

        # 5. Security Check: User B blocked from extracting User A's document
        email_b = f"unauth_extractor_{int(time.time() * 1000)}@srsense.ai"
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
        headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

        unauth_ext = await ac.post(
            f"/api/projects/{project_id}/documents/{doc_id}/extract-candidates",
            headers=headers_b,
        )
        assert unauth_ext.status_code == 404

        # 6. Batch Acceptance Workflow
        batch_items = [
            {
                "title": fr_cand["title"],
                "description": fr_cand["description"],
                "type": fr_cand["type"],
                "priority": fr_cand["priority"],
                "status": "approved",
                "source_document_id": doc_id,
                "source_section": fr_cand["source_section"],
                "source_snippet": fr_cand["source_snippet"],
                "original_req_id": fr_cand["original_req_id"],
            },
            {
                "title": user_cand["title"],
                "description": user_cand["description"],
                "type": user_cand["type"],
                "priority": user_cand["priority"],
                "status": "in_review",
                "source_document_id": doc_id,
                "source_section": user_cand["source_section"],
                "source_snippet": user_cand["source_snippet"],
                "original_req_id": user_cand["original_req_id"],
            },
        ]

        batch_res = await ac.post(
            f"/api/projects/{project_id}/extraction/batch-accept",
            json={"items": batch_items},
            headers=headers_a,
        )
        assert batch_res.status_code == 201
        assert batch_res.json()["accepted_count"] == 2

        # Verify project requirement_count auto-sync (1 initial + 2 batch accepted = 3)
        proj_get = await ac.get(f"/api/projects/{project_id}", headers=headers_a)
        assert proj_get.status_code == 200
        assert proj_get.json()["requirement_count"] == 3
