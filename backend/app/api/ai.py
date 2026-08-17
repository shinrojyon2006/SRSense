"""
AI requirement analysis and improvement API routes.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import dependencies
from app.core.ai.provider_interface import AnalysisResult, ImprovementResult
from app.models.user import User
from app.schemas.requirement import RequirementResponse
from app.services.ai_service import AIService

router = APIRouter(tags=["AI Requirements Engineering"])


class DraftAnalysisRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=5, max_length=5000)
    type: str = Field(default="functional")


@router.post(
    "/projects/{project_id}/requirements/{requirement_id}/analyze",
    response_model=RequirementResponse,
)
async def analyze_requirement(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Run AI Quality Scoring and Ambiguity Analysis on an existing requirement."""
    service = AIService(db)
    return await service.analyze_requirement(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.post(
    "/projects/{project_id}/requirements/{requirement_id}/improve",
    response_model=ImprovementResult,
)
async def improve_requirement(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Generate EARS-formatted requirement improvement suggestion."""
    service = AIService(db)
    return await service.improve_requirement(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.post("/ai/analyze-draft", response_model=AnalysisResult)
async def analyze_draft(
    data: DraftAnalysisRequest,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Run ephemeral AI ambiguity analysis on draft requirement text."""
    service = AIService(db)
    return await service.analyze_draft(
        title=data.title, description=data.description, req_type=data.type
    )


@router.get("/projects/{project_id}/export")
async def export_srs_document(
    project_id: UUID,
    format: str = Query("markdown", description="Export format: 'markdown' or 'json'"),
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Export project requirements as IEEE 830 compliant SRS document (Markdown or JSON)."""
    service = AIService(db)
    return await service.export_srs_document(
        user=current_user, project_id=project_id, format_type=format
    )
