"""
AstroOS — KnowledgeGraphEngine Unit Tests (Phase D, Module 12 Extension)

Tests the graph engine built on top of the OntologyRegistry. We build a
minimal hand-crafted registry for basic contract tests, and a real
`build_default_ontology()` registry for the integration-flavoured
completeness tests (no DB, no network — all in-memory constants).
"""

from __future__ import annotations

import pytest

from apps.api.domain.graph import Entity, GraphNode, GraphRelationship
from apps.api.domain.ontology import OntologyEntity, OntologyRelationship
from apps.api.services.knowledge_graph_engine import KnowledgeGraphEngine
from apps.api.services.ontology_registry import OntologyRegistry


# ── Minimal hand-built registry ───────────────────────────────────────────────

def _minimal_registry() -> OntologyRegistry:
    """A small registry with 3 entities and 2 relationships for unit tests."""
    reg = OntologyRegistry()
    reg.add_entity(OntologyEntity(
        entity_id="GRAHA-SUN", entity_type="Graha", name="Sun",
        metadata={"natural_classification": "malefic"},
    ))
    reg.add_entity(OntologyEntity(
        entity_id="RASHI-ARIES", entity_type="Rashi", name="Aries",
        metadata={"element": "fire"},
    ))
    reg.add_entity(OntologyEntity(
        entity_id="GRAHA-MOON", entity_type="Graha", name="Moon",
        metadata={"natural_classification": "benefic"},
    ))
    reg.add_relationship(OntologyRelationship(
        subject_id="GRAHA-SUN",
        relationship_type="ExaltedIn",
        object_id="RASHI-ARIES",
        metadata={"exact_degree": 10},
    ))
    reg.add_relationship(OntologyRelationship(
        subject_id="GRAHA-MOON",
        relationship_type="Owns",
        object_id="RASHI-ARIES",
    ))
    return reg


@pytest.fixture
def minimal_engine() -> KnowledgeGraphEngine:
    return KnowledgeGraphEngine(_minimal_registry())


# ── Entity lookup ─────────────────────────────────────────────────────────────

class TestGetEntity:
    def test_known_entity_returns_node(self, minimal_engine):
        result = minimal_engine.get_entity("GRAHA-SUN")
        assert result is not None
        assert isinstance(result, Entity)
        assert result.node.id == "GRAHA-SUN"
        assert result.node.label == "Sun"
        assert result.node.type == "Graha"
        assert result.node.metadata["natural_classification"] == "malefic"

    def test_unknown_entity_returns_none(self, minimal_engine):
        assert minimal_engine.get_entity("DOES-NOT-EXIST") is None

    def test_entity_includes_direct_relationships(self, minimal_engine):
        result = minimal_engine.get_entity("GRAHA-SUN")
        assert len(result.relationships) == 1
        rel = result.relationships[0]
        assert isinstance(rel, GraphRelationship)
        assert rel.source_id == "GRAHA-SUN"
        assert rel.target_id == "RASHI-ARIES"
        assert rel.relationship_type == "ExaltedIn"
        assert rel.metadata["exact_degree"] == 10

    def test_object_entity_also_includes_relationship(self, minimal_engine):
        # RASHI-ARIES is the *object* in both relationships; should appear.
        result = minimal_engine.get_entity("RASHI-ARIES")
        assert len(result.relationships) == 2

    def test_entity_with_no_relationships(self, minimal_engine):
        # GRAHA-MOON has an Owns relationship, not zero — but let's test
        # isolation: add an entity with no relationships.
        reg = OntologyRegistry()
        reg.add_entity(OntologyEntity(
            entity_id="ORPHAN-1", entity_type="Test", name="Orphan",
        ))
        engine = KnowledgeGraphEngine(reg)
        result = engine.get_entity("ORPHAN-1")
        assert result is not None
        assert len(result.relationships) == 0


# ── Relationship listing ──────────────────────────────────────────────────────

class TestGetRelationships:
    def test_no_filters_returns_all(self, minimal_engine):
        rels = minimal_engine.get_relationships()
        assert len(rels) == 2
        assert all(isinstance(r, GraphRelationship) for r in rels)

    def test_filter_by_relationship_type(self, minimal_engine):
        rels = minimal_engine.get_relationships(relationship_type="ExaltedIn")
        assert len(rels) == 1
        assert rels[0].relationship_type == "ExaltedIn"

    def test_filter_by_source_type(self, minimal_engine):
        rels = minimal_engine.get_relationships(source_type="Graha")
        assert len(rels) == 2  # both Sun→Aries and Moon→Aries

    def test_filter_by_both(self, minimal_engine):
        rels = minimal_engine.get_relationships(
            source_type="Graha", relationship_type="Owns"
        )
        assert len(rels) == 1
        assert rels[0].source_id == "GRAHA-MOON"

    def test_nonexistent_type_returns_empty(self, minimal_engine):
        rels = minimal_engine.get_relationships(relationship_type="Imaginary")
        assert rels == []


# ── Default ontology completeness ─────────────────────────────────────────────

class TestDefaultOntology:
    """Exercises build_default_ontology() — real in-memory data, no DB."""

    @pytest.fixture(scope="class")
    @classmethod
    def default_engine(cls):
        from apps.api.services.ontology_registry import build_default_ontology
        return KnowledgeGraphEngine(build_default_ontology())

    def test_graha_sun_exists(self, default_engine):
        entity = default_engine.get_entity("GRAHA-SUN")
        assert entity is not None
        assert entity.node.type == "Graha"

    def test_graha_sun_has_dignity_relationships(self, default_engine):
        entity = default_engine.get_entity("GRAHA-SUN")
        rel_types = {r.relationship_type for r in entity.relationships}
        # Sun owns Leo and is exalted in Aries.
        assert "ExaltedIn" in rel_types
        assert "Owns" in rel_types

    def test_graha_rashi_relationships_present(self, default_engine):
        rels = default_engine.get_relationships(
            source_type="Graha", relationship_type="Owns"
        )
        assert len(rels) >= 9  # all 9 grahas own at least one sign

    def test_stats_entity_and_relationship_counts(self, default_engine):
        stats = default_engine.stats()
        # Lower bounds confirmed against the real registry.
        # 9 grahas + 12 rashi + 12 bhava + 27 nakshatra + 108 pada
        #   + vargas + yogas + balas + dashas + aspects + karakas + events ≥ 250
        assert stats["entities"] >= 250
        assert stats["relationships"] >= 200
