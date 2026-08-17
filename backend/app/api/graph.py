"""
Requirement Knowledge Graph REST API router.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import dependencies
from app.models.user import User
from app.schemas.graph import (
    DependencyChainResponse,
    ProjectGraphResponse,
    RelationshipCreateRequest,
    RelationshipResponse,
    RequirementRelationshipsResponse,
    SuggestRelationshipsResponse,
)
from app.services.graph_service import GraphService

router = APIRouter(tags=["Requirement Knowledge Graph"])


@router.post(
    "/projects/{project_id}/graph/relationships",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_relationship(
    project_id: UUID,
    request: RelationshipCreateRequest,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Create a graph relationship edge between two requirements in a project."""
    service = GraphService(db)
    return await service.create_relationship(
        user=current_user, project_id=project_id, request=request
    )


@router.get(
    "/projects/{project_id}/graph/relationships",
    response_model=ProjectGraphResponse,
)
async def get_project_graph(
    project_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Get complete project graph node and edge breakdown."""
    service = GraphService(db)
    return await service.get_project_graph(user=current_user, project_id=project_id)


@router.get(
    "/projects/{project_id}/graph/requirements/{requirement_id}",
    response_model=RequirementRelationshipsResponse,
)
async def get_relationships_for_requirement(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Get outgoing, incoming, and conflict relationships for a specific requirement."""
    service = GraphService(db)
    return await service.get_relationships_for_requirement(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.delete(
    "/projects/{project_id}/graph/relationships/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_relationship(
    project_id: UUID,
    relationship_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Delete a relationship edge."""
    service = GraphService(db)
    await service.delete_relationship(
        user=current_user, project_id=project_id, relationship_id=relationship_id
    )


@router.get(
    "/projects/{project_id}/graph/requirements/{requirement_id}/dependencies",
    response_model=DependencyChainResponse,
)
async def query_dependencies(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Query upstream dependencies and downstream impacted requirements for a specification."""
    service = GraphService(db)
    return await service.query_dependencies(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.get(
    "/projects/{project_id}/graph/requirements/{requirement_id}/conflicts",
    response_model=List[RelationshipResponse],
)
async def query_conflicts(
    project_id: UUID,
    requirement_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Query conflicting requirement specifications."""
    service = GraphService(db)
    return await service.query_conflicts(
        user=current_user, project_id=project_id, requirement_id=requirement_id
    )


@router.post(
    "/projects/{project_id}/graph/suggest-relationships",
    response_model=SuggestRelationshipsResponse,
)
async def suggest_relationships(
    project_id: UUID,
    current_user: User = Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(dependencies.get_db),
):
    """Run automatic heuristic relationship discovery."""
    service = GraphService(db)
    return await service.suggest_relationships(user=current_user, project_id=project_id)
