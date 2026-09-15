"""
Service layer for Requirement -> Code -> Test Traceability Analysis & Scoring.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement, RequirementStatus
from app.models.codebase import Codebase, CodeFile, RequirementCodeLink
from app.models.traceability import CodeTestArtifact, RequirementTestLink, TestRelationshipType
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.codebase_repository import CodebaseRepository
from app.repositories.traceability_repository import TraceabilityRepository
from app.core.code_intelligence.test_discovery_engine import TestDiscoveryEngine
from app.core.code_intelligence.requirement_test_traceability import RequirementTestTraceabilityEngine
from app.schemas.traceability import (
    RequirementTraceabilityItemResponse,
    TraceabilitySummaryResponse,
    TraceabilityGapItem,
    TraceabilityGapsListResponse,
    CodeTestArtifactResponse,
    RequirementTestLinkResponse,
)

logger = logging.getLogger(__name__)


class RequirementTraceabilityService:
    """Manages multi-layer Requirement -> Code -> Test traceability and coverage scoring."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)
        self.codebase_repo = CodebaseRepository(db)
        self.traceability_repo = TraceabilityRepository(db)

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

    async def discover_and_link_tests(
        self, user: User, project_id: UUID
    ) -> List[CodeTestArtifactResponse]:
        """Discovers tests in codebase and establishes Requirement -> Test links."""
        await self._verify_ownership(project_id, user)
        codebase = await self.codebase_repo.get_by_project(project_id)
        if not codebase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No codebase imported for this project. Please upload a codebase ZIP first.",
            )

        # 1. Fetch files and discover test artifacts
        files = await self.codebase_repo.get_files(codebase.id)
        raw_tests = TestDiscoveryEngine.discover_tests(files)

        # 2. Clear old test artifacts and save newly discovered artifacts
        await self.traceability_repo.clear_test_artifacts_by_codebase(codebase.id)

        artifacts_to_create = [
            CodeTestArtifact(
                project_id=project_id,
                codebase_id=codebase.id,
                file_path=rt.file_path,
                test_name=rt.test_name,
                test_framework=rt.test_framework,
                test_type=rt.test_type,
                line_start=rt.line_start,
                content_hash=rt.content_hash,
            )
            for rt in raw_tests
        ]

        created_artifacts = await self.traceability_repo.create_test_artifacts(artifacts_to_create)

        # 3. Match requirements to test artifacts
        requirements = await self.req_repo.get_all_by_project(project_id)
        link_res = await self.db.execute(
            select(RequirementCodeLink).where(RequirementCodeLink.project_id == project_id)
        )
        code_links = list(link_res.scalars().all())

        raw_matched_links = RequirementTestTraceabilityEngine.match_requirements_to_tests(
            requirements, created_artifacts, code_links, files
        )

        links_to_create = [
            RequirementTestLink(
                project_id=project_id,
                requirement_id=ml["requirement_id"],
                test_artifact_id=ml["test_artifact_id"],
                relationship_type=ml["relationship_type"],
                confidence=ml["confidence"],
                evidence=ml["evidence"],
                verified=ml["verified"],
            )
            for ml in raw_matched_links
        ]

        if links_to_create:
            await self.traceability_repo.create_requirement_test_links(links_to_create)

        return [CodeTestArtifactResponse.model_validate(a) for a in created_artifacts]

    async def analyze_project_traceability(
        self, user: User, project_id: UUID
    ) -> Tuple[TraceabilitySummaryResponse, List[RequirementTraceabilityItemResponse]]:
        """Analyzes full Requirement -> Code -> Test coverage and computes score."""
        await self._verify_ownership(project_id, user)

        requirements = await self.req_repo.get_all_by_project(project_id)
        codebase = await self.codebase_repo.get_by_project(project_id)

        code_links_res = await self.db.execute(
            select(RequirementCodeLink).where(RequirementCodeLink.project_id == project_id)
        )
        code_links = list(code_links_res.scalars().all())

        test_artifacts = await self.traceability_repo.get_test_artifacts_by_project(project_id)
        test_links = await self.traceability_repo.get_test_links_by_project(project_id)

        # Map Code Files
        code_file_map = {}
        if codebase:
            files = await self.codebase_repo.get_files(codebase.id)
            code_file_map = {f.id: f.path for f in files}

        # Map Links
        req_code_map: Dict[str, List[str]] = {}
        for cl in code_links:
            req_id = str(cl.requirement_id)
            if req_id not in req_code_map:
                req_code_map[req_id] = []
            if cl.code_file_id in code_file_map:
                req_code_map[req_id].append(code_file_map[cl.code_file_id])

        req_test_map: Dict[str, List[RequirementTestLink]] = {}
        for tl in test_links:
            req_id = str(tl.requirement_id)
            if req_id not in req_test_map:
                req_test_map[req_id] = []
            req_test_map[req_id].append(tl)

        items: List[RequirementTraceabilityItemResponse] = []
        total_reqs = len(requirements)
        with_code = 0
        with_tests = 0
        fully_traced = 0
        partially_traced = 0
        untraced = 0

        total_penalties = 0

        for req in requirements:
            req_id_str = str(req.id)
            linked_code = req_code_map.get(req_id_str, [])
            linked_test_objs = req_test_map.get(req_id_str, [])
            linked_tests = [tl.test_artifact.test_name if tl.test_artifact else f"TestArtifact:{tl.test_artifact_id}" for tl in linked_test_objs]

            has_c = len(linked_code) > 0
            has_t = len(linked_tests) > 0

            if has_c:
                with_code += 1
            if has_t:
                with_tests += 1

            # Determine Traceability Status
            ev_list = [tl.evidence for tl in linked_test_objs if tl.evidence]
            highest_confidence = max([tl.confidence for tl in linked_test_objs], default=1.0 if (has_c and has_t) else (0.5 if (has_c or has_t) else 0.0))

            if has_c and has_t:
                status_str = "FULLY_TRACED"
                fully_traced += 1
                risk_msg = None
            elif has_c and not has_t:
                status_str = "IMPLEMENTED_NOT_TESTED"
                partially_traced += 1
                total_penalties += 7
                risk_msg = "Implementation exists but no associated test evidence discovered."
            elif not has_c and has_t:
                status_str = "TESTED_NOT_LINKED"
                partially_traced += 1
                total_penalties += 5
                risk_msg = "Test evidence exists but requirement is not linked to source implementation."
            elif not has_c and not has_t:
                status_str = "NO_IMPLEMENTATION"
                untraced += 1
                total_penalties += 10
                risk_msg = "No code implementation or test evidence found for requirement."
            else:
                status_str = "UNDETERMINED"
                untraced += 1
                total_penalties += 5
                risk_msg = "Insufficient evidence to determine traceability status."

            item = RequirementTraceabilityItemResponse(
                requirement_id=req.id,
                original_req_id=req.original_req_id,
                title=req.title,
                requirement_type=req.type.value if hasattr(req, "type") and hasattr(req.type, "value") else str(getattr(req, "type", getattr(req, "requirement_type", "functional"))),
                has_code=has_c,
                has_test=has_t,
                status=status_str,
                confidence=highest_confidence,
                linked_code_files=linked_code,
                linked_test_names=linked_tests,
                evidence=ev_list,
                risk=risk_msg,
            )
            items.append(item)

        # Coverage Math & Normalized Score
        code_cov_pct = round((with_code / total_reqs * 100.0) if total_reqs > 0 else 0.0, 1)
        test_cov_pct = round((with_tests / total_reqs * 100.0) if total_reqs > 0 else 0.0, 1)
        full_traced_pct = round((fully_traced / total_reqs * 100.0) if total_reqs > 0 else 0.0, 1)

        traceability_score = max(0, min(100, 100 - total_penalties))

        if traceability_score >= 85:
            health = "HEALTHY"
        elif traceability_score >= 60:
            health = "NEEDS_ATTENTION"
        else:
            health = "AT_RISK"

        summary = TraceabilitySummaryResponse(
            total_requirements=total_reqs,
            requirements_with_code=with_code,
            requirements_without_code=total_reqs - with_code,
            requirements_with_tests=with_tests,
            requirements_without_tests=total_reqs - with_tests,
            fully_traced_count=fully_traced,
            partially_traced_count=partially_traced,
            untraced_count=untraced,
            code_coverage_pct=code_cov_pct,
            test_coverage_pct=test_cov_pct,
            full_traceability_pct=full_traced_pct,
            traceability_score=traceability_score,
            health_status=health,
        )

        return summary, items

    async def get_traceability_gaps(
        self, user: User, project_id: UUID
    ) -> TraceabilityGapsListResponse:
        """Identifies specific missing implementation and test coverage gaps."""
        _, items = await self.analyze_project_traceability(user, project_id)

        gaps: List[TraceabilityGapItem] = []
        for item in items:
            req_title_lower = item.title.lower()
            req_type_lower = item.requirement_type.lower()

            if item.status == "NO_IMPLEMENTATION":
                gaps.append(
                    TraceabilityGapItem(
                        requirement_id=item.requirement_id,
                        original_req_id=item.original_req_id,
                        title=item.title,
                        gap_type="NO_IMPLEMENTATION",
                        description=f"Requirement '{item.title}' has no linked source code implementation.",
                        severity="CRITICAL",
                        recommendation="Implement feature source code and attach file link in Requirement-Code Matrix.",
                    )
                )
            elif item.status == "IMPLEMENTED_NOT_TESTED":
                gaps.append(
                    TraceabilityGapItem(
                        requirement_id=item.requirement_id,
                        original_req_id=item.original_req_id,
                        title=item.title,
                        gap_type="IMPLEMENTED_NOT_TESTED",
                        description=f"Requirement '{item.title}' is implemented in code but has zero associated test coverage.",
                        severity="HIGH",
                        recommendation="Generate test proposal using [Suggest Test] and implement unit/integration test suite.",
                    )
                )

            # Check for specialized requirement type gaps
            if "performance" in req_type_lower or "sla" in req_title_lower or "ms" in req_title_lower:
                if not any("perf" in t.lower() or "benchmark" in t.lower() for t in item.linked_test_names):
                    gaps.append(
                        TraceabilityGapItem(
                            requirement_id=item.requirement_id,
                            original_req_id=item.original_req_id,
                            title=item.title,
                            gap_type="MISSING_SLA_TEST",
                            description=f"Performance/SLA requirement '{item.title}' lacks observable benchmark/load test coverage.",
                            severity="HIGH",
                            recommendation="Create automated performance/load benchmark test validating latency SLA threshold.",
                        )
                    )
            elif "security" in req_type_lower or "auth" in req_title_lower or "credential" in req_title_lower:
                if not any("sec" in t.lower() or "auth" in t.lower() for t in item.linked_test_names):
                    gaps.append(
                        TraceabilityGapItem(
                            requirement_id=item.requirement_id,
                            original_req_id=item.original_req_id,
                            title=item.title,
                            gap_type="MISSING_SECURITY_TEST",
                            description=f"Security requirement '{item.title}' lacks security-focused verification test coverage.",
                            severity="CRITICAL",
                            recommendation="Implement security unit/integration test verifying auth/access-control boundaries.",
                        )
                    )

        return TraceabilityGapsListResponse(total_gaps=len(gaps), gaps=gaps)

    async def get_requirement_traceability_detail(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> RequirementTraceabilityItemResponse:
        """Retrieves complete R -> C -> T traceability detail for a specific requirement."""
        _, items = await self.analyze_project_traceability(user, project_id)
        target = next((item for item in items if item.requirement_id == requirement_id), None)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requirement {requirement_id} not found in project {project_id}",
            )
        return target

    async def create_manual_test_link(
        self, user: User, project_id: UUID, requirement_id: UUID, test_artifact_id: UUID
    ) -> RequirementTestLinkResponse:
        """Manually links a requirement to a test artifact."""
        await self._verify_ownership(project_id, user)
        link = RequirementTestLink(
            project_id=project_id,
            requirement_id=requirement_id,
            test_artifact_id=test_artifact_id,
            relationship_type=TestRelationshipType.DIRECT.value,
            confidence=1.0,
            evidence={"signal": "MANUAL_USER_LINK", "explanation": "Explicitly linked by user in Traceability Workspace."},
            verified=True,
        )
        created = await self.traceability_repo.create_requirement_test_links([link])
        return RequirementTestLinkResponse.model_validate(created[0])

    async def delete_test_link(
        self, user: User, project_id: UUID, link_id: UUID
    ) -> bool:
        """Deletes a requirement-test link."""
        await self._verify_ownership(project_id, user)
        deleted = await self.traceability_repo.delete_link(link_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requirement-test link {link_id} not found",
            )
        return True
