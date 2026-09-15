"""
Sprint 2.2 — Code Improvement Service layer.
Manages proposal generation, context collection, requirement grounding,
patch safety validation, explicit human approval/rejection, and safe codebase application.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.code_intelligence.improvement_engine import (
    CodeImprovementEngine,
    PatchSafetyValidator,
)
from app.models.code_improvement import CodeImprovementProposal, ImprovementStatus
from app.models.code_quality import CodeReviewFinding
from app.models.codebase import Codebase, CodeFile, CodeSymbol
from app.models.requirement import Requirement
from app.models.user import User
from app.repositories.code_improvement_repository import CodeImprovementRepository
from app.repositories.code_quality_repository import CodeQualityRepository
from app.repositories.codebase_repository import CodebaseRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_repository import RequirementRepository
from app.schemas.code_improvement import (
    CodeImprovementCreateRequest,
    CodeImprovementListResponse,
    CodeImprovementResponse,
)

logger = logging.getLogger(__name__)


class CodeImprovementService:
    """Service layer managing reviewable code improvement proposals and non-silent patch execution."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.codebase_repo = CodebaseRepository(db)
        self.req_repo = RequirementRepository(db)
        self.quality_repo = CodeQualityRepository(db)
        self.improvement_repo = CodeImprovementRepository(db)
        self.engine = CodeImprovementEngine()

    async def _verify_ownership(self, project_id: UUID, user: User):
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
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
                detail="No codebase imported for this project. Upload a codebase ZIP first.",
            )
        return codebase

    async def create_improvement_proposal(
        self, user: User, project_id: UUID, req: CodeImprovementCreateRequest
    ) -> CodeImprovementResponse:
        """Collect bounded context and generate a reviewable code improvement proposal."""
        await self._verify_ownership(project_id, user)
        codebase = await self._get_codebase(project_id)

        finding: Optional[CodeReviewFinding] = None
        code_file: Optional[CodeFile] = None
        linked_req: Optional[Requirement] = None

        if req.finding_id:
            finding = await self.quality_repo.get_finding_by_id(req.finding_id)
            if not finding:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Code review finding not found.",
                )
            if finding.file_id:
                code_file = await self.codebase_repo.get_file_by_id(finding.file_id, project_id)
            if finding.linked_requirement_id:
                linked_req = await self.req_repo.get_by_id(finding.linked_requirement_id)
        elif req.file_id:
            code_file = await self.codebase_repo.get_file_by_id(req.file_id, project_id)
            if not code_file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Code file not found in this project.",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must specify either finding_id or file_id to generate code improvement proposal.",
            )

        # Build synthetic finding if file_id was supplied directly
        if not finding and code_file:
            finding = CodeReviewFinding(
                id=uuid4(),
                report_id=uuid4(),
                file_id=code_file.id,
                file_path=code_file.path,
                line_number=1,
                category="quality",
                severity="warning",
                title=f"Improvement Request for {code_file.filename}",
                description="Manual improvement proposal request.",
                rule_id=req.rule_id or "QUAL-001",
                suggestion="Refactor code for improved quality and maintainability.",
                snippet="",
            )

        # Load codebase symbols
        sym_res = await self.db.execute(
            select(CodeSymbol).where(CodeSymbol.codebase_id == codebase.id)
        )
        symbols = list(sym_res.scalars().all())

        # Collect bounded context
        context = self.engine.collect_bounded_context(
            finding=finding,
            file=code_file,
            linked_requirement=linked_req,
            symbols=symbols,
        )

        # Generate proposal data
        prop_data = await self.engine.generate_proposal(context)

        # Construct DB entity
        proposal = CodeImprovementProposal(
            id=uuid4(),
            project_id=project_id,
            codebase_id=codebase.id,
            finding_id=finding.id if finding and hasattr(finding, "id") and req.finding_id else None,
            linked_requirement_id=context.linked_requirement_id,
            rule_id=finding.rule_id if finding else (req.rule_id or "QUAL-001"),
            title=prop_data.title,
            problem_summary=prop_data.problem_summary,
            root_cause=prop_data.root_cause,
            recommendation=prop_data.recommendation,
            file_id=code_file.id if code_file else finding.file_id,
            file_path=context.file_path,
            current_code=prop_data.current_code,
            proposed_code=prop_data.proposed_code,
            patch_diff=prop_data.patch_diff,
            affected_files=prop_data.affected_files,
            affected_requirements=prop_data.affected_requirements,
            affected_tests=prop_data.affected_tests,
            risks=prop_data.risks,
            confidence=prop_data.confidence,
            uncertainty=prop_data.uncertainty,
            status=ImprovementStatus.PROPOSED,
        )

        created_proposal = await self.improvement_repo.create(proposal)
        await self.db.commit()

        return CodeImprovementResponse.model_validate(created_proposal)

    async def get_improvement(
        self, user: User, project_id: UUID, improvement_id: UUID
    ) -> CodeImprovementResponse:
        """Get detail of a specific improvement proposal."""
        await self._verify_ownership(project_id, user)
        proposal = await self.improvement_repo.get_by_id(improvement_id)
        if not proposal or proposal.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Code improvement proposal not found.",
            )
        return CodeImprovementResponse.model_validate(proposal)

    async def list_improvements(
        self,
        user: User,
        project_id: UUID,
        status_filter: Optional[ImprovementStatus] = None,
        finding_id: Optional[UUID] = None,
    ) -> CodeImprovementListResponse:
        """List improvement proposals for a project."""
        await self._verify_ownership(project_id, user)
        proposals = await self.improvement_repo.get_by_project(
            project_id=project_id, status=status_filter, finding_id=finding_id
        )
        dtos = [CodeImprovementResponse.model_validate(p) for p in proposals]
        return CodeImprovementListResponse(total=len(dtos), items=dtos)

    async def approve_and_apply_improvement(
        self, user: User, project_id: UUID, improvement_id: UUID
    ) -> CodeImprovementResponse:
        """
        Explicitly approve and apply patch to the codebase safely.
        Never mutates code silently or without explicit approval.
        """
        await self._verify_ownership(project_id, user)
        proposal = await self.improvement_repo.get_by_id(improvement_id)
        if not proposal or proposal.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Code improvement proposal not found.",
            )

        if proposal.status in (ImprovementStatus.APPLIED, ImprovementStatus.REJECTED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proposal cannot be applied because its current status is {proposal.status.value.upper()}.",
            )

        # 1. Path Safety Validation
        if not PatchSafetyValidator.validate_path_safety(proposal.file_path):
            proposal.status = ImprovementStatus.FAILED
            proposal.error_message = "Path traversal validation error: File path contains unsafe relative references."
            await self.improvement_repo.update(proposal)
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=proposal.error_message,
            )

        # 2. Retrieve CodeFile
        code_file: Optional[CodeFile] = None
        if proposal.file_id:
            code_file = await self.codebase_repo.get_file_by_id(proposal.file_id, project_id)
        if not code_file:
            # Fallback search by file_path
            codebase = await self._get_codebase(project_id)
            files = await self.codebase_repo.get_files(codebase.id)
            code_file = next((f for f in files if f.path == proposal.file_path), None)

        if not code_file:
            proposal.status = ImprovementStatus.FAILED
            proposal.error_message = f"Target file '{proposal.file_path}' not found in codebase index."
            await self.improvement_repo.update(proposal)
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=proposal.error_message,
            )

        raw_content = (code_file.metadata_json or {}).get("raw_content", "")

        # 3. Check for Stale Patch Content
        if PatchSafetyValidator.check_stale_content(raw_content, proposal.current_code):
            proposal.status = ImprovementStatus.STALE
            proposal.error_message = "Stale patch error: The target file content has changed since this proposal was generated."
            proposal.reviewed_at = datetime.now(timezone.utc)
            await self.improvement_repo.update(proposal)
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stale patch detected. The source code was modified after this proposal was created. Please regenerate the improvement.",
            )

        # 4. Perform Safe Patch Application
        success, new_content, err_msg = PatchSafetyValidator.apply_replacement(
            full_content=raw_content,
            current_code=proposal.current_code,
            proposed_code=proposal.proposed_code,
        )

        if not success:
            proposal.status = ImprovementStatus.FAILED
            proposal.error_message = err_msg or "Patch replacement failed."
            proposal.reviewed_at = datetime.now(timezone.utc)
            await self.improvement_repo.update(proposal)
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=proposal.error_message,
            )

        # 5. Persist updated raw_content into CodeFile metadata_json
        updated_meta = dict(code_file.metadata_json or {})
        updated_meta["raw_content"] = new_content
        code_file.metadata_json = updated_meta
        self.db.add(code_file)

        # 6. Update Proposal Status to APPLIED
        proposal.status = ImprovementStatus.APPLIED
        proposal.reviewed_at = datetime.now(timezone.utc)
        proposal.applied_at = datetime.now(timezone.utc)
        proposal.error_message = None
        await self.improvement_repo.update(proposal)

        await self.db.commit()
        return CodeImprovementResponse.model_validate(proposal)

    async def reject_improvement(
        self, user: User, project_id: UUID, improvement_id: UUID
    ) -> CodeImprovementResponse:
        """Explicitly reject an improvement proposal."""
        await self._verify_ownership(project_id, user)
        proposal = await self.improvement_repo.get_by_id(improvement_id)
        if not proposal or proposal.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Code improvement proposal not found.",
            )

        proposal.status = ImprovementStatus.REJECTED
        proposal.reviewed_at = datetime.now(timezone.utc)
        await self.improvement_repo.update(proposal)
        await self.db.commit()

        return CodeImprovementResponse.model_validate(proposal)
