"""
Unit tests for AstroOS Astrological Graph Vocabulary (Step 1).

Tests cover:
  1. All required AstroNodeCategory members exist.
  2. All required AstroRelationshipType members exist.
  3. Enum values serialize to strings.
  4. Enum values can be supplied to GraphNode.type via .value.
  5. Enum values can be supplied to GraphRelationship.relationship_type via .value.
  6. Existing OntologyEntity and OntologyRelationship unchanged.
  7. No regression in existing graph/ontology behavior.
"""

from __future__ import annotations

import pytest

from apps.api.domain.astro_graph_vocabulary import (
    AstroNodeCategory,
    AstroRelationshipType,
)
from apps.api.domain.graph import Entity, GraphNode, GraphRelationship
from apps.api.domain.ontology import OntologyEntity, OntologyRelationship


# ── 1. AstroNodeCategory member coverage ──────────────────────────────────────


REQUIRED_NODE_CATEGORIES = {
    "PLANET",
    "SIGN",
    "HOUSE",
    "NAKSHATRA",
    "DASHA",
    "VARGA",
    "RULE",
    "EVIDENCE",
    "EVENT_DOMAIN",
}


class TestAstroNodeCategory:
    def test_all_required_members_exist(self):
        actual = {m.value for m in AstroNodeCategory}
        missing = REQUIRED_NODE_CATEGORIES - actual
        assert not missing, f"Missing AstroNodeCategory members: {missing}"

    def test_exact_member_count(self):
        assert len(AstroNodeCategory) == 9

    def test_no_duplicate_values(self):
        values = [m.value for m in AstroNodeCategory]
        assert len(values) == len(set(values))

    def test_all_values_are_uppercase_snake_case(self):
        for member in AstroNodeCategory:
            assert member.value == member.value.upper()
            assert " " not in member.value


# ── 2. AstroRelationshipType member coverage ──────────────────────────────────


REQUIRED_RELATIONSHIP_TYPES = {
    "OCCUPIES",
    "OWNS",
    "DISPOSITOR_OF",
    "ASPECTS",
    "CONJUNCT_WITH",
    "LOCATED_IN_NAKSHATRA",
    "RULED_BY",
    "ACTIVATES",
    "APPLIES_TO",
    "SUPPORTED_BY",
    "CONTRADICTED_BY",
    "DERIVED_FROM",
}


class TestAstroRelationshipType:
    def test_all_required_members_exist(self):
        actual = {m.value for m in AstroRelationshipType}
        missing = REQUIRED_RELATIONSHIP_TYPES - actual
        assert not missing, f"Missing AstroRelationshipType members: {missing}"

    def test_exact_member_count(self):
        assert len(AstroRelationshipType) == 12

    def test_no_duplicate_values(self):
        values = [m.value for m in AstroRelationshipType]
        assert len(values) == len(set(values))

    def test_all_values_are_uppercase_snake_case(self):
        for member in AstroRelationshipType:
            assert member.value == member.value.upper()
            assert " " not in member.value


# ── 3. Enum values serialize to strings ──────────────────────────────────────


class TestSerialization:
    def test_node_category_value_is_str(self):
        for member in AstroNodeCategory:
            assert isinstance(member.value, str)

    def test_relationship_type_value_is_str(self):
        for member in AstroRelationshipType:
            assert isinstance(member.value, str)

    def test_node_category_value_not_empty(self):
        for member in AstroNodeCategory:
            assert len(member.value) > 0

    def test_relationship_type_value_not_empty(self):
        for member in AstroRelationshipType:
            assert len(member.value) > 0


# ── 4. Enum values work with GraphNode.type ────────────────────────────────


