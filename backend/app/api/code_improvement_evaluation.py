"""
FastAPI router for Sprint 2.3 Before/After Code Improvement Evaluation.

Endpoints:
- POST /api/projects/{project_id}/codebase/improvements/{improvement_id}/evaluate
- GET  /api/projects/{project_id}/codebase/improvements/{improvement_id}/evaluation
"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.code_improvement_evaluation import CodeImprovementEvaluationResponse
from app.services.code_improvement_evaluation_service import CodeImprovementEvaluationService

router = APIRouter(
    prefix="/projects/{project_id}/codebase/improvements/{improvement_id}",
    tags=["Code Improvement Evaluation"],
)


@router.post(
    "/evaluate",
    response_model=CodeImprovementEvaluationResponse,
    status_code=status.HTTP_200_OK,
)
async def evaluate_code_improvement(
    project_id: UUID,
    improvement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Triggers post-patch re-analysis and generates Before/After evaluation."""
    service = CodeImprovementEvaluationService(db)
    return await service.evaluate_improvement(
        user=current_user, project_id=project_id, proposal_id=improvement_id
    )


@router.get(
    "/evaluation",
    response_model=CodeImprovementEvaluationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_code_improvement_evaluation(
    project_id: UUID,
    improvement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves existing evaluation record for an improvement proposal."""
    service = CodeImprovementEvaluationService(db)
    return await service.get_evaluation(
        user=current_user, project_id=project_id, proposal_id=improvement_id
    )
