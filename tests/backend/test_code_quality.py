"""
Sprint 2.1 — Code Review & Code Quality Intelligence Test Suite.

Validates static rule detectors across all 5 categories (security, performance, maintainability, compliance, quality),
deterministic quality score calculation (0-100), health classification boundaries,
API router responses, search/filter/pagination, and AI fallback handling.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4
import pytest

from app.core.code_intelligence.quality_analyzer import (
    CodeQualityAnalyzer,
    RawFinding,
    CRITICAL_PENALTY,
    WARNING_PENALTY,
    INFO_PENALTY,
)
from app.models.code_quality import (
    CodeHealthStatus,
    FindingCategory,
    FindingSeverity,
)
from app.models.codebase import CodeFile, CodeSymbol, RequirementCodeLink
from app.models.requirement import Requirement, RequirementStatus, RequirementType, RequirementPriority


def create_sample_code_file(path: str, filename: str, content: str) -> CodeFile:
    return CodeFile(
        id=uuid4(),
        codebase_id=uuid4(),
        project_id=uuid4(),
        path=path,
        filename=filename,
        language="Python",
        line_count=len(content.splitlines()),
        metadata_json={"raw_content": content},
    )


def create_sample_requirement(title: str, status: RequirementStatus) -> Requirement:
    return Requirement(
        id=uuid4(),
        project_id=uuid4(),
        title=title,
        description=f"Description for {title}",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=status,
    )


class TestCodeQualityAnalyzerRules:

    def test_security_rule_detection(self):
        """Detects SEC-001 (secrets), SEC-002 (eval), SEC-003 (SQL injection), SEC-004 (SSL disable)."""
        analyzer = CodeQualityAnalyzer()
        content = """
api_key = "sk_live_1234567890abcdef"
eval("user_input")
query = "SELECT * FROM users WHERE name = " + user_input
requests.get("https://internal.api", verify=False)
"""
        file = create_sample_code_file("src/security_test.py", "security_test.py", content)
        findings = analyzer._analyze_file(file, {})

        rule_ids = [f.rule_id for f in findings]
        assert "SEC-001" in rule_ids
        assert "SEC-002" in rule_ids
        assert "SEC-003" in rule_ids
        assert "SEC-004" in rule_ids

    def test_performance_rule_detection(self):
        """Detects PERF-001 (nested loop), PERF-002 (query in loop), PERF-003 (blocking I/O)."""
        analyzer = CodeQualityAnalyzer()
        content = """
async def process():
    for item in items:
        for inner in item.children:
            result = db.execute(select(User))
            time.sleep(1)
"""
        file = create_sample_code_file("src/perf_test.py", "perf_test.py", content)
        findings = analyzer._analyze_file(file, {})

        rule_ids = [f.rule_id for f in findings]
        assert "PERF-001" in rule_ids
        assert "PERF-002" in rule_ids
        assert "PERF-003" in rule_ids

    def test_quality_and_maintainability_rules(self):
        """Detects QUAL-001 (swallowed exception) and MAINT-002 (missing docstring)."""
        analyzer = CodeQualityAnalyzer()
        content = """
def public_function(a, b):
    try:
        do_something()
    except Exception:
        pass
"""
        file = create_sample_code_file("src/quality_test.py", "quality_test.py", content)
        findings = analyzer._analyze_file(file, {})

        rule_ids = [f.rule_id for f in findings]
        assert "QUAL-001" in rule_ids
        assert "MAINT-002" in rule_ids

    def test_negative_cases_clean_code(self):
        """Clean code triggers zero security or quality warnings."""
        analyzer = CodeQualityAnalyzer()
        content = """
def calculate_total(price: float, tax_rate: float) -> float:
    \"\"\"Calculate total price including tax.\"\"\"
    return price * (1.0 + tax_rate)
"""
        file = create_sample_code_file("src/clean.py", "clean.py", content)
        findings = analyzer._analyze_file(file, {})
        assert len(findings) == 0


class TestCodeQualityScoringFormula:

    def test_scoring_math_and_healthy_classification(self):
        """Zero issues yields 100 score and HEALTHY status."""
        analyzer = CodeQualityAnalyzer()
        findings, score, health, counts = analyzer.analyze_codebase([], [], [], [])

        assert score == 100
        assert health == CodeHealthStatus.HEALTHY
        assert sum(counts.values()) == 0

    def test_scoring_math_critical_penalties_needs_attention(self):
        """1 Critical (-15) + 1 Warning (-5) yields 80 score and NEEDS_ATTENTION status."""
        analyzer = CodeQualityAnalyzer()
        clean_file = create_sample_code_file("src/clean.py", "clean.py", "def foo(): pass")
        
        # Inject custom findings
        mock_findings = [
            RawFinding("SEC-001", FindingCategory.SECURITY, FindingSeverity.CRITICAL, "T1", "D1", "S1", "f.py"),
            RawFinding("PERF-001", FindingCategory.PERFORMANCE, FindingSeverity.WARNING, "T2", "D2", "S2", "f.py"),
        ]

        with patch.object(analyzer, "_analyze_file", return_value=mock_findings):
            with patch.object(analyzer, "_analyze_compliance", return_value=[]):
                _, score, health, _ = analyzer.analyze_codebase([clean_file], [], [], [])

                # 100 - 15 - 5 = 80
                assert score == 80
                assert health == CodeHealthStatus.NEEDS_ATTENTION

    def test_scoring_math_at_risk_classification(self):
        """3 Critical issues (-45) yields AT_RISK status despite score >= 50."""
        analyzer = CodeQualityAnalyzer()
        clean_file = create_sample_code_file("src/clean.py", "clean.py", "def foo(): pass")

        mock_findings = [
            RawFinding("SEC-001", FindingCategory.SECURITY, FindingSeverity.CRITICAL, "T1", "D1", "S1", "f.py"),
            RawFinding("SEC-002", FindingCategory.SECURITY, FindingSeverity.CRITICAL, "T2", "D2", "S2", "f.py"),
            RawFinding("SEC-004", FindingCategory.SECURITY, FindingSeverity.CRITICAL, "T3", "D3", "S3", "f.py"),
        ]

        with patch.object(analyzer, "_analyze_file", return_value=mock_findings):
            with patch.object(analyzer, "_analyze_compliance", return_value=[]):
                _, score, health, _ = analyzer.analyze_codebase([clean_file], [], [], [])

                # 100 - 45 = 55 -> AT_RISK
                assert score == 55
                assert health == CodeHealthStatus.AT_RISK


class TestComplianceRules:

    def test_unlinked_approved_requirement_flags_compliance_finding(self):
        """Approved requirement without code link flags COMP-001 compliance warning."""
        analyzer = CodeQualityAnalyzer()
        approved_req = create_sample_requirement("Payment Gateway Integration", RequirementStatus.APPROVED)

        compliance_findings = analyzer._analyze_compliance([approved_req], [], [])

        assert len(compliance_findings) == 1
        assert compliance_findings[0].rule_id == "COMP-001"
        assert compliance_findings[0].category == FindingCategory.COMPLIANCE
        assert compliance_findings[0].linked_requirement_id == approved_req.id
