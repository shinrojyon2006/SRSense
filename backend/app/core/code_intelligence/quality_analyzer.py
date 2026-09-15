"""
Sprint 2.1 — Code Review & Code Quality Intelligence Static Analyzer & Scoring Engine.

Implements rule detectors (Security, Performance, Maintainability, Compliance, Quality),
deterministic quality score calculation (0-100), health classification,
and grounded AI explanation generation.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.core.ai.factory import get_ai_provider
from app.models.code_quality import CodeHealthStatus, FindingCategory, FindingSeverity
from app.models.codebase import CodeFile, CodeSymbol, RequirementCodeLink
from app.models.requirement import Requirement, RequirementStatus

logger = logging.getLogger(__name__)

# Severity Deductions
CRITICAL_PENALTY = 15
WARNING_PENALTY = 5
INFO_PENALTY = 1


class RawFinding:
    """In-memory structure representing a discovered code quality finding."""

    def __init__(
        self,
        rule_id: str,
        category: FindingCategory,
        severity: FindingSeverity,
        title: str,
        description: str,
        suggestion: str,
        file_path: str,
        file_id: Optional[UUID] = None,
        line_number: Optional[int] = None,
        snippet: Optional[str] = None,
        linked_requirement_id: Optional[UUID] = None,
    ):
        self.rule_id = rule_id
        self.category = category
        self.severity = severity
        self.title = title
        self.description = description
        self.suggestion = suggestion
        self.file_path = file_path
        self.file_id = file_id
        self.line_number = line_number
        self.snippet = snippet
        self.linked_requirement_id = linked_requirement_id
        self.ai_explanation: Optional[str] = None


class CodeQualityAnalyzer:
    """Multi-language static code quality analysis and scoring engine."""

    def analyze_codebase(
        self,
        files: List[CodeFile],
        symbols: List[CodeSymbol],
        requirements: List[Requirement],
        code_links: List[RequirementCodeLink],
    ) -> Tuple[List[RawFinding], int, CodeHealthStatus, Dict[str, int]]:
        """Run all static detectors over codebase files, compute score, and classify health."""
        findings: List[RawFinding] = []

        req_map = {r.id: r for r in requirements}
        req_by_title_id = {}
        for r in requirements:
            req_by_title_id[r.title.lower()] = r
            if r.original_req_id:
                req_by_title_id[r.original_req_id.lower()] = r

        linked_req_ids = {link.requirement_id for link in code_links}

        # 1. File-level & Line-level Static Analysis
        for file in files:
            file_findings = self._analyze_file(file, req_by_title_id)
            findings.extend(file_findings)

        # 2. Compliance Rules (Requirement Coverage & Specs)
        compliance_findings = self._analyze_compliance(requirements, code_links, files)
        findings.extend(compliance_findings)

        # 3. Deterministic Quality Score Math
        critical_count = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
        warning_count = sum(1 for f in findings if f.severity == FindingSeverity.WARNING)
        info_count = sum(1 for f in findings if f.severity == FindingSeverity.INFO)

        total_penalties = (
            (critical_count * CRITICAL_PENALTY)
            + (warning_count * WARNING_PENALTY)
            + (info_count * INFO_PENALTY)
        )
        overall_score = max(0, min(100, 100 - total_penalties))

        # Health Classification Boundaries
        if overall_score >= 85 and critical_count == 0:
            health_status = CodeHealthStatus.HEALTHY
        elif overall_score >= 60 and critical_count <= 2:
            health_status = CodeHealthStatus.NEEDS_ATTENTION
        else:
            health_status = CodeHealthStatus.AT_RISK

        category_counts = {
            "security": sum(1 for f in findings if f.category == FindingCategory.SECURITY),
            "performance": sum(1 for f in findings if f.category == FindingCategory.PERFORMANCE),
            "maintainability": sum(1 for f in findings if f.category == FindingCategory.MAINTAINABILITY),
            "compliance": sum(1 for f in findings if f.category == FindingCategory.COMPLIANCE),
            "quality": sum(1 for f in findings if f.category == FindingCategory.QUALITY),
        }

        return findings, overall_score, health_status, category_counts

    def _analyze_file(
        self, file: CodeFile, req_map: Dict[str, Requirement]
    ) -> List[RawFinding]:
        findings: List[RawFinding] = []
        metadata = file.metadata_json or {}
        raw_content = metadata.get("raw_content", "")
        if not raw_content:
            return findings

        lines = raw_content.splitlines()
        lang = (file.language or "").lower()

        # State tracking for multi-line checks
        in_function = False
        func_start_line = 0
        func_line_count = 0
        indent_stack = []

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue

            # --- SECURITY RULES ---
            # SEC-001: Hardcoded Secrets / API Keys
            if re.search(
                r"""\b(api_key|secret_key|passwd|password|access_token|bearer_token|jwt_secret)\b\s*[:=]\s*["'][A-Za-z0-9_\-\.]{8,}["']""",
                line,
                re.IGNORECASE,
            ) and not any(env in line.lower() for env in ["os.getenv", "process.env", "config", "env("]):
                findings.append(
                    RawFinding(
                        rule_id="SEC-001",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.CRITICAL,
                        title="Hardcoded Secret / Credentials Detected",
                        description=f"Potential plain-text secret or credentials assigned directly in {file.filename}.",
                        suggestion="Extract hardcoded secrets into environment variables (.env) or a secure secrets vault.",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

            # SEC-002: Dynamic Code Execution (eval, exec, Function)
            if re.search(r"\b(eval|exec)\s*\(|new\s+Function\s*\(", line):
                findings.append(
                    RawFinding(
                        rule_id="SEC-002",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.CRITICAL,
                        title="Unsafe Dynamic Code Execution",
                        description="Use of eval(), exec(), or dynamic Function constructor can lead to arbitrary code execution vulnerabilities.",
                        suggestion="Refactor code to avoid dynamic code evaluation; use structured AST parsers or explicit lookup tables.",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

            # SEC-003: SQL Injection String Concatenation
            if re.search(
                r"""\b(select|insert|update|delete)\b.*(\+|%|\.format|f["'])""",
                line,
                re.IGNORECASE,
            ):
                findings.append(
                    RawFinding(
                        rule_id="SEC-003",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.WARNING,
                        title="Potential SQL Injection String Concatenation",
                        description="Raw SQL query built via string formatting or concatenation rather than parameterized query bindings.",
                        suggestion="Use parameterized query placeholders ($1, %s, :param) or an ORM query builder to prevent SQL injection.",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

            # SEC-004: Disabled SSL/TLS Verification
            if re.search(
                r"\b(verify\s*=\s*False|rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*0|check_hostname\s*=\s*False)\b",
                line,
                re.IGNORECASE,
            ):
                findings.append(
                    RawFinding(
                        rule_id="SEC-004",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.CRITICAL,
                        title="Disabled SSL/TLS Certificate Verification",
                        description="Disabling TLS certificate verification exposes network traffic to Man-in-the-Middle (MitM) attacks.",
                        suggestion="Enable SSL certificate verification (`verify=True` / `rejectUnauthorized: true`) in production environments.",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

            # SEC-005: Unauthenticated Sensitive Route Patterns
            if any(path in file.path.lower() for path in ["admin", "payment", "user"]) and re.search(r"@\w+\.(post|put|delete)\(", line):
                if i > 1 and not any(auth in lines[i - 2].lower() for auth in ["depends", "auth", "get_current_user", "protect", "jwt"]):
                    findings.append(
                        RawFinding(
                            rule_id="SEC-005",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.WARNING,
                            title="Potentially Unauthenticated Sensitive Route",
                            description=f"Sensitive endpoint defined in {file.filename} without explicit authentication dependency.",
                            suggestion="Add authentication middleware or dependency injection (`get_current_user`) to safeguard endpoint.",
                            file_path=file.path,
                            file_id=file.id,
                            line_number=i,
                            snippet=stripped[:120],
                        )
                    )

            # --- PERFORMANCE RULES ---
            # PERF-001: Nested Loops
            if re.search(r"\b(for|while)\b", line) and re.search(r"^\s{8,}\b(for|while)\b", line):
                findings.append(
                    RawFinding(
                        rule_id="PERF-001",
                        category=FindingCategory.PERFORMANCE,
                        severity=FindingSeverity.WARNING,
                        title="Nested Loop with O(n²) Complexity Risk",
                        description="Deeply nested iteration loops detected. Can cause execution latency on large datasets.",
                        suggestion="Use a hash map / dictionary lookup or database set join to reduce algorithmic time complexity to O(n).",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

            # PERF-002: Query inside Loop (N+1 Risk)
            indent_len = len(line) - len(line.lstrip())
            if indent_len >= 8 and any(q in line for q in ["db.execute", "session.execute", "db.query", "select(", "fetch("]):
                findings.append(
                    RawFinding(
                        rule_id="PERF-002",
                        category=FindingCategory.PERFORMANCE,
                        severity=FindingSeverity.WARNING,
                        title="Potential N+1 Database Query in Loop",
                        description="Database query executed inside iteration loop, leading to N+1 network roundtrips.",
                        suggestion="Batch query identifiers or use eagerness loading (`joinedload` / SQL `IN (...)` clause) outside the loop.",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

            # PERF-003: Blocking I/O inside Async Function
            if re.search(r"\b(time\.sleep|requests\.(get|post)|urllib\.request|fs\.readFileSync)\b", line):
                findings.append(
                    RawFinding(
                        rule_id="PERF-003",
                        category=FindingCategory.PERFORMANCE,
                        severity=FindingSeverity.CRITICAL,
                        title="Blocking Synchronous I/O Call",
                        description="Synchronous blocking I/O operation stalls event loop dispatching.",
                        suggestion="Replace blocking calls with async equivalents (`asyncio.sleep`, `httpx.AsyncClient`, `aiofiles`).",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

            # PERF-004: Unmemoized Heavy Computation in UI Render
            if ("tsx" in lang or "jsx" in lang or "react" in lang) and re.search(r"\b(\.filter\(|\.map\(|\.sort\()\b.*\.filter\(", line):
                findings.append(
                    RawFinding(
                        rule_id="PERF-004",
                        category=FindingCategory.PERFORMANCE,
                        severity=FindingSeverity.INFO,
                        title="Unmemoized Data Transformation in Component",
                        description="Chained array transformations executed directly in render cycle without memoization.",
                        suggestion="Wrap complex transformations in `useMemo()` to prevent unnecessary recalculations on re-render.",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

            # --- MAINTAINABILITY RULES ---
            # MAINT-002: Missing Docstrings on public def/class
            if re.search(r"^\s*(def|class)\s+[A-Za-z0-9_]+\(", line) and not line.strip().startswith("def _"):
                if i < len(lines) and '"""' not in lines[i] and "'''" not in lines[i]:
                    findings.append(
                        RawFinding(
                            rule_id="MAINT-002",
                            category=FindingCategory.MAINTAINABILITY,
                            severity=FindingSeverity.INFO,
                            title="Missing Public Interface Documentation",
                            description=f"Public class or function '{stripped[:40]}' lacks a descriptive docstring.",
                            suggestion="Add a standard docstring describing function intent, parameters, and return value.",
                            file_path=file.path,
                            file_id=file.id,
                            line_number=i,
                            snippet=stripped[:120],
                        )
                    )

            # MAINT-003: Deep Nesting (> 4 levels of indentation)
            indent_level = len(line) - len(line.lstrip())
            if indent_level >= 16 and re.search(r"\b(if|for|while|try)\b", line):
                findings.append(
                    RawFinding(
                        rule_id="MAINT-003",
                        category=FindingCategory.MAINTAINABILITY,
                        severity=FindingSeverity.INFO,
                        title="Excessive Block Indentation Nesting",
                        description=f"Indentation depth exceeds 4 levels ({indent_level // 4} levels deep). Increases cognitive complexity.",
                        suggestion="Use guard clauses (early returns) or extract nested logic into dedicated helper functions.",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

            # --- QUALITY RULES ---
            # QUAL-001: Swallowed Exceptions
            if re.search(r"\b(except\s*:|except\s+\w+\s*:|catch\s*\([^)]*\)\s*\{)\s*pass\b|\bexcept\s*:.*pass\b", line) or (
                stripped in ["pass", "{", "}"] and i > 1 and "except" in lines[i - 2].lower()
            ):
                findings.append(
                    RawFinding(
                        rule_id="QUAL-001",
                        category=FindingCategory.QUALITY,
                        severity=FindingSeverity.WARNING,
                        title="Swallowed Exception Handler",
                        description="Exception caught and swallowed silently without logging or error recovery.",
                        suggestion="Log the exception or re-raise an appropriate application domain exception.",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

            # QUAL-003: Missing Python Type Annotations
            if "python" in lang and re.search(r"^\s*def\s+[A-Za-z0-9_]+\([^)]*\)\s*:", line) and "->" not in line:
                findings.append(
                    RawFinding(
                        rule_id="QUAL-003",
                        category=FindingCategory.QUALITY,
                        severity=FindingSeverity.INFO,
                        title="Missing Function Type Annotations",
                        description="Python function definition lacks parameter or return type annotations.",
                        suggestion="Add type hints (`def func(a: int) -> str:`) to enforce static type safety.",
                        file_path=file.path,
                        file_id=file.id,
                        line_number=i,
                        snippet=stripped[:120],
                    )
                )

        # MAINT-001: Function length check via line count
        if file.line_count > 300:
            findings.append(
                RawFinding(
                    rule_id="MAINT-001",
                    category=FindingCategory.MAINTAINABILITY,
                    severity=FindingSeverity.WARNING,
                    title="Excessive File / Module Length",
                    description=f"File {file.filename} contains {file.line_count} lines (> 300 line threshold).",
                    suggestion="Split large file into modular sub-modules with single responsibility.",
                    file_path=file.path,
                    file_id=file.id,
                    line_number=1,
                    snippet=f"File length: {file.line_count} lines",
                )
            )

        return findings

    def _analyze_compliance(
        self,
        requirements: List[Requirement],
        code_links: List[RequirementCodeLink],
        files: List[CodeFile],
    ) -> List[RawFinding]:
        findings: List[RawFinding] = []
        linked_req_ids = {link.requirement_id for link in code_links}

        # COMP-001: Approved Requirements without linked code
        approved_reqs = [r for r in requirements if r.status == RequirementStatus.APPROVED]
        for req in approved_reqs:
            if req.id not in linked_req_ids:
                findings.append(
                    RawFinding(
                        rule_id="COMP-001",
                        category=FindingCategory.COMPLIANCE,
                        severity=FindingSeverity.WARNING,
                        title=f"Approved Requirement Lacks Code Implementation Link: '{req.title}'",
                        description=f"Requirement '{req.title}' is APPROVED but has no mapped source code files.",
                        suggestion="Use the Requirement-Code Link workspace to attach the implementation file or symbol.",
                        file_path="[Requirement Compliance Matrix]",
                        file_id=None,
                        line_number=None,
                        snippet=f"Requirement ID: {req.original_req_id or str(req.id)[:8]}",
                        linked_requirement_id=req.id,
                    )
                )

        return findings

    async def generate_ai_explanation(
        self, finding: RawFinding, requirement: Optional[Requirement] = None
    ) -> str:
        """Generate grounded AI explanation & contextual fix example for a finding."""
        ai = get_ai_provider()
        prompt = (
            f"Rule ID: {finding.rule_id}\n"
            f"Title: {finding.title}\n"
            f"Severity: {finding.severity.value}\n"
            f"Category: {finding.category.value}\n"
            f"File: {finding.file_path} (Line {finding.line_number or 1})\n"
            f"Code Snippet: {finding.snippet or 'N/A'}\n"
            f"Description: {finding.description}\n"
            f"Suggestion: {finding.suggestion}\n"
        )
        if requirement:
            prompt += f"Linked Requirement: '{requirement.title}' - {requirement.description}\n"

        prompt += "\nExplain the root cause in 2 sentences, provide a clean remediation code example, and note any requirement compliance impact."

        try:
            explanation = await ai.analyze_requirement(prompt)
            if explanation:
                return explanation
        except Exception as e:
            logger.warning("AI explanation provider error: %s", e)

        # Grounded Fallback
        req_note = f" Relates to requirement '{requirement.title}'." if requirement else ""
        return (
            f"Root Cause: Rule [{finding.rule_id}] triggered in {finding.file_path}. {finding.description}{req_note}\n"
            f"Remediation Suggestion: {finding.suggestion}"
        )
