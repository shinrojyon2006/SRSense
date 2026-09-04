"""
Integration and Service Tests for Sprint 2.0 Codebase Service and API.

Verifies:
- ZIP upload and indexing of multi-language repository.
- Summary metrics and language breakdown.
- Files listing, detail, and symbol search.
- Dependencies extraction.
- Requirement ↔ Code linking foundation (create, list, delete).
- Project ownership authorization and isolation.
"""

import io
import time
import zipfile
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


def create_sample_zip() -> bytes:
    """Create in-memory ZIP archive with multi-language sample files."""
    files = {
        "backend/main.py": """
import os
from fastapi import APIRouter

router = APIRouter()

class OrderManager:
    def process_order(self, order_id: int):
        return {"status": "processed"}

@router.get("/api/orders/{order_id}")
def get_order(order_id: int):
    return {"id": order_id}
""",
        "frontend/src/App.tsx": """
import React, { useState } from 'react';

export interface AppProps {
    title: string;
}

export const App: React.FC<AppProps> = ({ title }) => {
    return <h1>{title}</h1>;
};
""",
        "db/schema.sql": """
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    amount NUMERIC(10, 2)
);
""",
        "README.md": "# Sample Multi-language Project",
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_codebase_ingestion_and_indexing_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register User and Create Project
        unique_email = f"coder_{int(time.time() * 1000)}@srsense.ai"
        reg_res = await ac.post(
            "/api/auth/register",
            json={
                "name": "Dev User",
                "email": unique_email,
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        proj_res = await ac.post(
            "/api/projects",
            json={
                "title": "E-Commerce System",
                "description": "Core platform services",
                "status": "active",
            },
            headers=headers,
        )
        assert proj_res.status_code == 201
        project_id = proj_res.json()["id"]

        # Create a requirement
        req_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={
                "title": "Order Processing SLA",
                "description": "The system shall process orders within 200 milliseconds.",
                "type": "non_functional",
                "priority": "high",
            },
            headers=headers,
        )
        assert req_res.status_code == 201
        req_id = req_res.json()["id"]

        # 2. Upload Codebase ZIP
        zip_bytes = create_sample_zip()
        upload_res = await ac.post(
            f"/api/projects/{project_id}/codebase/upload",
            files={"file": ("ecommerce.zip", zip_bytes, "application/zip")},
            headers=headers,
        )
        assert upload_res.status_code == 201
        summary = upload_res.json()
        assert summary["status"] == "indexed"
        assert summary["total_files"] == 4
        assert summary["total_classes"] >= 1
        assert summary["total_functions"] >= 1
        assert "Python" in summary["languages_summary"]
        assert "TypeScript" in summary["languages_summary"]
        assert "SQL" in summary["languages_summary"]

        # 3. Get Codebase Summary
        sum_res = await ac.get(
            f"/api/projects/{project_id}/codebase/",
            headers=headers,
        )
        assert sum_res.status_code == 200
        assert sum_res.json()["total_files"] == 4

        # 4. List Code Files
        files_res = await ac.get(
            f"/api/projects/{project_id}/codebase/files",
            headers=headers,
        )
        assert files_res.status_code == 200
        files = files_res.json()
        assert len(files) == 4
        py_file = next(f for f in files if f["filename"] == "main.py")
        assert py_file["language"] == "Python"
        assert py_file["confidence"] == "High"

        # 5. Get File Detail
        file_detail_res = await ac.get(
            f"/api/projects/{project_id}/codebase/files/{py_file['id']}",
            headers=headers,
        )
        assert file_detail_res.status_code == 200
        detail = file_detail_res.json()
        sym_names = [s["symbol_name"] for s in detail["symbols"]]
        assert "OrderManager" in sym_names
        assert "GET /api/orders/{order_id}" in sym_names

        # 6. Search Symbols
        search_res = await ac.get(
            f"/api/projects/{project_id}/codebase/symbols?q=Order",
            headers=headers,
        )
        assert search_res.status_code == 200
        found_syms = search_res.json()
        assert len(found_syms) >= 1
        assert any("OrderManager" in s["symbol_name"] for s in found_syms)

        # 7. Get Dependencies
        dep_res = await ac.get(
            f"/api/projects/{project_id}/codebase/dependencies",
            headers=headers,
        )
        assert dep_res.status_code == 200

        # 8. Create Requirement ↔ Code Link
        link_res = await ac.post(
            f"/api/projects/{project_id}/codebase/links",
            json={
                "requirement_id": req_id,
                "file_id": py_file["id"],
                "link_type": "explicit_manual",
                "notes": "Order manager endpoint implementation",
            },
            headers=headers,
        )
        assert link_res.status_code == 201
        link_data = link_res.json()
        assert link_data["requirement_id"] == req_id
        assert link_data["file_path"] == "backend/main.py"
        link_id = link_data["id"]

        # 9. List Requirement ↔ Code Links
        list_links_res = await ac.get(
            f"/api/projects/{project_id}/codebase/links",
            headers=headers,
        )
        assert list_links_res.status_code == 200
        links_list = list_links_res.json()
        assert len(links_list) == 1
        assert links_list[0]["id"] == link_id

        # 10. Delete Link
        del_link_res = await ac.delete(
            f"/api/projects/{project_id}/codebase/links/{link_id}",
            headers=headers,
        )
        assert del_link_res.status_code == 204

        # Verify link is removed
        list_links_after = await ac.get(
            f"/api/projects/{project_id}/codebase/links",
            headers=headers,
        )
        assert len(list_links_after.json()) == 0


@pytest.mark.asyncio
async def test_codebase_project_authorization_isolation():
    """User B cannot access or link User A's codebase."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register User A
        reg_a = await ac.post(
            "/api/auth/register",
            json={
                "name": "User A",
                "email": f"user_a_{int(time.time() * 1000)}@srsense.ai",
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        token_a = reg_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Register User B
        reg_b = await ac.post(
            "/api/auth/register",
            json={
                "name": "User B",
                "email": f"user_b_{int(time.time() * 1000)}@srsense.ai",
                "password": "Password123!",
                "password_confirmation": "Password123!",
                "role": "developer",
            },
        )
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User A creates Project A
        proj_a = await ac.post(
            "/api/projects",
            json={
                "title": "Project A Private",
                "description": "User A private repo",
                "status": "active",
            },
            headers=headers_a,
        )
        project_a_id = proj_a.json()["id"]

        # User A uploads codebase
        zip_bytes = create_sample_zip()
        await ac.post(
            f"/api/projects/{project_a_id}/codebase/upload",
            files={"file": ("repo_a.zip", zip_bytes, "application/zip")},
            headers=headers_a,
        )

        # User B attempts to access Project A codebase -> must return 403 Forbidden
        forbidden_res = await ac.get(
            f"/api/projects/{project_a_id}/codebase/",
            headers=headers_b,
        )
        assert forbidden_res.status_code == 403
