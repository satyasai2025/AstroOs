"""
AstroOS — Ontology Registry (Module 12)

Deliberately minimal storage + direct lookup only — NOT a query or
inference engine, per explicit scope. `build_default_ontology()`
populates it with the 12 entity types and their relationships, reusing
already-verified data from earlier modules wherever it exists (Module
8's yoga_ids, Module 9's Shadbala component_ids, and the classical
constants tables in packages/shared/constants.py) rather than asserting
new classical facts.
"""

from __future__ import annotations

from apps.api.domain.ontology import OntologyEntity, OntologyRelationship
from packages.shared.enums import Rashi

_RASHI_LIST = [r.value for r in Rashi]
_GRAHA_LIST = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]


class OntologyRegistry:
    """Storage + direct lookup by id only. No traversal, no inference, no querying."""

    def __init__(self) -> None:
        self._entities: dict[str, OntologyEntity] = {}
        self._relationships: list[OntologyRelationship] = []

    def add_entity(self, entity: OntologyEntity) -> None:
        if entity.entity_id in self._entities:
            raise ValueError(f"Duplicate entity_id: {entity.entity_id!r}")
        self._entities[entity.entity_id] = entity

    def add_relationship(self, relationship: OntologyRelationship) -> None:
        self._relationships.append(relationship)

    def get_entity(self, entity_id: str) -> OntologyEntity | None:
        return self._entities.get(entity_id)

    def all_entities(self, entity_type: str | None = None) -> list[OntologyEntity]:
        if entity_type is None:
            return list(self._entities.values())
        return [e for e in self._entities.values() if e.entity_type == entity_type]

    def relationships_for(self, entity_id: str) -> list[OntologyRelationship]:
        """Direct lookup only — every relationship where entity_id is subject OR object."""
        return [
            r for r in self._relationships
            if r.subject_id == entity_id or r.object_id == entity_id
        ]

    def all_relationships(self, relationship_type: str | None = None) -> list[OntologyRelationship]:
        if relationship_type is None:
            return list(self._relationships)
        return [r for r in self._relationships if r.relationship_type == relationship_type]

    def entity_count(self) -> int:
        return len(self._entities)

    def relationship_count(self) -> int:
        return len(self._relationships)


def _populate_graha(registry: OntologyRegistry) -> None:
    from apps.api.services.yoga_predicates import NATURAL_BENEFICS, NATURAL_MALEFICS

    for planet in _GRAHA_LIST:
        nature = "benefic" if planet in NATURAL_BENEFICS else (
            "malefic" if planet in NATURAL_MALEFICS else "neutral"
        )
        registry.add_entity(OntologyEntity(
            entity_id=f"GRAHA-{planet.upper()}",
            entity_type="Graha",
            name=planet.capitalize(),
            metadata={
                "is_luminary": planet in ("sun", "moon"),
                "is_shadow_planet": planet in ("rahu", "ketu"),
                "natural_classification": nature,
            },
        ))


def _populate_rashi(registry: OntologyRegistry) -> None:
    element_by_index = ["fire", "earth", "air", "water"]
    modality_by_index = ["movable", "fixed", "dual"]

    for i, rashi in enumerate(_RASHI_LIST):
        registry.add_entity(OntologyEntity(
            entity_id=f"RASHI-{rashi.upper()}",
            entity_type="Rashi",
            name=rashi.capitalize(),
            metadata={
                "element": element_by_index[i % 4],
                "modality": modality_by_index[i % 3],
                "order": i + 1,
            },
        ))


def _populate_bhava(registry: OntologyRegistry) -> None:
    from apps.api.services.yoga_predicates import KENDRA_HOUSES, TRIKONA_HOUSES

    dusthana_houses = {6, 8, 12}
    upachaya_houses = {3, 6, 10, 11}

    for house in range(1, 13):
        tags = []
        if house in KENDRA_HOUSES:
            tags.append("kendra")
        if house in TRIKONA_HOUSES:
            tags.append("trikona")
        if house in dusthana_houses:
            tags.append("dusthana")
        if house in upachaya_houses:
            tags.append("upachaya")

        registry.add_entity(OntologyEntity(
            entity_id=f"BHAVA-{house}",
            entity_type="Bhava",
            name=f"House {house}",
            metadata={"house_number": house, "category_tags": tags},
        ))


