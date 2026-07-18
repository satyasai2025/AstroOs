"""
AstroOS — Knowledge Graph API Schemas (Phase D)

Pydantic response models for the graph HTTP surface. Mirrors the
domain GraphNode / GraphRelationship primitives.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class NodeResponse(BaseModel):
    id: str
    label: str
    type: str
    metadata: dict[str, Any] = {}


class RelationshipResponse(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str
    metadata: dict[str, Any] = {}


class EntityResponse(BaseModel):
    """An entity together with its direct relationships."""

    node: NodeResponse
    relationships: list[RelationshipResponse] = []


class RelationshipListResponse(BaseModel):
    relationships: list[RelationshipResponse] = []
    total: int = 0
