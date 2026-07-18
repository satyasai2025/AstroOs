"""
AstroOS — Knowledge Graph Domain Objects (Phase D, Module 12 Extension)

Thin, read-optimised presentation layer over the OntologyRegistry. The
registry itself is the storage + direct-lookup surface (see
apps/api/services/ontology_registry.py); this module adds the
graph-shaped primitives the HTTP layer returns so the frontend can
render an entity + its relationships without knowing about ontology
internals.

Two primitives mirror the registry's entities/relationships exactly:
  - GraphNode:        one ontology entity, flattened for JSON.
  - GraphRelationship: one typed, directed edge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GraphNode:
    """A knowledge-graph node — a flattened ontology entity."""

    id: str
    label: str
    type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphRelationship:
    """A typed, directed edge between two graph nodes."""

    source_id: str
    target_id: str
    relationship_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Entity:
    """A graph node together with its direct relationships."""

    node: GraphNode
    relationships: tuple[GraphRelationship, ...] = ()