def _populate_nakshatra(registry: OntologyRegistry) -> None:
    from packages.shared.constants import VIMSHOTTARI_NAKSHATRA_LORDS
    from packages.shared.enums import Nakshatra

    nakshatra_list = [n.value for n in Nakshatra]
    for i, nakshatra in enumerate(nakshatra_list):
        registry.add_entity(OntologyEntity(
            entity_id=f"NAKSHATRA-{nakshatra.upper()}",
            entity_type="Nakshatra",
            name=nakshatra.replace("_", " ").title(),
            metadata={"order": i + 1, "vimshottari_lord": VIMSHOTTARI_NAKSHATRA_LORDS[i]},
        ))
        registry.add_relationship(OntologyRelationship(
            subject_id=f"NAKSHATRA-{nakshatra.upper()}",
            relationship_type="RuledBy",
            object_id=f"GRAHA-{VIMSHOTTARI_NAKSHATRA_LORDS[i].upper()}",
            metadata={"dasha_system": "vimshottari"},
        ))


def _populate_pada(registry: OntologyRegistry) -> None:
    """
    108 entities (27 nakshatras x 4 padas). Minimal metadata — this is a
    large mechanical enumeration, not a place with much additional
    classical nuance to attach per-entry.
    """
    from packages.shared.enums import Nakshatra

    for nakshatra in [n.value for n in Nakshatra]:
        for pada_number in range(1, 5):
            registry.add_entity(OntologyEntity(
                entity_id=f"PADA-{nakshatra.upper()}-{pada_number}",
                entity_type="Pada",
                name=f"{nakshatra.replace('_', ' ').title()} Pada {pada_number}",
                metadata={"nakshatra": nakshatra, "pada_number": pada_number},
            ))
            registry.add_relationship(OntologyRelationship(
                subject_id=f"PADA-{nakshatra.upper()}-{pada_number}",
                relationship_type="PartOf",
                object_id=f"NAKSHATRA-{nakshatra.upper()}",
            ))


def _populate_yoga(registry: OntologyRegistry) -> None:
    from apps.api.services.yoga_registry import all_yogas
    from apps.api.services import yogas as _yogas  # noqa: F401 — triggers @register_yoga

    for definition in all_yogas():
        registry.add_entity(OntologyEntity(
            entity_id=definition.yoga_id,
            entity_type="Yoga",
            name=definition.name,
            metadata={
                "category": definition.category,
                "source_text": definition.source_text,
                "rule_version": definition.rule_version,
                "requires": list(definition.requires),
            },
        ))
        for dependency in definition.requires:
            varga_entity_id = f"VARGA-{dependency}"
            if registry.get_entity(varga_entity_id) is not None:
                registry.add_relationship(OntologyRelationship(
                    subject_id=definition.yoga_id,
                    relationship_type="Requires",
                    object_id=varga_entity_id,
                ))


def _populate_technique(registry: OntologyRegistry) -> None:
    """
    Registers the generic Technique framework's catalogue (domain/technique.py
    + services/techniques/) exactly like `_populate_yoga` registers Yogas:
    one entity per technique (latest version only), a `Requires` edge to each
    VARGA entity its `dependencies` names, and an `AppliesTo` edge to each
    EVENT entity its `event_types` names — both only when the target entity
    already exists in the ontology (same discipline `_populate_yoga` uses for
    Varga: never invent an entity here just to link to it).
    """
    from apps.api.services import technique_registry
    from apps.api.services import techniques as _techniques  # noqa: F401 — triggers registration

    latest: dict[str, object] = {}
    for t in technique_registry.all_techniques():
        cur = latest.get(t.technique_id)
        if cur is None or t.version > cur.version:
            latest[t.technique_id] = t

    for definition in latest.values():
        registry.add_entity(OntologyEntity(
            entity_id=f"TECHNIQUE-{definition.technique_id.upper()}",
            entity_type="Technique",
            name=definition.name,
            metadata={
                "tradition": definition.tradition,
                "objective": definition.objective,
                "status": definition.status,
                "provenance": definition.provenance.value,
                "version": definition.version,
                "rule_count": len(definition.rule_refs),
                "event_types": list(definition.event_types),
                "timing_resolution": (
                    definition.timing_resolution.value if definition.timing_resolution else None
                ),
            },
        ))
        for dependency in definition.dependencies:
            varga_entity_id = f"VARGA-{dependency}"
            if registry.get_entity(varga_entity_id) is not None:
                registry.add_relationship(OntologyRelationship(
                    subject_id=f"TECHNIQUE-{definition.technique_id.upper()}",
                    relationship_type="Requires",
                    object_id=varga_entity_id,
                ))
        for event_type in definition.event_types:
            event_entity_id = f"EVENT-{event_type.upper()}"
            if registry.get_entity(event_entity_id) is not None:
                registry.add_relationship(OntologyRelationship(
                    subject_id=f"TECHNIQUE-{definition.technique_id.upper()}",
                    relationship_type="AppliesTo",
                    object_id=event_entity_id,
                ))


