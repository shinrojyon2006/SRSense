"""
Repository layer for CodeReviewReport and CodeReviewFinding entities.
"""

from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.code_quality import (
    CodeReviewReport,
    CodeReviewFinding,
    FindingCategory,
    FindingSeverity,
)


class CodeQualityRepository:
    """Async PostgreSQL repository for code quality reports and findings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_report(self, report: CodeReviewReport) -> CodeReviewReport:
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def create_findings(self, findings: List[CodeReviewFinding]) -> None:
        self.session.add_all(findings)
        await self.session.commit()

    async def get_latest_report_by_project(self, project_id: UUID) -> Optional[CodeReviewReport]:
        result = await self.session.execute(
            select(CodeReviewReport)
            .where(CodeReviewReport.project_id == project_id)
            .order_by(CodeReviewReport.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_finding_by_id(self, finding_id: UUID) -> Optional[CodeReviewFinding]:
        result = await self.session.execute(
            select(CodeReviewFinding).where(CodeReviewFinding.id == finding_id)
        )
        return result.scalar_one_or_none()

    async def get_findings_by_report(
        self,
        report_id: UUID,
        severity: Optional[FindingSeverity] = None,
        category: Optional[FindingCategory] = None,
        file_path: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_by: str = "severity",
        sort_dir: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[CodeReviewFinding], int]:
        query = select(CodeReviewFinding).where(CodeReviewFinding.report_id == report_id)

        if severity:
            query = query.where(CodeReviewFinding.severity == severity)
        if category:
            query = query.where(CodeReviewFinding.category == category)
        if file_path:
            query = query.where(CodeReviewFinding.file_path.ilike(f"%{file_path}%"))
        if search_query:
            term = f"%{search_query}%"
            query = query.where(
                (CodeReviewFinding.title.ilike(term))
                | (CodeReviewFinding.description.ilike(term))
                | (CodeReviewFinding.rule_id.ilike(term))
                | (CodeReviewFinding.file_path.ilike(term))
            )

        # Count total matching
        count_query = select(func.count()).select_from(query.subquery())
        count_res = await self.session.execute(count_query)
        total = count_res.scalar_one() or 0

        # Sorting
        if sort_by == "category":
            order_col = CodeReviewFinding.category
        elif sort_by == "rule_id":
            order_col = CodeReviewFinding.rule_id
        elif sort_by == "file_path":
            order_col = CodeReviewFinding.file_path
        else:
            order_col = CodeReviewFinding.severity

        if sort_dir.lower() == "asc":
            query = query.order_by(asc(order_col), asc(CodeReviewFinding.created_at))
        else:
            query = query.order_by(desc(order_col), desc(CodeReviewFinding.created_at))

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        res = await self.session.execute(query)
        findings = list(res.scalars().all())
        return findings, total
