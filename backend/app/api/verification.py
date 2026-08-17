"""
Requirement-to-Verification Compiler REST API Router — Sprint 1.8.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import dependencies
from app.models.user import User
from app.models.verification import TestCase
from app.schemas.verification import (
    ProjectVerificationSummaryResponse,
    TestCaseResponse,
    UpdateTestCaseExecutionRequest,
    VerificationSpecificationResponse,
)
from app.services.verification_compiler_service import VerificationCompilerService

router = APIRouter(tags=["Requirement-to-Verification Compiler"])


@router.post(
    "/projects/{project_id}/verification/requirements/{requirement_id}/compile",
    response_model=VerificationSpecificationResponse,
)
async def compile_requirement(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Compile a requirement into structured verification specification & test case suite."""
    service = VerificationCompilerService(db)
    return await service.compile_requirement(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.get(
    "/projects/{project_id}/verification/requirements/{requirement_id}",
    response_model=VerificationSpecificationResponse,
)
async def get_verification_for_requirement(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Fetch compiled verification specification & test case suite for a requirement."""
    service = VerificationCompilerService(db)
    return await service.get_verification_for_requirement(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.patch(
    "/projects/{project_id}/verification/test-cases/{test_case_id}",
    response_model=TestCaseResponse,
)
async def update_test_case_status(
    project_id: UUID,
    test_case_id: UUID,
    payload: UpdateTestCaseExecutionRequest,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Update test case execution status (untested, passed, failed, blocked) & update verification evidence status."""
    service = VerificationCompilerService(db)
    updated_tc = await service.update_test_case_status(
        user=current_user,
        project_id=project_id,
        test_case_id=test_case_id,
        new_status=payload.execution_status,
    )
    return TestCaseResponse.model_validate(updated_tc)


@router.get(
    "/projects/{project_id}/verification/summary",
    response_model=ProjectVerificationSummaryResponse,
)
async def get_project_verification_summary(
    project_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Fetch project-wide verification coverage & readiness summary."""
    service = VerificationCompilerService(db)
    return await service.get_project_verification_summary(
        user=current_user, project_id=project_id
    )
