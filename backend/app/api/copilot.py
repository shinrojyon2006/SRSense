"""
Sprint 1.9 — Engineering AI Copilot REST API Router

Endpoints:
- POST /projects/{project_id}/copilot/chat
- GET  /projects/{project_id}/copilot/doctor/{requirement_id}
- POST /projects/{project_id}/copilot/review
- GET  /projects/{project_id}/copilot/referee/{suggestion_id}
- GET  /projects/{project_id}/copilot/gaps
- POST /projects/{project_id}/copilot/scenarios/{requirement_id}
- GET  /projects/{project_id}/copilot/traceability
- GET  /projects/{project_id}/copilot/memory
- PUT  /projects/{project_id}/copilot/memory
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.copilot import (
    AIRefereeResponse,
    AIReviewResponse,
    CopilotChatRequest,
    CopilotChatResponse,
    GapFinderResponse,
    ProjectMemoryResponse,
    ProjectMemoryUpdate,
    RequirementDoctorResponse,
    ReviewMode,
    ScenarioGeneratorResponse,
    TraceabilityResponse,
)
from app.services.copilot_service import CopilotService

router = APIRouter(prefix="/projects/{project_id}/copilot", tags=["Engineering AI Copilot"])


@router.post("/chat", response_model=CopilotChatResponse)
async def chat_with_copilot(
    project_id: UUID,
    request: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Project Copilot chat — ask questions about the project's requirements."""
    service = CopilotService(db)
    return await service.chat(user=current_user, project_id=project_id, request=request)


@router.get("/doctor/{requirement_id}", response_model=RequirementDoctorResponse)
async def requirement_doctor(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Requirement Doctor — deep health and quality diagnosis for a single requirement."""
    service = CopilotService(db)
    return await service.diagnose_requirement(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.post("/review", response_model=AIReviewResponse)
async def run_ai_review(
    project_id: UUID,
    mode: ReviewMode = Query(ReviewMode.QA, description="Review mode (qa, security, performance, product, architecture)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI Review Modes — run QA, Security, Performance, Product, or Architecture reviews."""
    service = CopilotService(db)
    return await service.run_review(user=current_user, project_id=project_id, mode=mode)


@router.get("/referee/{suggestion_id}", response_model=AIRefereeResponse)
async def referee_suggestion(
    project_id: UUID,
    suggestion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI Referee — evaluate relationship suggestions with confidence and risk reasoning."""
    service = CopilotService(db)
    return await service.referee_suggestion(
        user=current_user, project_id=project_id, suggestion_id=suggestion_id
    )


@router.get("/gaps", response_model=GapFinderResponse)
async def find_gaps(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI Gap Finder — identify missing requirement categories (NFRs, error handling, security, etc.)."""
    service = CopilotService(db)
    return await service.find_gaps(user=current_user, project_id=project_id)


@router.post("/scenarios/{requirement_id}", response_model=ScenarioGeneratorResponse)
async def generate_scenarios(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Scenario Generator — generate Given-When-Then test scenarios for a requirement."""
    service = CopilotService(db)
    return await service.generate_scenarios(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.get("/traceability", response_model=TraceabilityResponse)
async def get_traceability(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Traceability Assistant — explain dependency chains and identify orphaned requirements."""
    service = CopilotService(db)
    return await service.get_traceability(user=current_user, project_id=project_id)


@router.get("/memory", response_model=ProjectMemoryResponse)
async def get_project_memory(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project memory — domain terminology, personas, context."""
    service = CopilotService(db)
    return await service.get_memory(user=current_user, project_id=project_id)


@router.put("/memory", response_model=ProjectMemoryResponse)
async def update_project_memory(
    project_id: UUID,
    update: ProjectMemoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update project memory — human approval required for changes."""
    service = CopilotService(db)
    return await service.update_memory(
        user=current_user, project_id=project_id, update=update
    )
