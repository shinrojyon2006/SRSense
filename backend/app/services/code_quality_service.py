"""
Sprint 2.1 — Code Quality & Code Review Service layer.
Handles analysis execution, persistence, score computation, and findings querying.
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.code_intelligence.quality_analyzer import CodeQualityAnalyzer, RawFinding
from app.models.code_quality import (
    CodeHealthStatus,
    CodeReviewFinding,
    CodeReviewReport,
    FindingCategory,
    FindingSeverity,
)
from app.models.codebase import Codebase, CodeFile, CodeSymbol, RequirementCodeLink
from app.models.user import User
from app.repositories.code_quality_repository import CodeQualityRepository
from app.repositories.codebase_repository import CodebaseRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_repository import RequirementRepository
from app.schemas.code_quality import (
    CodeReviewFindingResponse,
    CodeReviewFindingsListResponse,
    CodeReviewReportResponse,
)

logger = logging.getLogger(__name__)


class CodeQualityService:
    """Service layer managing code review scans and finding queries."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.codebase_repo = CodebaseRepository(db)
        self.req_repo = RequirementRepository(db)
        self.quality_repo = CodeQualityRepository(db)
        self.analyzer = CodeQualityAnalyzer()

    async def _verify_ownership(self, project_id: UUID, user: User):
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        print(f"DEBUG OWNERSHIP: project.owner_id={project.owner_id} ({type(project.owner_id)}), user.id={user.id} ({type(user.id)})")
        if str(project.owner_id) != str(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to project"
            )
        return project

    async def _get_codebase(self, project_id: UUID) -> Codebase:
        codebase = await self.codebase_repo.get_by_project(project_id)
        if not codebase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No codebase imported for this project. Please upload a codebase ZIP first.",
            )
        return codebase

    async def run_code_review(
        self, user: User, project_id: UUID
    ) -> CodeReviewReportResponse:
        """Trigger automated code quality analysis scan on the project's codebase."""
        await self._verify_ownership(project_id, user)
        codebase = await self._get_codebase(project_id)

        # 1. Load codebase files, symbols, requirements, & links
        files = await self.codebase_repo.get_files(codebase.id)
        sym_res = await self.db.execute(
            select(CodeSymbol).where(CodeSymbol.codebase_id == codebase.id)
        )
        symbols = list(sym_res.scalars().all())
        requirements = await self.req_repo.get_all_by_project(project_id)

        # Load links
        link_res = await self.db.execute(
            select(RequirementCodeLink).where(
                RequirementCodeLink.project_id == project_id
            )
        )
        links = list(link_res.scalars().all())

        # 2. Run Static Quality Analyzer
        raw_findings, overall_score, health_status, category_counts = (
            self.analyzer.analyze_codebase(files, symbols, requirements, links)
        )

        critical_count = sum(
            1 for f in raw_findings if f.severity == FindingSeverity.CRITICAL
        )
        warning_count = sum(
            1 for f in raw_findings if f.severity == FindingSeverity.WARNING
        )
        info_count = sum(1 for f in raw_findings if f.severity == FindingSeverity.INFO)

        # 3. Create CodeReviewReport
        summary_text = (
            f"Code Review Complete: Analyzed {len(files)} files. "
            f"Overall Quality Score: {overall_score}/100 ({health_status.value.upper()}). "
            f"Identified {len(raw_findings)} issues ({critical_count} critical, {warning_count} warning, {info_count} info)."
        )

        report = CodeReviewReport(
            id=uuid4(),
            project_id=project_id,
            codebase_id=codebase.id,
            overall_score=overall_score,
            health_status=health_status,
            summary=summary_text,
            total_files_analyzed=len(files),
            total_issues_count=len(raw_findings),
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            category_counts=category_counts,
        )

        created_report = await self.quality_repo.create_report(report)

        # 4. Generate Grounded AI Explanations & Build CodeReviewFinding DB models
        req_map = {r.id: r for r in requirements}
        db_findings: List[CodeReviewFinding] = []

        for raw in raw_findings:
            linked_req = (
                req_map.get(raw.linked_requirement_id)
                if raw.linked_requirement_id
                else None
            )
            ai_explanation = await self.analyzer.generate_ai_explanation(
                raw, linked_req
            )

            db_finding = CodeReviewFinding(
                id=uuid4(),
                report_id=created_report.id,
                file_id=raw.file_id,
                file_path=raw.file_path,
                line_number=raw.line_number,
                category=raw.category,
                severity=raw.severity,
                title=raw.title,
                description=raw.description,
                rule_id=raw.rule_id,
                suggestion=raw.suggestion,
                ai_explanation=ai_explanation,
                snippet=raw.snippet,
                linked_requirement_id=raw.linked_requirement_id,
            )
            db_findings.append(db_finding)

        if db_findings:
            await self.quality_repo.create_findings(db_findings)

        # Return full report with preview findings
        preview_dtos = [
            CodeReviewFindingResponse.model_validate(f) for f in db_findings[:10]
        ]
        resp = CodeReviewReportResponse.model_validate(created_report)
        resp.findings_preview = preview_dtos
        return resp

    async def get_latest_review(
        self, user: User, project_id: UUID
    ) -> Optional[CodeReviewReportResponse]:
        """Get the most recent code review report for a project."""
        await self._verify_ownership(project_id, user)
        report = await self.quality_repo.get_latest_report_by_project(project_id)
        if not report:
            return None

        # Fetch preview findings
        findings, _ = await self.quality_repo.get_findings_by_report(
            report_id=report.id, page=1, page_size=10
        )
        preview_dtos = [
            CodeReviewFindingResponse.model_validate(f) for f in findings
        ]
        resp = CodeReviewReportResponse.model_validate(report)
        resp.findings_preview = preview_dtos
        return resp

    async def get_findings(
        self,
        user: User,
        project_id: UUID,
        severity: Optional[FindingSeverity] = None,
        category: Optional[FindingCategory] = None,
        file_path: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "severity",
        sort_dir: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> CodeReviewFindingsListResponse:
        """Query findings from the latest report with filtering, search, and pagination."""
        await self._verify_ownership(project_id, user)
        report = await self.quality_repo.get_latest_report_by_project(project_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No code review report found for this project. Run a review scan first.",
            )

        findings, total = await self.quality_repo.get_findings_by_report(
            report_id=report.id,
            severity=severity,
            category=category,
            file_path=file_path,
            search_query=search_query,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )

        dtos = [CodeReviewFindingResponse.model_validate(f) for f in findings]
        return CodeReviewFindingsListResponse(
            total_findings=total,
            report_id=report.id,
            page=page,
            page_size=page_size,
            findings=dtos,
        )
