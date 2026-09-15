"""
FastAPI router for Sprint 2.4 Requirements -> Code -> Tests Traceability Intelligence.

Endpoints:
- GET  /api/projects/{project_id}/traceability/requirements
- GET  /api/projects/{project_id}/traceability/summary
- GET  /api/projects/{project_id}/traceability/gaps
- GET  /api/projects/{project_id}/traceability/requirements/{requirement_id}
- POST /api/projects/{project_id}/traceability/tests/discover
- POST /api/projects/{project_id}/traceability/tests/suggest
- POST /api/projects/{project_id}/traceability/links
- DELETE /api/projects/{project_id}/traceability/links/{link_id}
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.traceability import (
    RequirementTraceabilityItemResponse,
    TraceabilitySummaryResponse,
    TraceabilityGapsListResponse,
    CodeTestArtifactResponse,
    TestProposalRequest,
    TestProposalResponse,
    CreateTestLinkRequest,
    RequirementTestLinkResponse,
)
from app.services.requirement_traceability_service import RequirementTraceabilityService
from app.services.test_generation_service import TestGenerationService

router = APIRouter(
    prefix="/projects/{project_id}/traceability",
    tags=["Requirement Test Traceability Intelligence"],
)


@router.get("/requirements", response_model=List[RequirementTraceabilityItemResponse])
async def get_requirement_traceability_list(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns requirement-by-requirement traceability status."""
    service = RequirementTraceabilityService(db)
    _, items = await service.analyze_project_traceability(current_user, project_id)
    return items


@router.get("/summary", response_model=TraceabilitySummaryResponse)
async def get_traceability_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns overall project traceability metrics, coverage percentages, and score."""
    service = RequirementTraceabilityService(db)
    summary, _ = await service.analyze_project_traceability(current_user, project_id)
    return summary


@router.get("/gaps", response_model=TraceabilityGapsListResponse)
async def get_traceability_gaps(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns identified missing code implementation and test coverage gaps."""
    service = RequirementTraceabilityService(db)
    return await service.get_traceability_gaps(current_user, project_id)


@router.get(
    "/requirements/{requirement_id}",
    response_model=RequirementTraceabilityItemResponse,
)
async def get_requirement_traceability_detail(
    project_id: UUID,
    requirement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns complete Requirement -> Code -> Test evidence graph for a requirement."""
    service = RequirementTraceabilityService(db)
    return await service.get_requirement_traceability_detail(
        current_user, project_id, requirement_id
    )


@router.post("/tests/discover", response_model=List[CodeTestArtifactResponse])
async def discover_tests(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Triggers deterministic test discovery and auto-links test artifacts to requirements."""
    service = RequirementTraceabilityService(db)
    return await service.discover_and_link_tests(current_user, project_id)


@router.post("/tests/suggest", response_model=TestProposalResponse)
async def suggest_test_proposal(
    project_id: UUID,
    payload: TestProposalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates a bounded, grounded AI test suggestion proposal (does NOT write code/files)."""
    service = TestGenerationService(db)
    return await service.generate_test_proposal(
        current_user, project_id, payload.requirement_id
    )


@router.post("/links", response_model=RequirementTestLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement_test_link(
    project_id: UUID,
    payload: CreateTestLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually links a requirement to a test artifact."""
    service = RequirementTraceabilityService(db)
    return await service.create_manual_test_link(
        current_user, project_id, payload.requirement_id, payload.test_artifact_id
    )


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement_test_link(
    project_id: UUID,
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Removes a requirement-test link."""
    service = RequirementTraceabilityService(db)
    await service.delete_test_link(current_user, project_id, link_id)
    return None
