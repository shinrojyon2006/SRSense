"""
Requirement Change Impact & Risk Simulator Service —
Graph-Based Impact Propagation, Ephemeral What-If Simulation, Deterministic Change Classification,
Constraint & Semantic Delta Analysis, Explainable Weighted Risk Scoring Engine ($0-100$), and Persisted Impact Reports.
"""

from collections import defaultdict, deque
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.codebase import RequirementCodeLink
from app.models.impact_report import ChangeType, RequirementImpactReport
from app.models.relationship import RequirementRelationship, RelationshipType
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.models.traceability import RequirementTestLink
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


def extract_measurable_constraints(text: str) -> List[Dict[str, Any]]:
    """
    Extract numeric thresholds, SLAs, interaction limits, percentages, time limits from text.
    Returns list of dicts: {"category": str, "value": float, "raw": str, "unit": str}
    """
    if not text:
        return []

    constraints = []
    text_lower = text.lower()

    # Pattern 1: Time thresholds (e.g., "200 milliseconds", "500 ms", "30 seconds")
    time_matches = re.finditer(
        r'(\d+(?:\.\d+)?)\s*(milliseconds|millisecond|ms|seconds|second|sec|s|minutes|minute|min|hours|hour|h)\b',
        text_lower,
    )
    for m in time_matches:
        constraints.append({
            "category": "time_threshold",
            "value": float(m.group(1)),
            "unit": m.group(2),
            "raw": m.group(0),
        })

    # Pattern 2: Percentages (e.g., "95%", "99.9%")
    pct_matches = re.finditer(r'(\d+(?:\.\d+)?)\s*%', text_lower)
    for m in pct_matches:
        constraints.append({
            "category": "percentage",
            "value": float(m.group(1)),
            "unit": "%",
            "raw": m.group(0),
        })

    # Pattern 3: Counts & Interaction limits (e.g., "no more than 3 user interactions", "max 5 retries")
    limit_matches = re.finditer(
        r'(?:maximum|max|limit of|no more than|at most|up to|at least|minimum|min)\s*(\d+)\s*([a-z_]+)?',
        text_lower,
    )
    for m in limit_matches:
        constraints.append({
            "category": "count_limit",
            "value": float(m.group(1)),
            "unit": m.group(2) or "count",
            "raw": m.group(0),
        })

    # Pattern 4: Standalone interaction/retry/attempt count numbers (e.g. "3 user interactions", "8 interactions")
    standalone_matches = re.finditer(
        r'\b(\d+)\s*(interactions|interaction|retries|retry|attempts|attempt|users|user|requests|request|files|file|mb|gb|kb)\b',
        text_lower,
    )
    for m in standalone_matches:
        raw_str = m.group(0)
        if not any(raw_str in c["raw"] for c in constraints):
            constraints.append({
                "category": "count_limit",
                "value": float(m.group(1)),
                "unit": m.group(2),
                "raw": raw_str,
            })

    return constraints


def compare_measurable_constraints(
    before_text: str, after_text: str
) -> List[Dict[str, Any]]:
    """Compares measurable constraints before vs after and returns detected constraint changes."""
    before_c = extract_measurable_constraints(before_text)
    after_c = extract_measurable_constraints(after_text)

    changes = []
    for b in before_c:
        matched = False
        for a in after_c:
            if b["category"] == a["category"]:
                matched = True
                if b["value"] != a["value"]:
                    change_type = "threshold_relaxed" if a["value"] > b["value"] else "threshold_tightened"
                    changes.append({
                        "field": b["category"],
                        "before": b["raw"],
                        "after": a["raw"],
                        "before_value": b["value"],
                        "after_value": a["value"],
                        "change": change_type,
                        "impact": f"Measurable constraint modified from '{b['raw']}' to '{a['raw']}'",
                    })
                break
        if not matched and after_c:
            pass

    if not changes and before_c and after_c:
        for b in before_c:
            for a in after_c:
                if b["value"] != a["value"]:
                    changes.append({
                        "field": "numeric_constraint",
                        "before": b["raw"],
                        "after": a["raw"],
                        "before_value": b["value"],
                        "after_value": a["value"],
                        "change": "constraint_modified",
                        "impact": f"Numeric constraint changed from '{b['raw']}' to '{a['raw']}'",
                    })
                    break

    return changes


def detect_behavioral_reversal(before_text: str, after_text: str) -> bool:
    """Detect if behavioral polarity has flipped (e.g. allow -> prevent, enable -> disable)."""
    b_norm = normalize_text(before_text)
    a_norm = normalize_text(after_text)

    reversal_pairs = [
        ("allow", "prevent"), ("allow", "forbid"), ("allow", "prohibit"), ("allow", "disallow"),
        ("enable", "disable"), ("permit", "deny"), ("require", "optional"),
        ("must", "must not"), ("shall", "shall not"), ("include", "exclude"),
    ]

    for p1, p2 in reversal_pairs:
        if (p1 in b_norm and p2 in a_norm) or (p2 in b_norm and p1 in a_norm):
            return True
    return False


