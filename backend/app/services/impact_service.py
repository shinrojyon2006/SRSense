"""
Requirement Change Impact & Risk Simulator Service —
Graph-Based Impact Propagation, Ephemeral What-If Simulation, Change Type Classification,
Explainable Risk Scoring Engine ($0-100$), and Persisted Impact Reports.
"""

from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.impact_report import ChangeType, RequirementImpactReport
from app.models.relationship import RequirementRelationship, RelationshipType
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.models.user import User
from app.repositories.impact_repository import ImpactRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.requirement_repository import RequirementRepository
from app.schemas.impact import (
    ImpactedRequirementItem,
    ImpactReportResponse,
    ProjectRiskSummaryResponse,
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
)
from app.services.intelligence_service import IntelligenceService
from app.utils.logger import get_logger

logger = get_logger("srsense.impact_service")


def normalize_text(text: str) -> str:
    """Normalize text for cosmetic vs behavioral change comparison."""
    if not text:
        return ""
    # Strip whitespace, lower case, collapse multiple spaces
    return " ".join(text.strip().lower().split())


def classify_change(
    existing: Optional[Requirement],
    proposed_title: str,
    proposed_desc: str,
    proposed_type: Optional[RequirementType],
    proposed_priority: Optional[RequirementPriority],
    proposed_status: Optional[RequirementStatus],
) -> ChangeType:
    """Classify requirement change into COSMETIC, METADATA, or BEHAVIORAL."""
    if not existing:
        return ChangeType.BEHAVIORAL

    norm_existing_title = normalize_text(existing.title)
    norm_existing_desc = normalize_text(existing.description)
    norm_prop_title = normalize_text(proposed_title)
    norm_prop_desc = normalize_text(proposed_desc)

    text_changed = (norm_existing_title != norm_prop_title) or (norm_existing_desc != norm_prop_desc)

    metadata_changed = (
        (proposed_type and proposed_type != existing.type)
        or (proposed_priority and proposed_priority != existing.priority)
        or (proposed_status and proposed_status != existing.status)
    )

    if text_changed:
        return ChangeType.BEHAVIORAL
    elif metadata_changed:
        return ChangeType.METADATA
    else:
        return ChangeType.COSMETIC


