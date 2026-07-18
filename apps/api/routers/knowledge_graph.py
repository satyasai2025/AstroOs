"""
AstroOS — Knowledge Graph Router (Phase D, Module 12 Extension)

HTTP adapter layer over KnowledgeGraphEngine. No business logic lives here —
only request/response mapping and HTTP error translation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from apps.api.dependencies import get_knowledge_graph_engine
from apps.api.domain.graph import Entity
from apps.api.schemas.knowledge_graph import (
    EntityResponse,
    NodeResponse,
    RelationshipListResponse,
    RelationshipResponse,
)

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


def _node_response(node) -> NodeResponse:
    return NodeResponse(
        id=node.id,
        label=node.label,
        type=node.type,
        metadata=dict(node.metadata),
    )


def _relationship_response(rel) -> RelationshipResponse:
    return RelationshipResponse(
        source_id=rel.source_id,
        target_id=rel.target_id,
        relationship_type=rel.relationship_type,
        metadata=dict(rel.metadata),
    )


@router.get("/entity/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str = Path(..., description="Ontology entity ID, e.g. GRAHA-SUN"),
    engine=Depends(get_knowledge_graph_engine),
) -> EntityResponse:
    """
    Return a single entity together with the relationships where it appears
    as subject or object.
    """
    entity: Entity | None = engine.get_entity(entity_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{entity_id}' not found in knowledge graph.",
        )
    return EntityResponse(
        node=_node_response(entity.node),
        relationships=[_relationship_response(r) for r in entity.relationships],
    )


@router.get("/relationships", response_model=RelationshipListResponse)
async def list_relationships(
    source_type: str | None = Query(
        None, description="Filter by source entity type (e.g. Graha, Rashi)"
    ),
    relationship_type: str | None = Query(
        None,
        description="Filter by relationship type (e.g. Owns, ExaltedIn)",
    ),
    engine=Depends(get_knowledge_graph_engine),
) -> RelationshipListResponse:
    """
    Return a list of relationships, optionally filtered by source entity
    type and/or relationship type.
    """
    rels = engine.get_relationships(source_type=source_type, relationship_type=relationship_type)
    return RelationshipListResponse(
        relationships=[_relationship_response(r) for r in rels],
        total=len(rels),
    )