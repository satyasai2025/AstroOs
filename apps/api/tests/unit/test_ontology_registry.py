"""
AstroOS — Ontology Registry Unit Tests (Module 12)
"""

import pytest

from apps.api.domain.ontology import OntologyEntity, OntologyRelationship
from apps.api.services.ontology_registry import OntologyRegistry, build_default_ontology


def test_add_and_get_entity():
    registry = OntologyRegistry()
    entity = OntologyEntity(entity_id="GRAHA-SUN", entity_type="Graha", name="Sun")
    registry.add_entity(entity)
    assert registry.get_entity("GRAHA-SUN") == entity


def test_get_entity_missing_returns_none():
    registry = OntologyRegistry()
    assert registry.get_entity("NONEXISTENT") is None


def test_duplicate_entity_id_rejected():
    registry = OntologyRegistry()
    registry.add_entity(OntologyEntity(entity_id="GRAHA-SUN", entity_type="Graha", name="Sun"))
    with pytest.raises(ValueError):
        registry.add_entity(OntologyEntity(entity_id="GRAHA-SUN", entity_type="Graha", name="Sun (dup)"))


def test_all_entities_filters_by_type():
    registry = OntologyRegistry()
    registry.add_entity(OntologyEntity(entity_id="GRAHA-SUN", entity_type="Graha", name="Sun"))
    registry.add_entity(OntologyEntity(entity_id="RASHI-ARIES", entity_type="Rashi", name="Aries"))
    grahas = registry.all_entities("Graha")
    assert len(grahas) == 1
    assert grahas[0].entity_id == "GRAHA-SUN"


def test_all_entities_no_filter_returns_everything():
    registry = OntologyRegistry()
    registry.add_entity(OntologyEntity(entity_id="A", entity_type="Graha", name="A"))
    registry.add_entity(OntologyEntity(entity_id="B", entity_type="Rashi", name="B"))
    assert len(registry.all_entities()) == 2


def test_relationships_for_finds_subject_and_object_matches():
    registry = OntologyRegistry()
    rel = OntologyRelationship(subject_id="GRAHA-MARS", relationship_type="Owns", object_id="RASHI-ARIES")
    registry.add_relationship(rel)
    assert registry.relationships_for("GRAHA-MARS") == [rel]
    assert registry.relationships_for("RASHI-ARIES") == [rel]
    assert registry.relationships_for("GRAHA-VENUS") == []


def test_all_relationships_filters_by_type():
    registry = OntologyRegistry()
    registry.add_relationship(OntologyRelationship("A", "Owns", "B"))
    registry.add_relationship(OntologyRelationship("A", "ExaltedIn", "C"))
    owns_only = registry.all_relationships("Owns")
    assert len(owns_only) == 1
    assert owns_only[0].relationship_type == "Owns"


def test_all_relationships_no_filter_returns_everything():
    registry = OntologyRegistry()
    registry.add_relationship(OntologyRelationship("A", "Owns", "B"))
    registry.add_relationship(OntologyRelationship("A", "ExaltedIn", "C"))
    assert len(registry.all_relationships()) == 2


def test_entity_and_relationship_counts():
    registry = OntologyRegistry()
    registry.add_entity(OntologyEntity(entity_id="A", entity_type="Graha", name="A"))
    registry.add_relationship(OntologyRelationship("A", "Owns", "B"))
    assert registry.entity_count() == 1
    assert registry.relationship_count() == 1


@pytest.fixture(scope="module")
def ontology():
    return build_default_ontology()


def test_all_12_entity_types_present(ontology):
    types_present = {e.entity_type for e in ontology.all_entities()}
    assert types_present == {
        "Graha", "Rashi", "Bhava", "Nakshatra", "Pada", "Yoga",
        "Bala", "Dasha", "Aspect", "Karaka", "Varga", "Event",
    }


def test_graha_count_is_9(ontology):
    assert len(ontology.all_entities("Graha")) == 9


def test_rashi_count_is_12(ontology):
    assert len(ontology.all_entities("Rashi")) == 12


def test_bhava_count_is_12(ontology):
    assert len(ontology.all_entities("Bhava")) == 12


def test_nakshatra_count_is_27(ontology):
    assert len(ontology.all_entities("Nakshatra")) == 27


def test_pada_count_is_108(ontology):
    assert len(ontology.all_entities("Pada")) == 108


def test_yoga_count_matches_module_8_registry(ontology):
    from apps.api.services.yoga_registry import all_yogas
    from apps.api.services import yogas as _yogas  # noqa: F401

    assert len(ontology.all_entities("Yoga")) == len(all_yogas())


