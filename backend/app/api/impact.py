"""
Requirement Change Impact & Risk Simulator REST API router.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import dependencies
from app.models.user import User
from app.schemas.impact import (
    ImpactReportResponse,
    ProjectRiskSummaryResponse,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
)
from app.services.impact_service import ImpactService

router = APIRouter(tags=["Requirement Change Impact Simulator"])


@router.post(
    "/projects/{project_id}/impact/simulate",
    response_model=WhatIfSimulationResponse,
)
async def simulate_what_if(
    project_id: UUID,
    request: WhatIfSimulationRequest,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Run ephemeral What-If change simulation in memory (STRICTLY NO DB MUTATION)."""
    service = ImpactService(db)
    return await service.simulate_what_if(
        user=current_user, project_id=project_id, request=request
    )


@router.get(
    "/projects/{project_id}/impact/requirements/{requirement_id}",
    response_model=WhatIfSimulationResponse,
)
async def get_impact_analysis_for_requirement(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Get impact propagation analysis for an existing requirement."""
    service = ImpactService(db)
    return await service.get_impact_analysis_for_requirement(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.post(
    "/projects/{project_id}/impact/requirements/{requirement_id}/report",
    response_model=ImpactReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_impact_report(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Calculate and persist formal Requirement Impact Report into PostgreSQL."""
    service = ImpactService(db)
    return await service.generate_impact_report(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.get(
    "/projects/{project_id}/impact/summary",
    response_model=ProjectRiskSummaryResponse,
)
async def get_project_risk_summary(
    project_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Get project-wide risk summary analytics and high-risk rankings."""
    service = ImpactService(db)
    return await service.get_project_risk_summary(
        user=current_user, project_id=project_id
    )
