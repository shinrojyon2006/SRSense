"""
Sprint 2.4 — Requirement-Test Traceability Engine Unit Tests.

Validates evidence-backed matching (DIRECT, INFERRED) connecting requirements
to discovered code test artifacts.
"""

import uuid
import pytest
from app.core.code_intelligence.requirement_test_traceability import RequirementTestTraceabilityEngine
from app.models.requirement import Requirement, RequirementType
from app.models.codebase import RequirementCodeLink, CodeFile
from app.models.traceability import CodeTestArtifact, TestRelationshipType


def test_explicit_id_match():
    req_id = uuid.uuid4()
    test_id = uuid.uuid4()
    req = Requirement(id=req_id, original_req_id="REQ-101", title="User Login Authentication", description="User login", type=RequirementType.FUNCTIONAL)
    test = CodeTestArtifact(id=test_id, file_path="tests/test_auth.py", test_name="test_REQ_101_login_success", test_type="unit")

    matches = RequirementTestTraceabilityEngine.match_requirements_to_tests([req], [test], [], [])
    assert len(matches) == 1
    match = matches[0]
    assert match["requirement_id"] == req_id
    assert match["test_artifact_id"] == test_id
    assert match["relationship_type"] == TestRelationshipType.DIRECT.value
    assert match["confidence"] == 1.0
    assert match["evidence"]["signal"] == "EXPLICIT_ID_MATCH"


def test_inferred_code_file_link_match():
    req_id = uuid.uuid4()
    file_id = uuid.uuid4()
    project_id = uuid.uuid4()
    test_id = uuid.uuid4()
    req = Requirement(id=req_id, original_req_id="REQ-202", title="Export PDF Summary Report", description="PDF export", type=RequirementType.FUNCTIONAL)
    code_file = CodeFile(id=file_id, project_id=project_id, path="app/services/pdf_exporter.py", filename="pdf_exporter.py")
    code_link = RequirementCodeLink(id=uuid.uuid4(), project_id=project_id, requirement_id=req_id, file_id=file_id)
    test = CodeTestArtifact(id=test_id, file_path="tests/test_pdf_exporter.py", test_name="test_export_pdf_layout", test_type="unit")

    matches = RequirementTestTraceabilityEngine.match_requirements_to_tests([req], [test], [code_link], [code_file])
    assert len(matches) == 1
    match = matches[0]
    assert match["relationship_type"] == TestRelationshipType.INFERRED.value
    assert match["confidence"] >= 0.80
    assert "pdf_exporter.py" in match["evidence"]["explanation"] or "INFERRED" in match["evidence"]["signal"]


def test_no_match_returns_empty():
    req_id = uuid.uuid4()
    req = Requirement(id=req_id, original_req_id="REQ-303", title="Database Backup Task", description="Backup", type=RequirementType.SYSTEM)
    test = CodeTestArtifact(id=uuid.uuid4(), file_path="tests/test_stripe_payment.py", test_name="test_charge_credit_card", test_type="unit")

    matches = RequirementTestTraceabilityEngine.match_requirements_to_tests([req], [test], [], [])
    assert len(matches) == 0