def _populate_bala(registry: OntologyRegistry) -> None:
    """
    Uses ShadbalaEngine's own implemented_components() list — the exact
    same source of truth Module 9 itself uses to report what it covers —
    rather than a separately hand-maintained list that could drift.
    """
    from apps.api.services.shadbala_engine import ShadbalaEngine

    component_ids = ShadbalaEngine().implemented_components()
    for component_id in component_ids:
        category = component_id.split(".")[0] if "." in component_id else "kala_bala"
        name = component_id.split(".")[-1].replace("_", " ").title()
        bala_entity_id = f"BALA-{component_id.upper().replace('.', '-')}"
        registry.add_entity(OntologyEntity(
            entity_id=bala_entity_id,
            entity_type="Bala",
            name=name,
            metadata={"category": category, "component_key": component_id},
        ))
        for planet in _GRAHA_LIST[:7]:  # 7 classical grahas evaluated by Shadbala
            graha_id = f"GRAHA-{planet.upper()}"
            if registry.get_entity(graha_id) is not None:
                registry.add_relationship(OntologyRelationship(
                    subject_id=bala_entity_id,
                    relationship_type="Evaluates",
                    object_id=graha_id,
                ))


def _populate_dasha(registry: OntologyRegistry) -> None:
    from packages.shared.constants import VIMSHOTTARI_TOTAL_YEARS

    dasha_systems = {
        "vimshottari": {"total_years": VIMSHOTTARI_TOTAL_YEARS, "basis": "nakshatra"},
        "yogini": {"basis": "nakshatra"},
        "ashtottari": {"total_years": 108, "basis": "nakshatra"},
        "kalachakra": {"basis": "nakshatra_pada"},
        "chara": {"basis": "rashi"},
        "narayana": {"basis": "rashi"},
    }
    for system, metadata in dasha_systems.items():
        registry.add_entity(OntologyEntity(
            entity_id=f"DASHA-{system.upper()}",
            entity_type="Dasha",
            name=system.capitalize(),
            metadata=metadata,
        ))


def _populate_aspect(registry: OntologyRegistry) -> None:
    aspect_types = {
        "conjunction": "0 degrees — same house/sign",
        "opposition": "180 degrees — 7th house aspect, universal to all grahas",
        "trine": "120 degrees",
        "square": "90 degrees",
        "special_graha": "Mars/Jupiter/Saturn's additional classical special aspects",
    }
    for aspect_type, description in aspect_types.items():
        registry.add_entity(OntologyEntity(
            entity_id=f"ASPECT-{aspect_type.upper().replace('_', '-')}",
            entity_type="Aspect",
            name=aspect_type.replace("_", " ").title(),
            metadata={"description": description},
        ))