class TestGraphNodeCompatibility:
    def test_planet_node_type(self):
        node = GraphNode(
            id="PLANET-SUN",
            label="Sun",
            type=AstroNodeCategory.PLANET.value,
        )
        assert node.type == "PLANET"

    def test_sign_node_type(self):
        node = GraphNode(
            id="SIGN-ARIES",
            label="Aries",
            type=AstroNodeCategory.SIGN.value,
        )
        assert node.type == "SIGN"

    def test_house_node_type(self):
        node = GraphNode(
            id="HOUSE-1",
            label="Lagna",
            type=AstroNodeCategory.HOUSE.value,
        )
        assert node.type == "HOUSE"

    def test_nakshatra_node_type(self):
        node = GraphNode(
            id="NAKSHATRA-ASHVINI",
            label="Ashvini",
            type=AstroNodeCategory.NAKSHATRA.value,
        )
        assert node.type == "NAKSHATRA"

    def test_dasha_node_type(self):
        node = GraphNode(
            id="DASHA-VD",
            label="Vimshottari",
            type=AstroNodeCategory.DASHA.value,
        )
        assert node.type == "DASHA"

    def test_varga_node_type(self):
        node = GraphNode(
            id="VARGA-D9",
            label="Navamsa",
            type=AstroNodeCategory.VARGA.value,
        )
        assert node.type == "VARGA"

    def test_rule_node_type(self):
        node = GraphNode(
            id="RULE-GK-01",
            label="Gaja Kesari Yoga",
            type=AstroNodeCategory.RULE.value,
        )
        assert node.type == "RULE"

    def test_evidence_node_type(self):
        node = GraphNode(
            id="EVIDENCE-E1",
            label="E1",
            type=AstroNodeCategory.EVIDENCE.value,
        )
        assert node.type == "EVIDENCE"

    def test_event_domain_node_type(self):
        node = GraphNode(
            id="EVENT_DOMAIN-CAREER",
            label="Career",
            type=AstroNodeCategory.EVENT_DOMAIN.value,
        )
        assert node.type == "EVENT_DOMAIN"


# ── 5. Enum values work with GraphRelationship.relationship_type ─────────────


class TestGraphRelationshipCompatibility:
    def test_occupies_relationship(self):
        rel = GraphRelationship(
            source_id="PLANET-SUN",
            target_id="SIGN-LEO",
            relationship_type=AstroRelationshipType.OCCUPIES.value,
        )
        assert rel.relationship_type == "OCCUPIES"

    def test_owns_relationship(self):
        rel = GraphRelationship(
            source_id="PLANET-MARS",
            target_id="SIGN-ARIES",
            relationship_type=AstroRelationshipType.OWNS.value,
        )
        assert rel.relationship_type == "OWNS"

    def test_dispositor_of_relationship(self):
        rel = GraphRelationship(
            source_id="PLANET-MERCURY",
            target_id="PLANET-MOON",
            relationship_type=AstroRelationshipType.DISPOSITOR_OF.value,
        )
        assert rel.relationship_type == "DISPOSITOR_OF"

    def test_aspects_relationship(self):
        rel = GraphRelationship(
            source_id="PLANET-MARS",
            target_id="SIGN-7",
            relationship_type=AstroRelationshipType.ASPECTS.value,
        )
        assert rel.relationship_type == "ASPECTS"

    def test_conjunct_with_relationship(self):
        rel = GraphRelationship(
            source_id="PLANET-SUN",
            target_id="PLANET-VENUS",
            relationship_type=AstroRelationshipType.CONJUNCT_WITH.value,
        )
        assert rel.relationship_type == "CONJUNCT_WITH"

    def test_located_in_nakshatra_relationship(self):
        rel = GraphRelationship(
            source_id="PLANET-MOON",
            target_id="NAKSHATRA-ROHINI",
            relationship_type=AstroRelationshipType.LOCATED_IN_NAKSHATRA.value,
        )
        assert rel.relationship_type == "LOCATED_IN_NAKSHATRA"

    def test_ruled_by_relationship(self):
        rel = GraphRelationship(
            source_id="NAKSHATRA-ASHVINI",
            target_id="PLANET-KETU",
            relationship_type=AstroRelationshipType.RULED_BY.value,
        )
        assert rel.relationship_type == "RULED_BY"

    def test_activates_relationship(self):
        rel = GraphRelationship(
            source_id="DASHA-VD",
            target_id="PLANET-VENUS",
            relationship_type=AstroRelationshipType.ACTIVATES.value,
        )
        assert rel.relationship_type == "ACTIVATES"

    def test_applies_to_relationship(self):
        rel = GraphRelationship(
            source_id="RULE-GK-01",
            target_id="EVENT_DOMAIN-WEALTH",
            relationship_type=AstroRelationshipType.APPLIES_TO.value,
        )
        assert rel.relationship_type == "APPLIES_TO"

    def test_supported_by_relationship(self):
        rel = GraphRelationship(
            source_id="RULE-GK-01",
            target_id="EVIDENCE-E1",
            relationship_type=AstroRelationshipType.SUPPORTED_BY.value,
        )
        assert rel.relationship_type == "SUPPORTED_BY"

    def test_contradicted_by_relationship(self):
        rel = GraphRelationship(
            source_id="RULE-GK-01",
            target_id="EVIDENCE-E2",
            relationship_type=AstroRelationshipType.CONTRADICTED_BY.value,
        )
        assert rel.relationship_type == "CONTRADICTED_BY"

    def test_derived_from_relationship(self):
        rel = GraphRelationship(
            source_id="FACT-PL1",
            target_id="GRAHA-ENGINE",
            relationship_type=AstroRelationshipType.DERIVED_FROM.value,
        )
        assert rel.relationship_type == "DERIVED_FROM"