def normalize_modal_words(text: str) -> str:
    """Normalize requirement modal verbs (shall, must, will, should) to canonical token."""
    norm = normalize_text(text)
    return re.sub(r'\b(shall|must|will|should|can|may)\b', '__MODAL__', norm)


def is_security_related(text: str) -> bool:
    sec_keywords = ["auth", "login", "password", "credential", "token", "jwt", "permission", "role", "encrypt", "session", "access control", "security", "sso", "mfa", "oauth", "anonymous"]
    t_lower = text.lower()
    return any(k in t_lower for k in sec_keywords)


def security_keywords_in(text: str) -> Set[str]:
    sec_keywords = ["auth", "login", "password", "credential", "token", "jwt", "permission", "role", "encrypt", "session", "access control", "security", "sso", "mfa", "oauth", "anonymous"]
    t_lower = text.lower()
    return {k for k in sec_keywords if k in t_lower}


def is_performance_related(text: str) -> bool:
    perf_keywords = ["latency", "response time", "ms", "millisecond", "throughput", "qps", "rps", "concurrency", "rate limit", "performance", "sla", "benchmark"]
    t_lower = text.lower()
    return any(k in t_lower for k in perf_keywords)


def performance_keywords_in(text: str) -> Set[str]:
    perf_keywords = ["latency", "response time", "ms", "millisecond", "throughput", "qps", "rps", "concurrency", "rate limit", "performance", "sla", "benchmark"]
    t_lower = text.lower()
    return {k for k in perf_keywords if k in t_lower}


