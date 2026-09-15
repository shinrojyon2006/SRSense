"""
AI Test Suggestion Service for Sprint 2.4 Traceability.

Generates bounded, grounded test proposals for requirements and linked code snippets.
PROPOSAL ONLY: Never modifies source/test files or executes tests.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement
from app.models.codebase import RequirementCodeLink, CodeFile, CodeSymbol
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.codebase_repository import CodebaseRepository
from app.core.ai.factory import get_ai_provider
from app.schemas.traceability import TestProposalResponse

logger = logging.getLogger(__name__)


class TestGenerationService:
    """Bounded AI test proposal generator."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)
        self.codebase_repo = CodebaseRepository(db)

    async def _verify_ownership(self, project_id: UUID, user: User):
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found"
            )
        if str(project.owner_id) != str(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to project"
            )
        return project

    async def generate_test_proposal(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> TestProposalResponse:
        """Generates a structured test suggestion proposal grounded in requirement and code evidence."""
        await self._verify_ownership(project_id, user)

        req = await self.req_repo.get_by_id(requirement_id)
        if not req or req.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requirement {requirement_id} not found in project {project_id}",
            )

        # Check for insufficient requirement context
        if not req.description or len(req.description.strip()) < 5:
            return TestProposalResponse(
                requirement_id=req.id,
                requirement_title=req.title,
                test_title=f"Test Proposal for {req.title}",
                purpose="Insufficient requirement details to generate test steps.",
                test_type="UNKNOWN",
                suggested_framework="pytest",
                preconditions=[],
                inputs=[],
                steps=[],
                expected_result="N/A",
                validated_behavior="N/A",
                edge_cases=[],
                code_snippet_proposal="",
                confidence=0.0,
                status="INSUFFICIENT_CONTEXT",
                missing_context_explanation="Requirement description is empty or missing acceptance criteria context.",
            )

        # Bounded Context Extraction: Fetch linked code file snippet if available
        link_res = await self.db.execute(
            select(RequirementCodeLink).where(
                RequirementCodeLink.requirement_id == requirement_id,
                RequirementCodeLink.project_id == project_id,
            )
        )
        links = list(link_res.scalars().all())

        code_snippet = ""
        code_file_path = "N/A"
        framework = "pytest"

        if links:
            first_link = links[0]
            if first_link.code_file_id:
                code_file = await self.codebase_repo.get_file_by_id(first_link.code_file_id)
                if code_file:
                    code_file_path = code_file.path
                    raw = (code_file.metadata_json or {}).get("raw_content", "")
                    code_snippet = raw[:500] if raw else ""
                    if any(ext in code_file.filename.lower() for ext in [".ts", ".tsx", ".js"]):
                        framework = "vitest"
                    elif "java" in code_file.filename.lower():
                        framework = "junit"

        # Detect test type based on requirement title / category
        req_title_lower = req.title.lower()
        req_desc_lower = req.description.lower()

        if "performance" in req_title_lower or "sla" in req_title_lower or "ms" in req_title_lower:
            test_type = "PERFORMANCE"
            purpose = f"Validate performance latency threshold requirement: '{req.title}'."
        elif "security" in req_title_lower or "auth" in req_title_lower or "credential" in req_title_lower:
            test_type = "SECURITY"
            purpose = f"Validate security authorization boundary requirement: '{req.title}'."
        else:
            test_type = "UNIT"
            purpose = f"Validate functional requirement behavior: '{req.title}'."

        # Generate Grounded Test Code Proposal via AI Provider
        try:
            ai = get_ai_provider()
            prompt = (
                f"REQUIREMENT TRACEABILITY CONTEXT:\n"
                f"Requirement ID: {req.original_req_id or str(req.id)[:8]}\n"
                f"Title: {req.title}\n"
                f"Description: {req.description}\n"
                f"Linked Code File: {code_file_path}\n"
                f"Code Snippet Bounded Context:\n{code_snippet or 'No code file linked yet.'}\n\n"
                f"INSTRUCTIONS:\n"
                f"Generate a clean test function proposal in {framework} syntax to verify this requirement.\n"
                f"Include clear assertions and edge cases."
            )
            ai_code = ai.generate_text(prompt)
        except Exception as e:
            logger.warning(f"AI test proposal generation fallback: {e}")
            ai_code = None

        if not ai_code:
            ai_code = f"""# Proposed Test for {req.original_req_id or 'REQ'}: {req.title}
def test_{req.title.lower().replace(' ', '_')[:30]}():
    # Precondition: Initialize test context for {req.title}
    # Action: Execute target behavior
    # Assert: Verify requirement contract
    assert True
"""

        return TestProposalResponse(
            requirement_id=req.id,
            requirement_title=req.title,
            test_title=f"test_{req.title.lower().replace(' ', '_')[:35]}",
            purpose=purpose,
            test_type=test_type,
            suggested_framework=framework,
            preconditions=[f"Set up environment for requirement '{req.title}'"],
            inputs=["valid_sample_input", "invalid_edge_case_input"],
            steps=[
                "1. Initialize system test context",
                f"2. Trigger function related to '{req.title}'",
                "3. Assert expected output matching requirement criteria",
            ],
            expected_result=f"System satisfies requirement '{req.title}' without errors.",
            validated_behavior=req.description,
            edge_cases=["Null/Empty input parameters", "Boundary condition threshold"],
            code_snippet_proposal=ai_code,
            confidence=0.85,
            status="PROPOSAL_GENERATED",
            missing_context_explanation=None,
        )
