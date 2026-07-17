"""
AstroOS — Domain Ontology Objects (Module 12)

A Domain Ontology only, per explicit scope: entities, relationships,
stable identifiers, and metadata. Deliberately NOT a knowledge graph
(no Neo4j/RDF/OWL/SPARQL), NOT a query/inference engine, and NOT Rule
Engine behavior — Module 13 consumes this, it does not define it.

Two primitives:
  - OntologyEntity: one classical concept (a Graha, a Rashi, a Yoga...)
    with a stable id, a type, a name, and free-form metadata specific
    to that entity type.
  - OntologyRelationship: one typed, directed edge between two entities
    (e.g. Mars --Owns--> Aries), with its own metadata.

No graph traversal, no querying beyond direct lookup by id — see
OntologyRegistry in ontology_registry.py for the (deliberately minimal)
access surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OntologyEntity:
    """
    One classical astrology concept as a first-class, independently
    identifiable thing — not tied to any specific chart or calculation.
    """
    entity_id: str        # stable, permanent — e.g. "GRAHA-SUN", "YOGA-BPHS-PM-001"
    entity_type: str      # "Graha", "Rashi", "Bhava", "Nakshatra", "Pada",
                           # "Yoga", "Bala", "Dasha", "Aspect", "Karaka", "Varga", "Event"
    name: str              # human-readable name, e.g. "Sun", "Ruchaka Yoga"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OntologyRelationship:
    """
    One typed, directed edge between two entities. relationship_type is
    open vocabulary (not a fixed enum) — see ontology_registry.py's
    population code for the vocabulary actually used, but new types can
    be added without a schema change.
    """
    subject_id: str
    relationship_type: str  # "Owns", "ExaltedIn", "DebilitatedIn", "Requires", "ParticipatesIn", ...
    object_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
