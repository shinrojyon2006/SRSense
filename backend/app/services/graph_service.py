"""
Requirement Knowledge Graph Service — Graph Operations, Dependency Traversal,
Cycle Prevention, Symmetric Conflict Handling, and Heuristic Relationship Discovery.
"""

from collections import defaultdict, deque
from typing import Dict, List, Set
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.relationship import RequirementRelationship, RelationshipType
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.requirement_repository import RequirementRepository
from app.schemas.graph import (
    DependencyChainResponse,
    GraphEdge,
    GraphNode,
    ProjectGraphResponse,
    RelationshipCreateRequest,
    RelationshipResponse,
    RequirementRelationshipsResponse,
    SuggestRelationshipsResponse,
    SuggestedRelationshipItem,
)
from app.utils.logger import get_logger

logger = get_logger("srsense.graph_service")


def check_path_exists(start_node: UUID, goal_node: UUID, adjacency: Dict[UUID, List[UUID]]) -> bool:
    """BFS check to determine if goal_node is reachable from start_node."""
    if start_node == goal_node:
        return True

    visited: Set[UUID] = set()
    queue: deque[UUID] = deque([start_node])

    while queue:
        curr = queue.popleft()
        if curr == goal_node:
            return True
        if curr in visited:
            continue
        visited.add(curr)
        for neighbor in adjacency.get(curr, []):
            if neighbor not in visited:
                queue.append(neighbor)

    return False