class ImpactService:
    """Service layer for Change Impact & Risk Simulation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.impact_repo = ImpactRepository(db)
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)
        self.rel_repo = RelationshipRepository(db)
        self.intel_service = IntelligenceService(db)

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

    async def simulate_what_if(
        self, user: User, project_id: UUID, request: WhatIfSimulationRequest
    ) -> WhatIfSimulationResponse:
        """Run ephemeral What-If change simulation in memory (STRICTLY NO DB MUTATION)."""
        await self._verify_project_ownership(project_id, user)

        existing_req: Optional[Requirement] = None
        if request.requirement_id:
            existing_req = await self.req_repo.get_by_id_and_project(request.requirement_id, project_id)

        # 1. Mandatory Refinement 2: Classify Change Type
        change_type = classify_change(
            existing=existing_req,
            proposed_title=request.proposed_title,
            proposed_desc=request.proposed_description,
            proposed_type=request.proposed_type,
            proposed_priority=request.proposed_priority,
            proposed_status=request.proposed_status,
        )

        all_reqs = await self.req_repo.get_all_by_project(project_id)
        all_edges = await self.rel_repo.get_all_by_project(project_id)
        req_map: Dict[UUID, Requirement] = {r.id: r for r in all_reqs}

        # 2. Graph Impact Propagation Algorithm (with 100% cycle safety)
        direct_items: List[ImpactedRequirementItem] = []
        transitive_items: List[ImpactedRequirementItem] = []
        max_depth_reached = 0

        if change_type != ChangeType.COSMETIC and request.requirement_id:
            target_id = request.requirement_id
            max_depth = request.max_depth or 3

            # Adjacency list: u -> v where change to u affects v
            adj: Dict[UUID, List[UUID]] = defaultdict(list)
            for edge in all_edges:
                if edge.type in (RelationshipType.DEPENDS_ON, RelationshipType.DERIVED_FROM):
                    # If X depends_on Y, change to Y affects X (Y -> X)
                    adj[edge.target_id].append(edge.source_id)

            visited: Set[UUID] = {target_id}
            queue: deque[Tuple[UUID, int, List[UUID]]] = deque([(target_id, 0, [target_id])])

            while queue:
                curr_id, depth, path = queue.popleft()
                if depth > 0:
                    max_depth_reached = max(max_depth_reached, depth)
                    req_obj = req_map.get(curr_id)
                    if req_obj:
                        item = ImpactedRequirementItem(
                            requirement_id=curr_id,
                            title=req_obj.title,
                            type=req_obj.type,
                            priority=req_obj.priority,
                            depth=depth,
                            path=path,
                            impact_reason=f"Impacted via {depth}-hop dependency path: {' -> '.join([req_map.get(p, Requirement(title=str(p))).title for p in path])}",
                        )
                        if depth == 1:
                            direct_items.append(item)
                        else:
                            transitive_items.append(item)

                if depth < max_depth:
                    for neighbor in adj.get(curr_id, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append((neighbor, depth + 1, path + [neighbor]))

        # 3. Conflict Re-evaluation in Memory
        new_conflicts: List[Dict] = []
        if change_type == ChangeType.BEHAVIORAL and request.requirement_id:
            # Construct ephemeral proposed requirement
            ephemeral_req = Requirement(
                id=request.requirement_id,
                project_id=project_id,
                title=request.proposed_title,
                description=request.proposed_description,
                type=request.proposed_type or (existing_req.type if existing_req else RequirementType.FUNCTIONAL),
                priority=request.proposed_priority or (existing_req.priority if existing_req else RequirementPriority.MEDIUM),
                status=request.proposed_status or (existing_req.status if existing_req else RequirementStatus.DRAFT),
            )

            # Check potential numeric & modal clashes against other requirements in project
            for other_req in all_reqs:
                if other_req.id != request.requirement_id:
                    num_clash = self.intel_service._check_numeric_conflict(ephemeral_req, other_req)
                    if num_clash:
                        new_conflicts.append({
                            "conflicting_requirement_id": str(other_req.id),
                            "conflicting_title": other_req.title,
                            "category": num_clash["conflict_category"],
                            "evidence": num_clash["evidence_explanation"],
                        })

        # 4. Explainable Risk Scoring Engine ($0 - 100$)
        multiplier = 1.0 if change_type == ChangeType.BEHAVIORAL else (0.4 if change_type == ChangeType.METADATA else 0.0)

        highest_priority_score = 0
        all_affected = direct_items + transitive_items
        if all_affected:
            priorities = [item.priority.value for item in all_affected]
            if "critical" in priorities:
                highest_priority_score = 25
            elif "high" in priorities:
                highest_priority_score = 15
            elif "medium" in priorities:
                highest_priority_score = 5

        raw_score = (
            len(direct_items) * 10
            + len(transitive_items) * 5
            + max_depth_reached * 5
            + highest_priority_score
            + len(new_conflicts) * 20
        ) * multiplier

        risk_score = round(min(100.0, max(0.0, raw_score)), 1)

        if risk_score >= 90.0:
            risk_level = "CRITICAL"
        elif risk_score >= 70.0:
            risk_level = "HIGH"
        elif risk_score >= 36.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Evidence Reasoning Breakdown
        evidence_notes: List[str] = [
            f"Change classification: {change_type.value.upper()} (Impact Multiplier: {multiplier}x).",
            f"Predicted downstream impact: {len(direct_items)} direct requirement(s), {len(transitive_items)} transitive requirement(s).",
        ]
        if new_conflicts:
            evidence_notes.append(f"Triggered {len(new_conflicts)} new potential constraint conflict(s).")
        if max_depth_reached > 0:
            evidence_notes.append(f"Maximum dependency propagation depth reached: {max_depth_reached} hop(s).")

        return WhatIfSimulationResponse(
            project_id=project_id,
            target_requirement_id=request.requirement_id,
            change_type=change_type,
            risk_score=risk_score,
            risk_level=risk_level,
            direct_affected_count=len(direct_items),
            transitive_affected_count=len(transitive_items),
            direct_affected_requirements=direct_items,
            transitive_affected_requirements=transitive_items,
            new_conflicts_triggered=new_conflicts,
            conflicts_resolved=[],
            evidence_reasoning=evidence_notes,
            is_ephemeral=True,
        )

    async def generate_impact_report(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> ImpactReportResponse:
        """Calculate and persist formal Requirement Impact Report into PostgreSQL."""
        await self._verify_project_ownership(project_id, user)
        req = await self.req_repo.get_by_id_and_project(requirement_id, project_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found",
            )

        sim_req = WhatIfSimulationRequest(
            requirement_id=requirement_id,
            proposed_title=req.title,
            proposed_description=req.description,
            proposed_type=req.type,
            proposed_priority=req.priority,
            proposed_status=req.status,
        )
        sim_res = await self.simulate_what_if(user, project_id, sim_req)

        report = RequirementImpactReport(
            id=uuid4(),
            project_id=project_id,
            requirement_id=requirement_id,
            change_type=sim_res.change_type,
            risk_score=sim_res.risk_score,
            risk_level=sim_res.risk_level,
            direct_affected_count=sim_res.direct_affected_count,
            transitive_affected_count=sim_res.transitive_affected_count,
            conflicts_count=len(sim_res.new_conflicts_triggered),
            report_data_json=sim_res.model_dump(mode="json"),
        )
        saved = await self.impact_repo.create(report)
        logger.info("Persisted Impact Report %s for requirement %s", saved.id, requirement_id)
        return ImpactReportResponse.model_validate(saved)

    async def get_impact_analysis_for_requirement(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> WhatIfSimulationResponse:
        """Get impact propagation analysis for an existing requirement."""
        await self._verify_project_ownership(project_id, user)
        req = await self.req_repo.get_by_id_and_project(requirement_id, project_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found",
            )

        sim_req = WhatIfSimulationRequest(
            requirement_id=requirement_id,
            proposed_title=req.title,
            proposed_description=req.description,
            proposed_type=req.type,
            proposed_priority=req.priority,
            proposed_status=req.status,
        )
        return await self.simulate_what_if(user, project_id, sim_req)

    async def get_project_risk_summary(
        self, user: User, project_id: UUID
    ) -> ProjectRiskSummaryResponse:
        """Get project-wide risk summary analytics and high-risk rankings."""
        await self._verify_project_ownership(project_id, user)
        reqs = await self.req_repo.get_all_by_project(project_id)

        simulations: List[Tuple[Requirement, WhatIfSimulationResponse]] = []
        for r in reqs:
            sim = await self.get_impact_analysis_for_requirement(user, project_id, r.id)
            simulations.append((r, sim))

        if not simulations:
            return ProjectRiskSummaryResponse(
                project_id=project_id,
                average_project_risk_score=0.0,
                high_risk_requirements_count=0,
                risk_level_breakdown={"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
                top_high_risk_requirements=[],
            )

        total_score = sum(s[1].risk_score for s in simulations)
        avg_score = round(total_score / len(simulations), 1)

        breakdown = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for _, s in simulations:
            breakdown[s.risk_level] = breakdown.get(s.risk_level, 0) + 1

        high_risk_count = breakdown["HIGH"] + breakdown["CRITICAL"]

        # Sort top high risk requirements
        sorted_sims = sorted(simulations, key=lambda item: item[1].risk_score, reverse=True)
        top_list = [
            {
                "requirement_id": str(r.id),
                "title": r.title,
                "type": r.type.value,
                "priority": r.priority.value,
                "risk_score": sim.risk_score,
                "risk_level": sim.risk_level,
                "direct_affected_count": sim.direct_affected_count,
            }
            for r, sim in sorted_sims[:5]
        ]

        return ProjectRiskSummaryResponse(
            project_id=project_id,
            average_project_risk_score=avg_score,
            high_risk_requirements_count=high_risk_count,
            risk_level_breakdown=breakdown,
            top_high_risk_requirements=top_list,
        )