def test_bala_count_matches_shadbala_implemented_components(ontology):
    from apps.api.services.shadbala_engine import ShadbalaEngine

    assert len(ontology.all_entities("Bala")) == len(ShadbalaEngine().implemented_components())


def test_dasha_count_is_6(ontology):
    assert len(ontology.all_entities("Dasha")) == 6


def test_varga_includes_d1_through_d60(ontology):
    varga_ids = {e.entity_id for e in ontology.all_entities("Varga")}
    assert "VARGA-D1" in varga_ids
    assert "VARGA-D9" in varga_ids
    assert "VARGA-D60" in varga_ids


def test_mars_owns_aries_and_scorpio(ontology):
    owns = [r for r in ontology.relationships_for("GRAHA-MARS") if r.relationship_type == "Owns"]
    owned_rashis = {r.object_id for r in owns}
    assert owned_rashis == {"RASHI-ARIES", "RASHI-SCORPIO"}


def test_mars_exalted_in_capricorn_at_28_degrees(ontology):
    exalted = [r for r in ontology.relationships_for("GRAHA-MARS") if r.relationship_type == "ExaltedIn"]
    assert len(exalted) == 1
    assert exalted[0].object_id == "RASHI-CAPRICORN"
    assert exalted[0].metadata["exact_degree"] == 28.0


def test_mars_debilitated_in_cancer(ontology):
    debilitated = [r for r in ontology.relationships_for("GRAHA-MARS") if r.relationship_type == "DebilitatedIn"]
    assert len(debilitated) == 1
    assert debilitated[0].object_id == "RASHI-CANCER"


def test_ashwini_ruled_by_ketu(ontology):
    entity = ontology.get_entity("NAKSHATRA-ASHWINI")
    assert entity.metadata["vimshottari_lord"] == "ketu"


def test_ashwini_ruled_by_relationship_matches_metadata(ontology):
    ruled_by = [r for r in ontology.relationships_for("NAKSHATRA-ASHWINI") if r.relationship_type == "RuledBy"]
    assert len(ruled_by) == 1
    assert ruled_by[0].object_id == "GRAHA-KETU"


def test_ruchaka_yoga_entity_matches_module_8_definition(ontology):
    from apps.api.services.yoga_registry import get_yoga
    from apps.api.services import yogas as _yogas  # noqa: F401

    entity = ontology.get_entity("BPHS-PM-001")
    definition = get_yoga("BPHS-PM-001")
    assert entity is not None
    assert entity.name == definition.name
    assert entity.metadata["source_text"] == definition.source_text
    assert entity.metadata["requires"] == list(definition.requires)


def test_pada_entities_link_to_their_nakshatra(ontology):
    part_of = [r for r in ontology.relationships_for("PADA-ASHWINI-1") if r.relationship_type == "PartOf"]
    assert len(part_of) == 1
    assert part_of[0].object_id == "NAKSHATRA-ASHWINI"


def test_karaka_signifies_for_matching_graha(ontology):
    signifies = [r for r in ontology.relationships_for("KARAKA-JUPITER") if r.relationship_type == "SignifiesFor"]
    assert len(signifies) == 1
    assert signifies[0].object_id == "GRAHA-JUPITER"


def test_bhava_category_tags_match_yoga_predicates_constants(ontology):
    from apps.api.services.yoga_predicates import KENDRA_HOUSES, TRIKONA_HOUSES

    for house in range(1, 13):
        entity = ontology.get_entity(f"BHAVA-{house}")
        tags = entity.metadata["category_tags"]
        assert ("kendra" in tags) == (house in KENDRA_HOUSES)
        assert ("trikona" in tags) == (house in TRIKONA_HOUSES)


def test_no_new_classical_facts_asserted_beyond_existing_constants(ontology):
    from packages.shared.constants import OWN_SIGNS

    total_own_relationships = len(ontology.all_relationships("Owns"))
    expected = sum(len(rashis) for rashis in OWN_SIGNS.values())
    assert total_own_relationships == expected


def test_build_default_ontology_is_deterministic():
    ontology_a = build_default_ontology()
    ontology_b = build_default_ontology()
    assert ontology_a.entity_count() == ontology_b.entity_count()
    assert ontology_a.relationship_count() == ontology_b.relationship_count()
    assert {e.entity_id for e in ontology_a.all_entities()} == {e.entity_id for e in ontology_b.all_entities()}