def _populate_karaka(registry: OntologyRegistry) -> None:
    """
    Naisargika (natural/fixed) Karakas only — each graha's static
    classical significations. Deliberately NOT the Jaimini Chara Karakas
    (Atmakaraka etc.), which are chart-dependent (computed from a
    specific chart's planetary degrees) and so are not a fixed ontology
    fact the way natural significations are.
    """
    significations = {
        "sun": ["soul", "father", "authority", "government", "vitality"],
        "moon": ["mind", "mother", "emotions", "public"],
        "mars": ["siblings", "courage", "land", "conflict"],
        "mercury": ["intellect", "communication", "commerce"],
        "jupiter": ["wisdom", "children", "wealth", "guru", "dharma"],
        "venus": ["spouse", "relationships", "luxury", "arts"],
        "saturn": ["longevity", "career", "discipline", "servants", "sorrow"],
    }
    for planet, sigs in significations.items():
        registry.add_entity(OntologyEntity(
            entity_id=f"KARAKA-{planet.upper()}",
            entity_type="Karaka",
            name=f"{planet.capitalize()} (Naisargika Karaka)",
            metadata={"significations": sigs, "karaka_type": "naisargika"},
        ))
        registry.add_relationship(OntologyRelationship(
            subject_id=f"KARAKA-{planet.upper()}",
            relationship_type="SignifiesFor",
            object_id=f"GRAHA-{planet.upper()}",
        ))


def _populate_varga(registry: OntologyRegistry) -> None:
    from apps.api.services.divisional_engine import SUPPORTED_VARGAS

    all_vargas = {"D1": 1, **SUPPORTED_VARGAS}
    for varga, divisor in all_vargas.items():
        registry.add_entity(OntologyEntity(
            entity_id=f"VARGA-{varga}",
            entity_type="Varga",
            name=varga,
            metadata={"divisor": divisor},
        ))


def _populate_event(registry: OntologyRegistry) -> None:
    """
    A small, explicitly non-exhaustive starting vocabulary of classical
    life-event categories astrology traditionally addresses — not
    chart-specific occurrences (those are computed, not ontological
    facts), and not claimed complete.
    """
    categories = ["marriage", "career", "education", "health", "progeny", "wealth", "longevity"]
    for category in categories:
        registry.add_entity(OntologyEntity(
            entity_id=f"EVENT-{category.upper()}",
            entity_type="Event",
            name=category.capitalize(),
            metadata={"scope_note": "starting vocabulary, not exhaustive"},
        ))


def _populate_dignity_relationships(registry: OntologyRegistry) -> None:
    from packages.shared.constants import (
        DEBILITATION_RASHIS,
        EXALTATION_DEGREES,
        MOOLATRIKONA_RASHIS,
        OWN_SIGNS,
    )

    for planet, rashis in OWN_SIGNS.items():
        for rashi in rashis:
            registry.add_relationship(OntologyRelationship(
                subject_id=f"GRAHA-{planet.upper()}",
                relationship_type="Owns",
                object_id=f"RASHI-{rashi.upper()}",
            ))

    for planet, (rashi, degree) in EXALTATION_DEGREES.items():
        registry.add_relationship(OntologyRelationship(
            subject_id=f"GRAHA-{planet.upper()}",
            relationship_type="ExaltedIn",
            object_id=f"RASHI-{rashi.upper()}",
            metadata={"exact_degree": degree},
        ))

    for planet, rashi in DEBILITATION_RASHIS.items():
        registry.add_relationship(OntologyRelationship(
            subject_id=f"GRAHA-{planet.upper()}",
            relationship_type="DebilitatedIn",
            object_id=f"RASHI-{rashi.upper()}",
        ))

    for planet, rashi in MOOLATRIKONA_RASHIS.items():
        registry.add_relationship(OntologyRelationship(
            subject_id=f"GRAHA-{planet.upper()}",
            relationship_type="MoolatrikonaIn",
            object_id=f"RASHI-{rashi.upper()}",
        ))


def build_default_ontology() -> OntologyRegistry:
    """
    Construct and populate the full default ontology. Order matters:
    Varga and Graha must be populated before Yoga/Karaka/Technique (which
    reference them in relationships); Event must be populated before
    Technique (AppliesTo edges).
    """
    registry = OntologyRegistry()

    _populate_graha(registry)
    _populate_rashi(registry)
    _populate_bhava(registry)
    _populate_nakshatra(registry)
    _populate_pada(registry)
    _populate_varga(registry)
    _populate_yoga(registry)
    _populate_bala(registry)
    _populate_dasha(registry)
    _populate_aspect(registry)
    _populate_karaka(registry)
    _populate_event(registry)
    _populate_technique(registry)
    _populate_dignity_relationships(registry)

    return registry
