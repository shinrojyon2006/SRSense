"""
Service layer for Sprint 2.3 Code Improvement Evaluation (AsyncSession).

Orchestrates post-patch re-analysis, snapshot comparisons, regression detection,
evidence persistence, and AI explanation generation.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_improvement import CodeImprovementProposal, ImprovementStatus
from app.models.code_improvement_evaluation import CodeImprovementEvaluation
from app.models.code_quality import CodeReviewReport
from app.models.requirement import Requirement
from app.models.user import User
from app.repositories.code_improvement_repository import CodeImprovementRepository
from app.repositories.code_improvement_evaluation_repository import CodeImprovementEvaluationRepository
from app.repositories.code_quality_repository import CodeQualityRepository
from app.repositories.project_repository import ProjectRepository
from app.services.code_quality_service import CodeQualityService
from app.core.code_intelligence.evaluation_engine import EvaluationEngine

logger = logging.getLogger(__name__)


class CodeImprovementEvaluationService:
    """Business logic service managing Before/After engineering evaluations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.proposal_repo = CodeImprovementRepository(db)
        self.eval_repo = CodeImprovementEvaluationRepository(db)
        self.quality_repo = CodeQualityRepository(db)
        self.quality_service = CodeQualityService(db)

    async def _verify_ownership(self, project_id: UUID, user: User):
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found"
            )
        if str(project.owner_id) != str(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. You do not own this project."
            )
        return project

    async def evaluate_improvement(
        self, user: User, project_id: UUID, proposal_id: UUID
    ) -> CodeImprovementEvaluation:
        """Runs post-change code analysis scan and generates Before/After evaluation."""
        await self._verify_ownership(project_id, user)

        proposal = await self.proposal_repo.get_by_id(proposal_id)
        if not proposal or proposal.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Code improvement proposal {proposal_id} not found in project {project_id}",
            )

        if proposal.status != ImprovementStatus.APPLIED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot evaluate proposal with status '{proposal.status.value}'. Proposal must be APPLIED.",
            )

        # 1. Fetch BEFORE baseline report prior to new scan
        before_report = await self.quality_repo.get_latest_report_by_project(project_id)
        before_findings = []
        if before_report:
            before_findings, _ = await self.quality_repo.get_findings_by_report(
                before_report.id, page=1, page_size=500
            )

        # 2. Trigger AFTER post-change code analysis scan
        await self.quality_service.run_code_review(user=user, project_id=project_id)
        after_report = await self.quality_repo.get_latest_report_by_project(project_id)
        after_findings = []
        if after_report:
            after_findings, _ = await self.quality_repo.get_findings_by_report(
                after_report.id, page=1, page_size=500
            )

        # 3. Retrieve linked requirement title if present
        linked_req_title: Optional[str] = None
        if proposal.linked_requirement_id:
            req_res = await self.db.execute(
                select(Requirement).where(Requirement.id == proposal.linked_requirement_id)
            )
            req = req_res.scalars().first()
            if req:
                linked_req_title = req.title

        # 4. Perform deterministic comparison via EvaluationEngine
        comp = EvaluationEngine.compare_scans(
            before_report=before_report,
            after_report=after_report,
            proposal=proposal,
            linked_requirement_title=linked_req_title,
            before_findings=before_findings,
            after_findings=after_findings,
        )

        # 5. Generate AI grounded explanation
        ai_explanation = EvaluationEngine.generate_ai_explanation(comp, proposal)

        # 6. Clear existing evaluation for idempotency if re-evaluating
        await self.eval_repo.delete_by_proposal_id(proposal_id)

        # 7. Construct & persist evaluation record
        evaluation = CodeImprovementEvaluation(
            project_id=project_id,
            codebase_id=proposal.codebase_id,
            proposal_id=proposal_id,
            before_report_id=before_report.id if before_report else None,
            after_report_id=after_report.id if after_report else None,
            before_score=comp["before_score"],
            after_score=comp["after_score"],
            score_delta=comp["score_delta"],
            before_health=comp["before_health"],
            after_health=comp["after_health"],
            before_summary=comp["before_summary"],
            after_summary=comp["after_summary"],
            category_scores=comp["category_scores"],
            resolved_findings=comp["resolved_findings"],
            remaining_findings=comp["remaining_findings"],
            new_findings=comp["new_findings"],
            unchanged_findings=comp["unchanged_findings"],
            requirement_compliance_impact=comp["requirement_compliance_impact"],
            test_impact=comp["test_impact"],
            regression_detected=comp["regression_detected"],
            regression_details=comp["regression_details"],
            result_classification=comp["result_classification"],
            ai_explanation=ai_explanation,
        )

        return await self.eval_repo.create_evaluation(evaluation)

    async def get_evaluation(
        self, user: User, project_id: UUID, proposal_id: UUID
    ) -> Optional[CodeImprovementEvaluation]:
        """Retrieves existing evaluation record for a proposal."""
        await self._verify_ownership(project_id, user)

        proposal = await self.proposal_repo.get_by_id(proposal_id)
        if not proposal or proposal.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Code improvement proposal {proposal_id} not found in project {project_id}",
            )

        evaluation = await self.eval_repo.get_by_proposal_id(proposal_id)
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No evaluation found for improvement proposal {proposal_id}",
            )
        return evaluation
