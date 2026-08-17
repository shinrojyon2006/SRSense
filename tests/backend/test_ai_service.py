"""
Backend AI service & SRS Exporter test suite.

Tests AI ambiguity detection, quality scoring, EARS syntax formatting, type-aware analysis, and SRS export.
"""

import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.ai.heuristics_provider import HeuristicsAIProvider


@pytest.mark.asyncio
async def test_type_aware_ai_heuristic_analysis_regression():
    """Test type-aware quality scoring, title isolation, and non-functional metric recognition."""
    provider = HeuristicsAIProvider()

    # Regression Case 1: Title "Fast System", Description "The SRSense System shall respond within 200 milliseconds."
    res1 = await provider.analyze_requirement(
        title="Fast System",
        description="The SRSense System shall respond within 200 milliseconds.",
        req_type="non_functional",
    )
    assert res1.quality_score >= 90
    assert len(res1.ambiguity_tags) == 0  # "Fast" in title must NOT be flagged
    assert not any("brief" in c.lower() for c in res1.missing_criteria)
    assert not any("trigger" in c.lower() for c in res1.missing_criteria)

    # Regression Case 2: Vague Non-Functional vs Measurable Non-Functional
    res2_vague = await provider.analyze_requirement(
        title="System Speed",
        description="The system should be fast and scalable.",
        req_type="non_functional",
    )
    assert res2_vague.quality_score < 75
    assert len(res2_vague.ambiguity_tags) >= 2

    # Regression Case 3: User Story Format Validation
    res3_valid = await provider.analyze_requirement(
        title="Filter Requirements",
        description="As a developer, I want to filter requirements by type, so that I can analyze quality quickly.",
        req_type="user",
    )
    assert res3_valid.quality_score >= 85

    res3_invalid = await provider.analyze_requirement(
        title="Filter Requirements",
        description="Developers need to filter requirements by type in the grid.",
        req_type="user",
    )
    assert any("user story" in c.lower() for c in res3_invalid.missing_criteria)

    # Regression Case 4: Business Objective Requirement
    res4_bus = await provider.analyze_requirement(
        title="Checkout Conversion",
        description="The project shall reduce customer checkout abandonment rates by 15%.",
        req_type="business",
    )
    assert res4_bus.quality_score >= 85


@pytest.mark.asyncio
async def test_ears_improvement_grammar_and_scenarios():
    """Test EARS improvement generation across 4 required scenarios ensuring clean grammar."""
    provider = HeuristicsAIProvider()

    # 1. Vague requirement improvement
    res1 = await provider.suggest_improvement(
        title="Speed and Usability",
        description="The system should be fast and user-friendly.",
        req_type="non_functional",
    )
    assert "The SRSense System shall the system" not in res1.improved_description
    assert "should be respond" not in res1.improved_description
    assert res1.improved_description == (
        "The SRSense System shall respond within 200 milliseconds and "
        "require no more than 3 user interactions."
    )

    # 2. Already well-formed requirement
    res2 = await provider.suggest_improvement(
        title="Processing Time",
        description="The SRSense System shall process requests within 100 milliseconds.",
        req_type="functional",
    )
    assert res2.improved_description == (
        "The SRSense System shall process requests within 100 milliseconds."
    )

    # 3. Requirement with measurable performance constraints
    res3 = await provider.suggest_improvement(
        title="Auth Latency",
        description="The system shall authenticate users within 500ms.",
        req_type="functional",
    )
    assert res3.improved_description == (
        "The SRSense System shall authenticate users within 500ms."
    )

    # 4. Requirement containing multiple vague terms
    res4 = await provider.suggest_improvement(
        title="Platform Quality",
        description="The application must be fast, seamless, and scalable.",
        req_type="non_functional",
    )
    assert "The SRSense System shall" in res4.improved_description
    assert "respond within 200 milliseconds" in res4.improved_description
    assert "without manual user intervention" in res4.improved_description
    assert "support up to 10,000 concurrent requests" in res4.improved_description
    assert "application must be" not in res4.improved_description


@pytest.mark.asyncio
async def test_ai_analysis_and_improvement_flow():
    """Test AI analysis, quality score calculation, EARS improvement, and SRS document export."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Register user & project
        unique_email = f"ai_tester_{int(time.time() * 1000)}@srsense.ai"
        reg_res = await ac.post(
            "/api/auth/register",
            json={
                "name": "AI Tester",
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
                "title": "E-Commerce SRS System",
                "description": "AI-Assisted Requirements Test",
                "status": "active",
            },
            headers=headers,
        )
        assert proj_res.status_code == 201
        project_id = proj_res.json()["id"]

        # 2. Create requirement with intentionally vague text
        req_res = await ac.post(
            f"/api/projects/{project_id}/requirements",
            json={
                "title": "Payment Checkout Speed",
                "description": "The checkout process should be fast and user-friendly for all customers.",
                "type": "non_functional",
                "priority": "high",
            },
            headers=headers,
        )
        assert req_res.status_code == 201
        req_id = req_res.json()["id"]

        # 3. Analyze Requirement
        an_res = await ac.post(
            f"/api/projects/{project_id}/requirements/{req_id}/analyze",
            headers=headers,
        )
        assert an_res.status_code == 200
        an_data = an_res.json()
        assert "quality_score" in an_data
        assert an_data["quality_score"] < 100  # Penalized for "fast" and "user-friendly"
        assert len(an_data["analysis_result"]["ambiguity_tags"]) >= 2

        # 4. Improve Requirement via EARS
        imp_res = await ac.post(
            f"/api/projects/{project_id}/requirements/{req_id}/improve",
            headers=headers,
        )
        assert imp_res.status_code == 200
        imp_data = imp_res.json()
        assert "shall" in imp_data["improved_description"].lower()
        assert "respond within 200 milliseconds" in imp_data["improved_description"]

        # 5. Ephemeral Draft Analysis
        draft_res = await ac.post(
            "/api/ai/analyze-draft",
            json={
                "title": "Draft Test",
                "description": "The system shall process requests within 100 milliseconds.",
                "type": "functional",
            },
            headers=headers,
        )
        assert draft_res.status_code == 200
        assert draft_res.json()["quality_score"] >= 85

        # 6. SRS Document Export (Markdown)
        export_md = await ac.get(
            f"/api/projects/{project_id}/export?format=markdown", headers=headers
        )
        assert export_md.status_code == 200
        assert "Software Requirements Specification" in export_md.json()["content"]

        # 7. SRS Document Export (JSON)
        export_json = await ac.get(
            f"/api/projects/{project_id}/export?format=json", headers=headers
        )
        assert export_json.status_code == 200
        assert export_json.json()["total_requirements"] == 1
