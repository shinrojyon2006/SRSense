"""
Sprint 2.2 — AI Code Improvement Unit & Engine Tests.

Validates context bounding, requirement grounding, patch safety validation,
stale content detection, path traversal protection, and diff generation.
"""

from uuid import uuid4
import pytest

from app.core.code_intelligence.improvement_engine import (
    CodeImprovementEngine,
    PatchSafetyValidator,
)
from app.models.code_quality import CodeReviewFinding, FindingCategory, FindingSeverity
from app.models.codebase import CodeFile
from app.models.requirement import Requirement


def test_patch_safety_validator_path_traversal():
    assert PatchSafetyValidator.validate_path_safety("src/main.py") is True
    assert PatchSafetyValidator.validate_path_safety("app/services/db.py") is True
    assert PatchSafetyValidator.validate_path_safety("../etc/passwd") is False
    assert PatchSafetyValidator.validate_path_safety("..\\windows\\system32") is False
    assert PatchSafetyValidator.validate_path_safety("/absolute/path.py") is False


def test_patch_safety_validator_stale_content():
    content = "def process():\n    eval('dangerous()')\n"
    assert PatchSafetyValidator.check_stale_content(content, "eval('dangerous()')") is False
    # Stale: snippet no longer in content
    assert PatchSafetyValidator.check_stale_content(content, "eval('safe()')") is True


def test_patch_safety_validator_replacement():
    original = "api_key = \"sk_live_123456\""
    full_content = f"import os\n{original}\nprint('ok')\n"
    replacement = "api_key = os.getenv('API_KEY', '')"

    success, new_content, err = PatchSafetyValidator.apply_replacement(
        full_content, original, replacement
    )
    assert success is True
    assert err is None
    assert "os.getenv('API_KEY', '')" in new_content
    assert original not in new_content


@pytest.mark.asyncio
async def test_improvement_engine_insufficient_context():
    engine = CodeImprovementEngine()
    finding = CodeReviewFinding(
        id=uuid4(),
        report_id=uuid4(),
        file_path="empty.py",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.CRITICAL,
        title="Empty finding",
        description="Missing code snippet",
        rule_id="SEC-001",
        suggestion="Remove secret",
        snippet="",
    )

    context = engine.collect_bounded_context(finding=finding, file=None)
    assert context.is_sufficient is False
    assert "missing" in context.missing_reason.lower()

    proposal = await engine.generate_proposal(context)
    assert proposal.is_insufficient_context is True
    assert "INSUFFICIENT CONTEXT" in proposal.title
    assert proposal.confidence == 0.0


@pytest.mark.asyncio
async def test_improvement_engine_sql_injection_proposal():
    engine = CodeImprovementEngine()
    snippet = "query = \"SELECT * FROM users WHERE name = \" + name"
    finding = CodeReviewFinding(
        id=uuid4(),
        report_id=uuid4(),
        file_path="db.py",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.WARNING,
        title="SQL Injection",
        description="Raw SQL query built via string concatenation",
        rule_id="SEC-003",
        suggestion="Use parameterized query placeholders",
        snippet=snippet,
    )
    req = Requirement(
        id=uuid4(),
        title="Safe Order Querying",
        description="The system shall safely retrieve customer orders by order ID.",
    )

    context = engine.collect_bounded_context(finding=finding, linked_requirement=req)
    assert context.is_sufficient is True

    proposal = await engine.generate_proposal(context)
    assert proposal.is_insufficient_context is False
    assert "SEC-003" in proposal.title
    assert "parameterized" in proposal.recommendation.lower()
    assert proposal.patch_diff.startswith("--- a/db.py")
    assert len(proposal.affected_requirements) == 1
    assert proposal.affected_requirements[0]["requirement_id"] == str(req.id)


@pytest.mark.asyncio
async def test_improvement_engine_swallowed_exception():
    engine = CodeImprovementEngine()
    snippet = "except Exception:\n    pass"
    finding = CodeReviewFinding(
        id=uuid4(),
        report_id=uuid4(),
        file_path="main.py",
        category=FindingCategory.QUALITY,
        severity=FindingSeverity.WARNING,
        title="Swallowed Exception Handler",
        description="Exception caught and swallowed silently",
        rule_id="QUAL-001",
        suggestion="Log exception or re-raise",
        snippet=snippet,
    )

    context = engine.collect_bounded_context(finding=finding)
    proposal = await engine.generate_proposal(context)
    assert proposal.is_insufficient_context is False
    assert "logger.error" in proposal.proposed_code or "raise" in proposal.proposed_code
    assert "No linked requirement available." in proposal.uncertainty