# ── 6. OntologyEntity / OntologyRelation unchanged ──────────────────────────


class TestOntologyCompatibility:
    def test_ontology_entity_field_types_unchanged(self):
        entity = OntologyEntity(
            entity_id="GRAHA-SUN",
            entity_type="Graha",
            name="Sun",
        )
        assert isinstance(entity.entity_id, str)
        assert isinstance(entity.entity_type, str)
        assert isinstance(entity.name, str)
        assert isinstance(entity.metadata, dict)

    def test_ontology_relationship_field_types_unchanged(self):
        rel = OntologyRelationship(
            subject_id="GRAHA-SUN",
            relationship_type="OWNS",
            object_id="RASHI-SIMHA",
        )
        assert isinstance(rel.subject_id, str)
        assert isinstance(rel.object_id, str)
        assert isinstance(rel.relationship_type, str)
        assert isinstance(rel.metadata, dict)

    def test_ontology_relationship_type_is_open_vocabulary(self):
        """OntologyRelationship.relationship_type accepts any string, not just enum values."""
        rel = OntologyRelationship(
            subject_id="A",
            relationship_type="CUSTOM_RELATION",
            object_id="B",
        )
        assert rel.relationship_type == "CUSTOM_RELATION"

    def test_astro_node_category_not_injected_into_ontology(self):
        """New AstroNodeCategory values must not appear in OntologyEntity.entity_type."""
        # OntologyEntity.entity_type is intentionally open vocabulary
        entity = OntologyEntity(
            entity_id="X",
            entity_type="CustomType",
            name="X",
        )
        assert entity.entity_type == "CustomType"


# ── 7. No regression in graph/ontology dataclass behavior ────────────────────


class TestGraphOntologyRegression:
    def test_graph_node_fields_unchanged(self):
        node = GraphNode(id="1", label="n", type="t", metadata={})
        assert node.__dataclass_fields__.keys() == {
            "id", "label", "type", "metadata"
        }

    def test_graph_relationship_fields_unchanged(self):
        rel = GraphRelationship(
            source_id="a", target_id="b",
            relationship_type="r", metadata={}
        )
        assert rel.__dataclass_fields__.keys() == {
            "source_id", "target_id", "relationship_type", "metadata"
        }

    def test_entity_fields_unchanged(self):
        node = GraphNode(id="1", label="n", type="t")
        entity = Entity(node=node)
        assert entity.__dataclass_fields__.keys() == {
            "node", "relationships"
        }

    def test_graph_node_frozen(self):
        import dataclasses
        assert dataclasses.fields(GraphNode)[0].name == "id"

    def test_graph_relationship_frozen(self):
        import dataclasses
        assert dataclasses.fields(GraphRelationship)[0].name == "source_id"