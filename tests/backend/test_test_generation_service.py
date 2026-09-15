"""
Sprint 2.4 — Test Generation Service Unit & Bounded Safety Tests.

Validates that AI test proposal generation is strictly advisory, bounded,
and never executes or writes files automatically.
"""

import uuid
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.requirement import Requirement, RequirementType
from app.services.test_generation_service import TestGenerationService


@pytest.mark.asyncio
async def test_generate_test_proposal_bounded_structure():
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="test@srsense.ai",
        name="Test Dev",
        role=UserRole.DEVELOPER,
    )
    project_id = uuid.uuid4()
    project = Project(
        id=project_id,
        owner_id=user.id,
        title="Test Proj",
        description="Desc",
    )
    req_id = uuid.uuid4()
    req = Requirement(
        id=req_id,
        project_id=project_id,
        original_req_id="REQ-505",
        title="User Password Reset",
        description="Allow user to reset forgotten password safely.",
        type=RequirementType.FUNCTIONAL,
    )

    db_mock = AsyncMock()
    mock_execute_res = MagicMock()
    mock_execute_res.scalars.return_value.all.return_value = []
    db_mock.execute.return_value = mock_execute_res

    service = TestGenerationService(db_mock)
    service.project_repo.get_by_id = AsyncMock(return_value=project)
    service.req_repo.get_by_id = AsyncMock(return_value=req)

    with patch("app.services.test_generation_service.get_ai_provider") as mock_ai:
        ai_provider_mock = MagicMock()
        ai_provider_mock.generate_text.return_value = "def test_password_reset(): pass"
        mock_ai.return_value = ai_provider_mock

        proposal = await service.generate_test_proposal(user, project_id, req_id)

        assert proposal is not None
        assert proposal.requirement_id == req_id
        assert proposal.status == "PROPOSAL_GENERATED"
        assert "def test_password_reset" in proposal.code_snippet_proposal