class GraphService:
    """Service layer for Knowledge Graph operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rel_repo = RelationshipRepository(db)
        self.project_repo = ProjectRepository(db)
        self.req_repo = RequirementRepository(db)

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

    async def create_relationship(
        self, user: User, project_id: UUID, request: RelationshipCreateRequest
    ) -> RelationshipResponse:
        """Create a graph relationship edge between two requirements inside a project."""
        await self._verify_project_ownership(project_id, user)

        # 1. Reject self-referential loop
        if request.source_id == request.target_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Self-referential relationships are not allowed.",
            )

        # 2. Verify both requirements exist and belong to project
        source_req = await self.req_repo.get_by_id_and_project(request.source_id, project_id)
        target_req = await self.req_repo.get_by_id_and_project(request.target_id, project_id)

        if not source_req or not target_req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both requirement specifications were not found in this project.",
            )

        source_id = request.source_id
        target_id = request.target_id

        # 3. Mandatory Adjustment 2: Symmetric Conflict Canonical Ordering
        if request.type == RelationshipType.CONFLICTS_WITH:
            canonical_source = min(source_id, target_id, key=lambda x: str(x))
            canonical_target = max(source_id, target_id, key=lambda x: str(x))
            source_id, target_id = canonical_source, canonical_target

        # 4. Check if duplicate relationship already exists
        existing = await self.rel_repo.get_existing_edge(
            project_id=project_id,
            source_id=source_id,
            target_id=target_id,
            rel_type=request.type,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Relationship edge already exists between these specifications.",
            )

        # 5. Mandatory Adjustment 1: Dependency Cycle Prevention (depends_on)
        if request.type == RelationshipType.DEPENDS_ON:
            # Build adjacency list of existing depends_on edges: u -> v (u depends on v)
            existing_deps = await self.rel_repo.get_all_depends_on_by_project(project_id)
            adj: Dict[UUID, List[UUID]] = defaultdict(list)
            for edge in existing_deps:
                adj[edge.source_id].append(edge.target_id)

            # If adding source_id -> target_id, check if target_id can ALREADY reach source_id
            if check_path_exists(start_node=target_id, goal_node=source_id, adjacency=adj):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Circular dependency detected: adding this relationship would create a cycle.",
                )

        # Create relationship edge
        rel = RequirementRelationship(
            id=uuid4(),
            project_id=project_id,
            source_id=source_id,
            target_id=target_id,
            type=request.type,
            metadata_json=request.metadata,
        )
        created = await self.rel_repo.create(rel)
        logger.info(
            "Created relationship %s (%s -> %s) for project %s",
            request.type.value,
            source_id,
            target_id,
            project_id,
        )
        return RelationshipResponse.model_validate(created)

    async def get_project_graph(self, user: User, project_id: UUID) -> ProjectGraphResponse:
        """Get complete project graph node and edge breakdown."""
        await self._verify_project_ownership(project_id, user)

        reqs = await self.req_repo.get_all_by_project(project_id)
        edges = await self.rel_repo.get_all_by_project(project_id)

        nodes = [
            GraphNode(
                id=r.id,
                title=r.title,
                type=r.type,
                priority=r.priority,
                status=r.status,
            )
            for r in reqs
        ]

        graph_edges = [
            GraphEdge(
                id=e.id,
                source=e.source_id,
                target=e.target_id,
                type=e.type,
            )
            for e in edges
        ]

        return ProjectGraphResponse(
            project_id=project_id,
            total_nodes=len(nodes),
            total_edges=len(graph_edges),
            nodes=nodes,
            edges=graph_edges,
        )

    async def get_relationships_for_requirement(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> RequirementRelationshipsResponse:
        """Get incoming, outgoing, and symmetric conflict relationships for a specific requirement."""
        await self._verify_project_ownership(project_id, user)
        req = await self.req_repo.get_by_id_and_project(requirement_id, project_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found",
            )

        all_edges = await self.rel_repo.get_by_requirement(project_id, requirement_id)

        outgoing: List[RelationshipResponse] = []
        incoming: List[RelationshipResponse] = []
        conflicts: List[RelationshipResponse] = []

        for e in all_edges:
            rel_dto = RelationshipResponse.model_validate(e)
            if e.type == RelationshipType.CONFLICTS_WITH:
                conflicts.append(rel_dto)
            elif e.source_id == requirement_id:
                outgoing.append(rel_dto)
            else:
                incoming.append(rel_dto)

        return RequirementRelationshipsResponse(
            requirement_id=requirement_id,
            outgoing=outgoing,
            incoming=incoming,
            conflicts=conflicts,
        )

    async def delete_relationship(
        self, user: User, project_id: UUID, relationship_id: UUID
    ) -> None:
        """Delete a relationship edge."""
        await self._verify_project_ownership(project_id, user)
        edge = await self.rel_repo.get_by_id_and_project(relationship_id, project_id)
        if not edge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relationship edge not found",
            )
        await self.rel_repo.delete(edge)
        logger.info("Deleted relationship edge %s", relationship_id)

    async def query_dependencies(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> DependencyChainResponse:
        """Query upstream dependencies (what requirement_id needs) and downstream impacted requirements."""
        await self._verify_project_ownership(project_id, user)
        req = await self.req_repo.get_by_id_and_project(requirement_id, project_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found",
            )

        all_deps = await self.rel_repo.get_all_depends_on_by_project(project_id)

        upstream: List[RelationshipResponse] = []
        downstream: List[RelationshipResponse] = []

        for edge in all_deps:
            dto = RelationshipResponse.model_validate(edge)
            if edge.source_id == requirement_id:
                upstream.append(dto)
            elif edge.target_id == requirement_id:
                downstream.append(dto)

        return DependencyChainResponse(
            root_requirement_id=requirement_id,
            upstream_dependencies=upstream,
            impacted_downstream=downstream,
        )

    async def query_conflicts(
        self, user: User, project_id: UUID, requirement_id: UUID
    ) -> List[RelationshipResponse]:
        """Query conflicting requirements for a specific specification."""
        res = await self.get_relationships_for_requirement(user, project_id, requirement_id)
        return res.conflicts

    async def suggest_relationships(
        self, user: User, project_id: UUID
    ) -> SuggestRelationshipsResponse:
        """Foundation for automatic heuristic relationship discovery."""
        await self._verify_project_ownership(project_id, user)
        reqs = await self.req_repo.get_all_by_project(project_id)

        suggestions: List[SuggestedRelationshipItem] = []

        for i in range(len(reqs)):
            for j in range(i + 1, len(reqs)):
                r1, r2 = reqs[i], reqs[j]

                # Check explicit ID references (e.g. R1 description mentions R2's original_req_id)
                if r2.original_req_id and r2.original_req_id.lower() in r1.description.lower():
                    suggestions.append(
                        SuggestedRelationshipItem(
                            source_id=r1.id,
                            target_id=r2.id,
                            type=RelationshipType.DEPENDS_ON,
                            reason=f"Requirement '{r1.title}' explicitly references ID '{r2.original_req_id}' in its text.",
                            confidence_score=0.85,
                        )
                    )

                # Check non-functional latency/metric contradiction
                if r1.type.value == "non_functional" and r2.type.value == "non_functional":
                    if "milliseconds" in r1.description.lower() and "milliseconds" in r2.description.lower():
                        suggestions.append(
                            SuggestedRelationshipItem(
                                source_id=r1.id,
                                target_id=r2.id,
                                type=RelationshipType.CONFLICTS_WITH,
                                reason="Both specifications define performance latency metrics in milliseconds.",
                                confidence_score=0.70,
                            )
                        )

        return SuggestRelationshipsResponse(
            project_id=project_id,
            total_suggestions=len(suggestions),
            suggestions=suggestions,
        )
