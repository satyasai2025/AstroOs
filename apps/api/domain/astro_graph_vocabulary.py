"""
AstroOS — Astrological Graph Vocabulary (Step 1)

Vocabulary-only module: two closed enums for the astrological reasoning graph.
No DB tables, no migrations, no services, no routes, no prediction logic.

Reused primitives (unchanged):
  GraphNode            ← apps/api/domain/graph.py
  GraphRelationship    ← apps/api/domain/graph.py
  Entity               ← apps/api/domain/graph.py
  OntologyEntity       ← apps/api/domain/ontology.py
  OntologyRelation     ← apps/api/domain/ontology.py
  Fact                 ← apps/api/domain/facts.py
"""

from __future__ import annotations

from enum import Enum


# ── Node categories ──────────────────────────────────────────────────────────


class AstroNodeCategory(str, Enum):
    """
    Canonical node categories for the astrological reasoning graph.

    Values are stable string identifiers intended for GraphNode.type.
    Closed enumeration — add values only via phase gate.
    """

    PLANET = "PLANET"
    SIGN = "SIGN"
    HOUSE = "HOUSE"
    NAKSHATRA = "NAKSHATRA"
    DASHA = "DASHA"
    VARGA = "VARGA"
    RULE = "RULE"
    EVIDENCE = "EVIDENCE"
    EVENT_DOMAIN = "EVENT_DOMAIN"


# ── Relationship types ────────────────────────────────────────────────────────


class AstroRelationshipType(str, Enum):
    """
    Typed, directed edges between astrological graph nodes.

    Values are stable string identifiers intended for
    GraphRelationship.relationship_type.

    Intentionally does NOT replace the open-vocabulary
    OntologyRelation.relationship_type field — both coexist.
    """

    OCCUPIES = "OCCUPIES"
    OWNS = "OWNS"
    DISPOSITOR_OF = "DISPOSITOR_OF"
    ASPECTS = "ASPECTS"
    CONJUNCT_WITH = "CONJUNCT_WITH"
    LOCATED_IN_NAKSHATRA = "LOCATED_IN_NAKSHATRA"
    RULED_BY = "RULED_BY"
    ACTIVATES = "ACTIVATES"
    APPLIES_TO = "APPLIES_TO"
    SUPPORTED_BY = "SUPPORTED_BY"
    CONTRADICTED_BY = "CONTRADICTED_BY"
    DERIVED_FROM = "DERIVED_FROM"