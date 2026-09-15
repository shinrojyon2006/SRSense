"""
Unit and API integration tests for Sprint 2.3 Before/After Code Improvement Evaluation.

Covers deterministic classification rules (IMPROVED, UNCHANGED, REGRESSED, PARTIALLY_IMPROVED, UNDETERMINED),
finding deltas, regression warnings, authorization, and API endpoint verification.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.models.code_quality import (
    CodeReviewReport,
    CodeReviewFinding,
    CodeHealthStatus,
    FindingCategory,
    FindingSeverity,
)
from app.models.code_improvement import CodeImprovementProposal, ImprovementStatus
from app.models.code_improvement_evaluation import (
    CodeImprovementEvaluation,
    EvaluationResultClassification,
)
from app.core.code_intelligence.evaluation_engine import EvaluationEngine
from app.services.code_improvement_evaluation_service import CodeImprovementEvaluationService


def create_mock_finding(rule_id="SEC-003", title="SQL Injection", category="security", severity="critical", line=10, file_path="app/db.py"):
    finding = MagicMock(spec=CodeReviewFinding)
    finding.id = uuid.uuid4()
    finding.rule_id = rule_id
    finding.title = title
    finding.description = "Mock finding description"
    finding.category = MagicMock(value=category)
    finding.category.__str__ = lambda self: category
    finding.severity = MagicMock(value=severity)
    finding.severity.__str__ = lambda self: severity
    finding.file_path = file_path
    finding.line_number = line
    finding.snippet = "mock code"
    return finding


def create_mock_report(score=70, health="needs_attention", findings=None):
    report = MagicMock(spec=CodeReviewReport)
    report.id = uuid.uuid4()
    report.overall_score = score
    report.health_status = MagicMock(value=health)
    report.health_status.__str__ = lambda self: health
    report.total_issues_count = len(findings) if findings else 0
    report.critical_count = sum(1 for f in (findings or []) if str(f.severity) == "critical")
    report.warning_count = sum(1 for f in (findings or []) if str(f.severity) == "warning")
    report.info_count = sum(1 for f in (findings or []) if str(f.severity) == "info")
    
    cat_counts = {}
    for f in (findings or []):
        cat = str(f.category)
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    report.category_counts = cat_counts
    report.findings = findings or []
    return report


def create_mock_proposal(status=ImprovementStatus.APPLIED, rule_id="SEC-003"):
    proposal = MagicMock(spec=CodeImprovementProposal)
    proposal.id = uuid.uuid4()
    proposal.project_id = uuid.uuid4()
    proposal.codebase_id = uuid.uuid4()
    proposal.finding_id = uuid.uuid4()
    proposal.linked_requirement_id = uuid.uuid4()
    proposal.rule_id = rule_id
    proposal.title = "Fix SQL Injection using parameterized queries"
    proposal.status = status
    proposal.affected_tests = [{"type": "unit", "description": "Run test_db.py"}]
    proposal.finding = None
    return proposal


class TestEvaluationEngine:
    """Test suite for deterministic outcome classification rules in EvaluationEngine."""

    def test_1_successful_security_improvement(self):
        """Test 1 — Security issue resolved: expected IMPROVED."""
        sec_finding = create_mock_finding(rule_id="SEC-003", category="security", severity="critical")
        before_report = create_mock_report(score=70, health="needs_attention", findings=[sec_finding])
        after_report = create_mock_report(score=90, health="healthy", findings=[])

        proposal = create_mock_proposal(rule_id="SEC-003")
        proposal.finding_id = sec_finding.id

        result = EvaluationEngine.compare_scans(before_report, after_report, proposal)

        assert result["result_classification"] == EvaluationResultClassification.IMPROVED
        assert result["score_delta"] == 20
        assert len(result["resolved_findings"]) == 1
        assert len(result["new_findings"]) == 0
        assert result["regression_detected"] is False

    def test_2_no_meaningful_change(self):
        """Test 2 — Same findings present: expected UNCHANGED."""
        maint_finding = create_mock_finding(rule_id="MAINT-001", category="maintainability", severity="warning")
        before_report = create_mock_report(score=80, health="healthy", findings=[maint_finding])
        after_report = create_mock_report(score=80, health="healthy", findings=[maint_finding])

        proposal = create_mock_proposal(rule_id="MAINT-001")
        proposal.finding_id = maint_finding.id

        result = EvaluationEngine.compare_scans(before_report, after_report, proposal)

        assert result["result_classification"] == EvaluationResultClassification.UNCHANGED
        assert result["score_delta"] == 0
        assert len(result["resolved_findings"]) == 0
        assert len(result["new_findings"]) == 0

    def test_3_improvement_introduces_new_critical_issue(self):
        """Test 3 — New critical issue introduced: expected REGRESSED + warning flag."""
        warning_finding = create_mock_finding(rule_id="MAINT-001", severity="warning", line=5)
        new_critical_finding = create_mock_finding(rule_id="SEC-002", category="security", severity="critical", line=25)

        before_report = create_mock_report(score=85, health="healthy", findings=[warning_finding])
        after_report = create_mock_report(score=65, health="at_risk", findings=[warning_finding, new_critical_finding])

        proposal = create_mock_proposal(rule_id="MAINT-001")

        result = EvaluationEngine.compare_scans(before_report, after_report, proposal)

        assert result["result_classification"] == EvaluationResultClassification.REGRESSED
        assert result["regression_detected"] is True
        assert len(result["regression_details"]) > 0
        assert "REGRESSION DETECTED" in result["regression_details"][0]

    def test_4_mixed_result_partially_improved(self):
        """Test 4 — Target resolved but secondary info finding introduced: expected PARTIALLY_IMPROVED."""
        target_finding = create_mock_finding(rule_id="QUAL-001", category="quality", severity="warning", line=10)
        new_info_finding = create_mock_finding(rule_id="QUAL-003", category="quality", severity="info", line=40)

        before_report = create_mock_report(score=80, health="healthy", findings=[target_finding])
        after_report = create_mock_report(score=82, health="healthy", findings=[new_info_finding])

        proposal = create_mock_proposal(rule_id="QUAL-001")
        proposal.finding_id = target_finding.id

        result = EvaluationEngine.compare_scans(before_report, after_report, proposal)

        assert result["result_classification"] == EvaluationResultClassification.PARTIALLY_IMPROVED
        assert len(result["resolved_findings"]) == 1
        assert len(result["new_findings"]) == 1

    def test_5_insufficient_evidence_undetermined(self):
        """Test 5 — Missing scan report evidence: expected UNDETERMINED."""
        proposal = create_mock_proposal()
        result = EvaluationEngine.compare_scans(None, None, proposal)

        assert result["result_classification"] == EvaluationResultClassification.UNDETERMINED
        assert result["test_impact"]["execution_status"] == "NOT EXECUTED"


class TestEvaluationService:
    """Test suite for evaluation service workflow."""

    @pytest.mark.asyncio
    async def test_evaluate_non_applied_proposal_raises_error(self):
        """Evaluating proposal that is not APPLIED must raise error."""
        from unittest.mock import AsyncMock
        db_mock = MagicMock()
        service = CodeImprovementEvaluationService(db_mock)
        user_mock = MagicMock()

        unapplied_proposal = create_mock_proposal(status=ImprovementStatus.PROPOSED)
        service._verify_ownership = AsyncMock(return_value=None)
        service.proposal_repo.get_by_id = AsyncMock(return_value=unapplied_proposal)

        with pytest.raises(Exception):
            await service.evaluate_improvement(user_mock, unapplied_proposal.project_id, unapplied_proposal.id)
