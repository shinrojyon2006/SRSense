"""
AI Service — business logic for AI requirement analysis, EARS improvements,
and SRS Document export generation.
"""

from typing import Any, Dict
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.factory import get_ai_provider
from app.core.ai.provider_interface import AnalysisResult, ImprovementResult
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_repository import RequirementRepository
from app.schemas.requirement import RequirementResponse
from app.utils.logger import get_logger

logger = get_logger("srsense.ai")


class AIService:
    """Service layer for AI operations and SRS export."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_provider = get_ai_provider()
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)

    async def _verify_project_ownership(self, project_id: UUID, user: User):
        """Helper to ensure project belongs to the user."""
        project = await self.project_repo.get_by_id_and_owner(
            project_id=project_id, owner_id=user.id
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )
        return project

    async def analyze_requirement(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> RequirementResponse:
        """Run AI Quality Analysis on a requirement and save results to PostgreSQL."""
        await self._verify_project_ownership(project_id, user)

        req = await self.req_repo.get_by_id_and_project(
            requirement_id=requirement_id, project_id=project_id
        )
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found",
            )

        analysis: AnalysisResult = await self.ai_provider.analyze_requirement(
            title=req.title, description=req.description, req_type=req.type.value
        )

        req.quality_score = analysis.quality_score
        req.analysis_result = analysis.model_dump()
        updated = await self.req_repo.update(req)

        logger.info(
            "AI Analysis complete for req %s (Score=%d/100)",
            requirement_id,
            analysis.quality_score,
        )
        return RequirementResponse.model_validate(updated)

    async def improve_requirement(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> ImprovementResult:
        """Generate EARS-formatted improvement suggestion for a requirement."""
        await self._verify_project_ownership(project_id, user)

        req = await self.req_repo.get_by_id_and_project(
            requirement_id=requirement_id, project_id=project_id
        )
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found",
            )

        return await self.ai_provider.suggest_improvement(
            title=req.title, description=req.description, req_type=req.type.value
        )

    async def analyze_draft(
        self, title: str, description: str, req_type: str = "functional"
    ) -> AnalysisResult:
        """Ephemeral analysis for draft requirements prior to creation."""
        return await self.ai_provider.analyze_requirement(
            title=title, description=description, req_type=req_type
        )

    async def export_srs_document(
        self, user: User, project_id: UUID, format_type: str = "markdown"
    ) -> Dict[str, Any]:
        """Generate IEEE 830 compliant Software Requirements Specification document."""
        project = await self._verify_project_ownership(project_id, user)
        requirements = await self.req_repo.get_all_by_project(project_id=project_id)

        if format_type.lower() == "json":
            return {
                "srs_title": f"Software Requirements Specification — {project.title}",
                "project_id": str(project.id),
                "description": project.description,
                "total_requirements": len(requirements),
                "export_date": project.updated_at.isoformat() if project.updated_at else "",
                "requirements": [
                    {
                        "id": str(r.id),
                        "title": r.title,
                        "description": r.description,
                        "type": r.type.value,
                        "priority": r.priority.value,
                        "status": r.status.value,
                        "version": r.version,
                        "quality_score": r.quality_score,
                        "analysis_result": r.analysis_result,
                    }
                    for r in requirements
                ],
            }

        # Format as Markdown (.md)
        lines = [
            f"# Software Requirements Specification (SRS)",
            f"## Project: {project.title}",
            f"**Description**: {project.description or 'N/A'}",
            f"**Total Requirements**: {len(requirements)}",
            "",
            "---",
            "",
            "## Requirements Index",
            "",
        ]

        if not requirements:
            lines.append("*No requirements defined in this project specification.*")
        else:
            for idx, r in enumerate(requirements, 1):
                score_str = f"{r.quality_score}/100" if r.quality_score is not None else "Not Analyzed"
                lines.extend([
                    f"### {idx}. {r.title}",
                    f"- **ID**: `{r.id}`",
                    f"- **Type**: `{r.type.value}` | **Priority**: `{r.priority.value}` | **Status**: `{r.status.value}` | **Version**: `{r.version}`",
                    f"- **AI Quality Score**: **{score_str}**",
                    f"- **Specification Description**:",
                    f"  > {r.description}",
                    "",
                ])
                if r.analysis_result and r.analysis_result.get("summary_feedback"):
                    lines.append(f"  *AI Feedback*: {r.analysis_result['summary_feedback']}")
                    lines.append("")

        return {"filename": f"SRS_{project.title.replace(' ', '_')}.md", "content": "\n".join(lines)}
