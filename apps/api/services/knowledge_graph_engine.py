"""
AstroOS — Knowledge Graph Engine (Phase D, Module 12 Extension)

Read-only presentation layer over the OntologyRegistry. The registry is
the storage + direct-lookup surface (its own module); this engine adds
graph-shaped accessors (entity + relationships, filtered relationship
listing) so the HTTP layer stays thin.

Stateless — holds a reference to a built OntologyRegistry.
"""

from __future__ import annotations

from apps.api.domain.graph import Entity, GraphNode, GraphRelationship
from apps.api.services.ontology_registry import OntologyRegistry


def _to_node(entity) -> GraphNode:
    return GraphNode(
        id=entity.entity_id,
        label=entity.name,
        type=entity.entity_type,
        metadata=dict(entity.metadata),
    )


def _to_relationship(rel) -> GraphRelationship:
    return GraphRelationship(
        source_id=rel.subject_id,
        target_id=rel.object_id,
        relationship_type=rel.relationship_type,
        metadata=dict(rel.metadata) if rel.metadata else {},
    )


class KnowledgeGraphEngine:
    """Graph-shaped read access over an OntologyRegistry."""

    def __init__(self, registry: OntologyRegistry) -> None:
        self._registry = registry

    def get_entity(self, entity_id: str) -> Entity | None:
        """
        Return an entity with its direct relationships, or None if the
        entity does not exist.
        """
        entity = self._registry.get_entity(entity_id)
        if entity is None:
            return None
        rels = [_to_relationship(r) for r in self._registry.relationships_for(entity_id)]
        return Entity(node=_to_node(entity), relationships=tuple(rels))

    def get_relationships(
        self,
        source_type: str | None = None,
        relationship_type: str | None = None,
    ) -> list[GraphRelationship]:
        """
        Return relationships filtered by (optional) source entity type and/or
        relationship type. To filter by source_type the registry must be
        scanned: relationships are looked up by subject/object id, so we
        resolve each relationship's source entity type via the registry.
        """
        result: list[GraphRelationship] = []
        for rel in self._registry.all_relationships(relationship_type):
            if source_type is not None:
                source_entity = self._registry.get_entity(rel.subject_id)
                if source_entity is None or source_entity.entity_type != source_type:
                    continue
            result.append(_to_relationship(rel))
        return result

    def stats(self) -> dict[str, int]:
        return {
            "entities": self._registry.entity_count(),
            "relationships": self._registry.relationship_count(),
        }