def classify_change_detailed(
    existing: Optional[Requirement],
    proposed_title: str,
    proposed_desc: str,
    proposed_type: Optional[RequirementType],
    proposed_priority: Optional[RequirementPriority],
    proposed_status: Optional[RequirementStatus],
) -> Tuple[ChangeType, str, List[Dict[str, Any]], List[str], float]:
    """
    Deterministically analyzes requirement edit delta.
    Returns:
      - change_type: ChangeType (COSMETIC, METADATA, BEHAVIORAL)
      - detailed_classification: str (NO_CHANGE, COSMETIC, CONSTRAINT_CHANGE, BEHAVIOR_CHANGE, SECURITY_CHANGE, PERFORMANCE_CHANGE, METADATA_CHANGE)
      - detected_constraint_changes: List[Dict[str, Any]]
      - changed_fields: List[str]
      - intrinsic_risk_score: float
    """
    if not existing:
        return (ChangeType.BEHAVIORAL, "BEHAVIOR_CHANGE", [], ["title", "description"], 25.0)

    norm_existing_title = normalize_text(existing.title)
    norm_existing_desc = normalize_text(existing.description)
    norm_prop_title = normalize_text(proposed_title)
    norm_prop_desc = normalize_text(proposed_desc)

    title_changed = norm_existing_title != norm_prop_title
    desc_changed = norm_existing_desc != norm_prop_desc
    text_changed = title_changed or desc_changed

    type_changed = proposed_type is not None and proposed_type != existing.type
    priority_changed = proposed_priority is not None and proposed_priority != existing.priority
    status_changed = proposed_status is not None and proposed_status != existing.status
    metadata_changed = type_changed or priority_changed or status_changed

    changed_fields = []
    if title_changed:
        changed_fields.append("title")
    if desc_changed:
        changed_fields.append("description")
    if type_changed:
        changed_fields.append("type")
    if priority_changed:
        changed_fields.append("priority")
    if status_changed:
        changed_fields.append("status")

    # If nothing changed at all
    if not text_changed and not metadata_changed:
        return (ChangeType.COSMETIC, "NO_CHANGE", [], [], 0.0)

    # If text is normalized identical and only metadata changed
    if not text_changed and metadata_changed:
        risk = 0.0
        if priority_changed:
            risk += 15.0
        if type_changed:
            risk += 15.0
        if status_changed:
            risk += 10.0

        detail_cls = "PRIORITY_CHANGE" if (priority_changed and not type_changed) else ("TYPE_CHANGE" if (type_changed and not priority_changed) else "METADATA_CHANGE")
        return (ChangeType.METADATA, detail_cls, [], changed_fields, risk)

    # Text changed: Analyze cosmetic vs constraint vs behavioral
    modal_existing = normalize_modal_words(existing.description)
    modal_proposed = normalize_modal_words(proposed_desc)

    clean_existing_modal = re.sub(r'[^\w\s]', '', modal_existing)
    clean_proposed_modal = re.sub(r'[^\w\s]', '', modal_proposed)
    clean_title_e = re.sub(r'[^\w\s]', '', norm_existing_title)
    clean_title_p = re.sub(r'[^\w\s]', '', norm_prop_title)

    constraint_changes = compare_measurable_constraints(existing.description, proposed_desc)
    reversal = detect_behavioral_reversal(existing.description, proposed_desc)

    sec_before = security_keywords_in(existing.description)
    sec_after = security_keywords_in(proposed_desc)
    sec_delta = sec_before != sec_after

    perf_before = performance_keywords_in(existing.description)
    perf_after = performance_keywords_in(proposed_desc)
    perf_delta = perf_before != perf_after or (existing.type in [RequirementType.NON_FUNCTIONAL, RequirementType.SYSTEM] and bool(constraint_changes))

    is_purely_cosmetic = (
        clean_existing_modal == clean_proposed_modal
        and clean_title_e == clean_title_p
        and not constraint_changes
        and not reversal
        and not sec_delta
        and not perf_delta
        and not metadata_changed
    )

    if is_purely_cosmetic:
        return (ChangeType.COSMETIC, "COSMETIC", [], changed_fields, 3.0)

    # Calculate intrinsic risk for material text changes
    intrinsic_risk = 0.0
    if title_changed:
        intrinsic_risk += 10.0
    if desc_changed:
        intrinsic_risk += 15.0

    if constraint_changes:
        intrinsic_risk += 25.0

    if reversal:
        intrinsic_risk += 35.0

    if sec_delta:
        intrinsic_risk += 30.0

    if perf_delta:
        intrinsic_risk += 25.0

    if priority_changed:
        intrinsic_risk += 15.0
    if type_changed:
        intrinsic_risk += 15.0
    if status_changed:
        intrinsic_risk += 10.0

    intrinsic_risk = min(80.0, max(5.0, intrinsic_risk))

    if sec_delta:
        detailed_cls = "SECURITY_CHANGE"
    elif perf_delta or (is_performance_related(proposed_desc) and (constraint_changes or desc_changed)):
        detailed_cls = "PERFORMANCE_CHANGE"
    elif constraint_changes:
        detailed_cls = "CONSTRAINT_CHANGE"
    elif reversal:
        detailed_cls = "BEHAVIOR_CHANGE"
    elif text_changed:
        detailed_cls = "BEHAVIOR_CHANGE"
    elif metadata_changed:
        detailed_cls = "METADATA_CHANGE"
    else:
        detailed_cls = "COSMETIC"

    change_type = ChangeType.BEHAVIORAL if (text_changed or constraint_changes or reversal or sec_delta or perf_delta) else (ChangeType.METADATA if metadata_changed else ChangeType.COSMETIC)

    return (change_type, detailed_cls, constraint_changes, changed_fields, intrinsic_risk)


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

        # Resolve proposed values: fall back to existing requirement's values if not provided
        resolved_title = request.proposed_title or (existing_req.title if existing_req else "New Requirement")
        resolved_desc = request.proposed_description or (existing_req.description if existing_req else "New requirement description.")

        # 1. Deterministic Content & Constraint Delta Analysis
        change_type, detailed_cls, constraint_changes, changed_fields, intrinsic_risk = classify_change_detailed(
            existing=existing_req,
            proposed_title=resolved_title,
            proposed_desc=resolved_desc,
            proposed_type=request.proposed_type,
            proposed_priority=request.proposed_priority,
            proposed_status=request.proposed_status,
        )

        all_reqs = await self.req_repo.get_all_by_project(project_id)
        all_edges = await self.rel_repo.get_all_by_project(project_id)
        req_map: Dict[UUID, Requirement] = {r.id: r for r in all_reqs}

        # Fetch multi-layer downstream artifacts (code links, test links, child reqs)
        linked_code_file_count = 0
        linked_symbol_count = 0
        linked_test_count = 0
        child_req_count = 0

        if request.requirement_id:
            try:
                code_link_res = await self.db.execute(
                    select(RequirementCodeLink).where(RequirementCodeLink.requirement_id == request.requirement_id)
                )
                code_links = list(code_link_res.scalars().all())
                linked_code_file_count = len([cl for cl in code_links if cl.file_id])
                linked_symbol_count = len([cl for cl in code_links if cl.symbol_id])
            except Exception as e:
                logger.warning("Could not fetch code links for impact analysis: %s", e)

            try:
                test_link_res = await self.db.execute(
                    select(RequirementTestLink).where(RequirementTestLink.requirement_id == request.requirement_id)
                )
                test_links = list(test_link_res.scalars().all())
                linked_test_count = len(test_links)
            except Exception as e:
                logger.warning("Could not fetch test links for impact analysis: %s", e)

            try:
                child_req_res = await self.db.execute(
                    select(Requirement).where(Requirement.parent_id == request.requirement_id)
                )
                child_reqs = list(child_req_res.scalars().all())
                child_req_count = len(child_reqs)
            except Exception as e:
                logger.warning("Could not fetch child requirements for impact analysis: %s", e)

        # 2. Graph Impact Propagation Algorithm (with 100% cycle safety)
        direct_items: List[ImpactedRequirementItem] = []
        transitive_items: List[ImpactedRequirementItem] = []
        max_depth_reached = 0

        if detailed_cls != "NO_CHANGE" and request.requirement_id:
            target_id = request.requirement_id
            max_depth = request.max_depth or 3

            adj: Dict[UUID, List[UUID]] = defaultdict(list)
            for edge in all_edges:
                if edge.type in (RelationshipType.DEPENDS_ON, RelationshipType.DERIVED_FROM):
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
        if detailed_cls not in ["NO_CHANGE", "COSMETIC"] and request.requirement_id:
            ephemeral_req = Requirement(
                id=request.requirement_id,
                project_id=project_id,
                title=resolved_title,
                description=resolved_desc,
                type=request.proposed_type or (existing_req.type if existing_req else RequirementType.FUNCTIONAL),
                priority=request.proposed_priority or (existing_req.priority if existing_req else RequirementPriority.MEDIUM),
                status=request.proposed_status or (existing_req.status if existing_req else RequirementStatus.DRAFT),
            )

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

        # 4. Explainable Downstream & Intrinsic Risk Scoring Engine ($0 - 100$)
        downstream_risk = (
            min(30.0, len(direct_items) * 5.0)
            + min(20.0, len(transitive_items) * 2.0)
            + min(25.0, (linked_code_file_count + linked_symbol_count) * 8.0)
            + min(15.0, linked_test_count * 5.0)
            + min(10.0, child_req_count * 5.0)
            + len(new_conflicts) * 20.0
            + max_depth_reached * 5.0
        )

        total_raw = intrinsic_risk + downstream_risk
        risk_score = round(min(100.0, max(0.0, total_raw)), 1)

        if detailed_cls == "NO_CHANGE":
            risk_score = 0.0
            risk_level = "LOW"
        elif risk_score >= 90.0:
            risk_level = "CRITICAL"
        elif risk_score >= 70.0:
            risk_level = "HIGH"
        elif risk_score >= 36.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Evidence Reasoning Breakdown
        evidence_notes: List[str] = [
            f"Change classification: {detailed_cls} (Base Type: {change_type.value.upper()}).",
            f"Intrinsic change risk score: {round(intrinsic_risk, 1)} / 100.",
        ]

        if detailed_cls == "NO_CHANGE":
            evidence_notes.append("No semantic or structural change detected between current and proposed specification.")
        elif detailed_cls == "COSMETIC":
            evidence_notes.append("Only harmless wording/formatting changes detected without material semantic impact.")

        for cc in constraint_changes:
            evidence_notes.append(f"Measurable constraint change detected: {cc['impact']} ({cc['before']} -> {cc['after']}).")

        if existing_req and detect_behavioral_reversal(existing_req.description, resolved_desc):
            evidence_notes.append("BEHAVIORAL_POLARITY_REVERSAL detected: the proposed change reverses the intent of the original requirement.")

        if detailed_cls == "SECURITY_CHANGE":
            evidence_notes.append("SECURITY_CHANGE detected: the proposed change modifies security-related constraints or access control behavior.")

        if "priority" in changed_fields and existing_req:
            evidence_notes.append(f"Priority modified from {existing_req.priority.value.upper()} to {request.proposed_priority.value.upper() if request.proposed_priority else 'N/A'}.")
        if "type" in changed_fields and existing_req:
            evidence_notes.append(f"Type modified from {existing_req.type.value.upper()} to {request.proposed_type.value.upper() if request.proposed_type else 'N/A'}.")
        if "status" in changed_fields and existing_req:
            evidence_notes.append(f"Status modified from {existing_req.status.value.upper()} to {request.proposed_status.value.upper() if request.proposed_status else 'N/A'}.")

        if linked_code_file_count > 0 or linked_symbol_count > 0:
            evidence_notes.append(f"Requirement is mapped to {linked_code_file_count} code file(s) and {linked_symbol_count} AST symbol(s).")
        if linked_test_count > 0:
            evidence_notes.append(f"Requirement is linked to {linked_test_count} verification test artifact(s).")
        if child_req_count > 0:
            evidence_notes.append(f"Requirement is parent to {child_req_count} child requirement(s).")

        evidence_notes.append(
            f"Predicted downstream impact: {len(direct_items)} direct requirement(s), {len(transitive_items)} transitive requirement(s)."
        )

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
            intrinsic_risk_score=round(intrinsic_risk, 1),
            downstream_risk_score=round(downstream_risk, 1),
            changed_fields=changed_fields,
            detected_constraint_changes=constraint_changes,
            detailed_classification=detailed_cls,
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
