"""
Requirement Conflict & Dependency Intelligence Service —
Automated Detection Engine, Scan Idempotency, Material Change Reconsideration,
Human-in-the-Loop Acceptance, and Project Summary Analytics.
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.relationship import RelationshipType
from app.models.requirement import Requirement
from app.models.suggestion import RequirementSuggestion, SuggestionStatus
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.suggestion_repository import SuggestionRepository
from app.schemas.graph import RelationshipCreateRequest
from app.schemas.intelligence import (
    IntelligenceSummaryResponse,
    ScanResponse,
    SuggestionResponse,
)
from app.services.graph_service import GraphService
from app.utils.logger import get_logger

logger = get_logger("srsense.intelligence_service")


def compute_text_hash(title: str, description: str) -> str:
    """Compute SHA-256 hash of title and description to detect material changes."""
    content = f"{title.strip().lower()}:{description.strip().lower()}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class IntelligenceService:
    """Service layer for Conflict & Dependency Intelligence."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.suggestion_repo = SuggestionRepository(db)
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)
        self.rel_repo = RelationshipRepository(db)
        self.graph_service = GraphService(db)

    async def _verify_project_ownership(self, project_id: UUID, user: User):
        """Verify project belongs to current authenticated user."""
        project = await self.project_repo.get_by_id_and_owner(
            project_id=project_id, owner_id=user.id
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied",
            )
        return project

    async def run_intelligence_scan(self, user: User, project_id: UUID) -> ScanResponse:
        """Run automated conflict & dependency discovery scan (Idempotent with material change tracking)."""
        await self._verify_project_ownership(project_id, user)
        reqs = await self.req_repo.get_all_by_project(project_id)

        new_count = 0
        updated_count = 0
        reconsidered_count = 0

        # Run Candidate Discovery Detectors
        candidates = self._detect_all_candidates(reqs)

        for cand in candidates:
            source_id = cand["source_id"]
            target_id = cand["target_id"]
            rel_type = cand["type"]
            source_req = cand["source_req"]
            target_req = cand["target_req"]

            # Mandatory Adjustment 2: Canonical ordering for symmetric conflict relationships
            if rel_type == RelationshipType.CONFLICTS_WITH:
                if str(source_id) > str(target_id):
                    source_id, target_id = target_id, source_id
                    source_req, target_req = target_req, source_req

            src_hash = compute_text_hash(source_req.title, source_req.description)
            tgt_hash = compute_text_hash(target_req.title, target_req.description)

            # Check if suggestion already exists in DB
            existing = await self.suggestion_repo.get_existing_edge(
                project_id=project_id,
                source_id=source_id,
                target_id=target_id,
                rel_type=rel_type,
            )

            if existing:
                # If existing is SUGGESTED: update scores & evidence
                if existing.status == SuggestionStatus.SUGGESTED:
                    existing.confidence_score = cand["confidence_score"]
                    existing.evidence_explanation = cand["evidence_explanation"]
                    existing.suggested_resolution = cand.get("suggested_resolution")
                    existing.source_hash = src_hash
                    existing.target_hash = tgt_hash
                    await self.suggestion_repo.update(existing)
                    updated_count += 1

                # Mandatory Adjustment 1: Material Change Reconsideration
                elif existing.status in (SuggestionStatus.REJECTED, SuggestionStatus.DISMISSED):
                    if existing.source_hash != src_hash or existing.target_hash != tgt_hash:
                        # Material change detected! Reconsider suggestion
                        existing.status = SuggestionStatus.SUGGESTED
                        existing.confidence_score = cand["confidence_score"]
                        existing.evidence_explanation = (
                            f"[Reconsidered after requirement update] {cand['evidence_explanation']}"
                        )
                        existing.suggested_resolution = cand.get("suggested_resolution")
                        existing.source_hash = src_hash
                        existing.target_hash = tgt_hash
                        existing.rejected_at = None
                        existing.dismissal_reason = None
                        await self.suggestion_repo.update(existing)
                        reconsidered_count += 1
                # If ACCEPTED: leave as ACCEPTED
            else:
                # Insert new suggestion
                sug = RequirementSuggestion(
                    id=uuid4(),
                    project_id=project_id,
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=rel_type,
                    status=SuggestionStatus.SUGGESTED,
                    confidence_score=cand["confidence_score"],
                    conflict_category=cand.get("conflict_category"),
                    evidence_explanation=cand["evidence_explanation"],
                    suggested_resolution=cand.get("suggested_resolution"),
                    source_hash=src_hash,
                    target_hash=tgt_hash,
                    detector_version="1.0.0",
                )
                await self.suggestion_repo.create(sug)
                new_count += 1

        all_suggestions = await self.suggestion_repo.get_all_by_project(project_id)
        dtos = [SuggestionResponse.model_validate(s) for s in all_suggestions]

        logger.info(
            "Intelligence scan for project %s complete: %d new, %d updated, %d reconsidered",
            project_id,
            new_count,
            updated_count,
            reconsidered_count,
        )

        return ScanResponse(
            project_id=project_id,
            scanned_requirements_count=len(reqs),
            new_suggestions_created=new_count,
            existing_suggestions_updated=updated_count,
            reconsidered_suggestions_count=reconsidered_count,
            total_suggestions=len(all_suggestions),
            suggestions=dtos,
        )

    def _detect_all_candidates(self, reqs: List[Requirement]) -> List[Dict]:
        """Engine combining numeric conflict parser, ID reference parser, and constraint checkers."""
        candidates: List[Dict] = []

        for i in range(len(reqs)):
            for j in range(i + 1, len(reqs)):
                r1, r2 = reqs[i], reqs[j]

                # 1. Check Explicit Requirement ID references (e.g., FR-001, FR-101, NFR-002, REQ-12, US-014)
                for source, target in [(r1, r2), (r2, r1)]:
                    ref_id = self._extract_requirement_id(target)
                    if ref_id:
                        pattern = r"\b" + re.escape(ref_id) + r"\b"
                        if re.search(pattern, source.description, re.IGNORECASE):
                            candidates.append({
                                "source_id": source.id,
                                "target_id": target.id,
                                "source_req": source,
                                "target_req": target,
                                "type": RelationshipType.DEPENDS_ON,
                                "confidence_score": 0.90,
                                "conflict_category": None,
                                "evidence_explanation": (
                                    f"Specification '{source.title}' explicitly references requirement ID '{ref_id}' "
                                    f"in its description text: \"{source.description[:100]}\"."
                                ),
                                "suggested_resolution": "Verify that dependency link is active.",
                            })

                # 2. Check Numeric Constraint & Range Conflicts
                num_conflict = self._check_numeric_conflict(r1, r2)
                if num_conflict:
                    candidates.append(num_conflict)

                # 3. Check Mandatory vs Optional Behavior Contradiction
                modal_conflict = self._check_modal_conflict(r1, r2)
                if modal_conflict:
                    candidates.append(modal_conflict)

        return candidates

    def _check_numeric_conflict(self, r1: Requirement, r2: Requirement) -> Optional[Dict]:
        """Detect numeric clashes e.g., 'exactly 8 characters' vs 'at least 12 characters'."""
        text1 = f"{r1.title} {r1.description}".lower()
        text2 = f"{r2.title} {r2.description}".lower()

        # Regex to capture numeric metric + unit (e.g. 8 characters, 12 characters, 200 ms)
        pattern = r"(exactly|at least|minimum|maximum|under|less than|greater than)?\s*(\d+)\s*(character|char|ms|millisecond|second|user|port|mb|gb|percent|%)"
        m1 = re.search(pattern, text1)
        m2 = re.search(pattern, text2)

        if m1 and m2:
            qual1, val1_str, unit1 = m1.groups()
            qual2, val2_str, unit2 = m2.groups()
            val1, val2 = int(val1_str), int(val2_str)

            # Standardize unit
            unit1_norm = "character" if "char" in unit1 else ("ms" if "ms" in unit1 or "milli" in unit1 else unit1)
            unit2_norm = "character" if "char" in unit2 else ("ms" if "ms" in unit2 or "milli" in unit2 else unit2)

            if unit1_norm == unit2_norm:
                qual1 = (qual1 or "").strip()
                qual2 = (qual2 or "").strip()

                # Clash 1: Exactly X vs At least Y (where X < Y or X != Y)
                is_clash = False
                reason = ""

                if qual1 == "exactly" and qual2 in ("at least", "minimum") and val1 < val2:
                    is_clash = True
                    reason = (
                        f"'{r1.title}' specifies exactly {val1} {unit1_norm}s, while '{r2.title}' "
                        f"specifies a minimum of {val2} {unit2_norm}s. These constraints cannot both be satisfied."
                    )
                elif qual2 == "exactly" and qual1 in ("at least", "minimum") and val2 < val1:
                    is_clash = True
                    reason = (
                        f"'{r2.title}' specifies exactly {val2} {unit2_norm}s, while '{r1.title}' "
                        f"specifies a minimum of {val1} {unit1_norm}s. These constraints cannot both be satisfied."
                    )
                elif qual1 == "exactly" and qual2 == "exactly" and val1 != val2:
                    is_clash = True
                    reason = (
                        f"'{r1.title}' specifies exactly {val1} {unit1_norm}s, while '{r2.title}' "
                        f"specifies exactly {val2} {unit2_norm}s. Contradictory exact limits."
                    )

                if is_clash:
                    return {
                        "source_id": r1.id,
                        "target_id": r2.id,
                        "source_req": r1,
                        "target_req": r2,
                        "type": RelationshipType.CONFLICTS_WITH,
                        "confidence_score": 0.95,
                        "conflict_category": "Numeric Constraint Clash",
                        "evidence_explanation": reason,
                        "suggested_resolution": f"Align exact requirement limits across specifications ({r1.title} vs {r2.title}).",
                    }
        return None

    def _check_modal_conflict(self, r1: Requirement, r2: Requirement) -> Optional[Dict]:
        """Detect mandatory vs optional behavior contradiction."""
        text1 = f"{r1.title} {r1.description}".lower()
        text2 = f"{r2.title} {r2.description}".lower()

        # Shared keyword check (e.g. multi-factor authentication, mfa, guest access)
        shared_keywords = ["multi-factor", "mfa", "guest", "encryption", "export"]
        for kw in shared_keywords:
            if kw in text1 and kw in text2:
                is_r1_mandatory = any(w in text1 for w in ["shall", "must", "required", "mandatory"])
                is_r2_optional = any(w in text2 for w in ["optional", "may", "not required"])

                if is_r1_mandatory and is_r2_optional:
                    return {
                        "source_id": r1.id,
                        "target_id": r2.id,
                        "source_req": r1,
                        "target_req": r2,
                        "type": RelationshipType.CONFLICTS_WITH,
                        "confidence_score": 0.80,
                        "conflict_category": "Mandatory vs Optional Conflict",
                        "evidence_explanation": (
                            f"'{r1.title}' specifies mandatory '{kw}' behavior, whereas "
                            f"'{r2.title}' states that '{kw}' is optional or not required."
                        ),
                        "suggested_resolution": "Clarify compliance policy to harmonize mandatory status.",
                    }
        return None

    async def get_suggestions(
        self,
        user: User,
        project_id: UUID,
        status_filter: Optional[SuggestionStatus] = None,
        rel_type_filter: Optional[RelationshipType] = None,
        min_confidence: Optional[float] = None,
    ) -> List[SuggestionResponse]:
        """Get suggestions for a project with optional filtering."""
        await self._verify_project_ownership(project_id, user)
        items = await self.suggestion_repo.get_all_by_project(
            project_id=project_id,
            status=status_filter,
            rel_type=rel_type_filter,
            min_confidence=min_confidence,
        )
        return [SuggestionResponse.model_validate(s) for s in items]

    async def accept_suggestion(
        self, user: User, project_id: UUID, suggestion_id: UUID
    ) -> SuggestionResponse:
        """Accept suggestion -> creates active Knowledge Graph edge via GraphService & sets status ACCEPTED."""
        await self._verify_project_ownership(project_id, user)
        sug = await self.suggestion_repo.get_by_id_and_project(suggestion_id, project_id)
        if not sug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Suggestion not found",
            )

        # Reuse GraphService to create actual requirement relationship edge (enforces cycle prevention & symmetric canonical order)
        await self.graph_service.create_relationship(
            user=user,
            project_id=project_id,
            request=RelationshipCreateRequest(
                source_id=sug.source_id,
                target_id=sug.target_id,
                type=sug.relationship_type,
                metadata={"accepted_from_suggestion_id": str(sug.id)},
            ),
        )

        sug.status = SuggestionStatus.ACCEPTED
        updated = await self.suggestion_repo.update(sug)
        logger.info("Accepted suggestion %s -> created Knowledge Graph edge", suggestion_id)
        return SuggestionResponse.model_validate(updated)

    async def reject_suggestion(
        self, user: User, project_id: UUID, suggestion_id: UUID, reason: Optional[str] = None
    ) -> SuggestionResponse:
        """Reject suggestion -> sets status REJECTED & records dismissal timestamp & reason."""
        await self._verify_project_ownership(project_id, user)
        sug = await self.suggestion_repo.get_by_id_and_project(suggestion_id, project_id)
        if not sug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Suggestion not found",
            )

        sug.status = SuggestionStatus.REJECTED
        sug.dismissal_reason = reason
        sug.rejected_at = datetime.now(timezone.utc)
        updated = await self.suggestion_repo.update(sug)
        logger.info("Rejected suggestion %s", suggestion_id)
        return SuggestionResponse.model_validate(updated)

    async def get_intelligence_summary(
        self, user: User, project_id: UUID
    ) -> IntelligenceSummaryResponse:
        """Get project-level intelligence analytics & orphan requirements count."""
        await self._verify_project_ownership(project_id, user)

        reqs = await self.req_repo.get_all_by_project(project_id)
        all_sugs = await self.suggestion_repo.get_all_by_project(project_id)
        all_edges = await self.rel_repo.get_all_by_project(project_id)

        # Orphan detection: requirement with 0 graph relationships and 0 accepted suggestions
        connected_ids = set()
        for e in all_edges:
            connected_ids.add(e.source_id)
            connected_ids.add(e.target_id)

        orphan_count = sum(1 for r in reqs if r.id not in connected_ids)

        conflicts_count = sum(
            1 for s in all_sugs if s.status == SuggestionStatus.SUGGESTED and s.relationship_type == RelationshipType.CONFLICTS_WITH
        )
        unresolved_deps_count = sum(
            1 for s in all_sugs if s.status == SuggestionStatus.SUGGESTED and s.relationship_type == RelationshipType.DEPENDS_ON
        )
        high_conf_count = sum(
            1 for s in all_sugs if s.status == SuggestionStatus.SUGGESTED and s.confidence_score >= 0.80
        )

        conf_dist = {
            "high": sum(1 for s in all_sugs if s.status == SuggestionStatus.SUGGESTED and s.confidence_score >= 0.80),
            "medium": sum(1 for s in all_sugs if s.status == SuggestionStatus.SUGGESTED and 0.50 <= s.confidence_score < 0.80),
            "low": sum(1 for s in all_sugs if s.status == SuggestionStatus.SUGGESTED and s.confidence_score < 0.50),
        }

        return IntelligenceSummaryResponse(
            project_id=project_id,
            total_conflicts=conflicts_count,
            unresolved_dependency_suggestions=unresolved_deps_count,
            orphan_requirements_count=orphan_count,
            high_confidence_issues_count=high_conf_count,
            confidence_distribution=conf_dist,
        )
