"""
AstroOS — Technique Fixture: Map Line Reading

Reads a single map line at a location: identify which planet / cusp it
represents, its orb, and the expected energy from living near it. This is
the per-line reading layer on top of the hierarchy technique.

Source: RAG technique 03-map-line-reading.md ("How to Read AstroCartography
Maps with Relocated Charts").

Purely declarative rules evaluated on `relocation.planet.<p>.*` line facts
produced by the RelocationEngine (longitude coordinate system).
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, ConditionGroup, Conclusion, RuleDefinition
from apps.api.domain.technique import (
    ProvenanceStatus,
    RuleRole,
    TechniqueDefinition,
    TechniqueRuleRef,
)
from apps.api.services.rule_registry import get_rule, register_rule
from apps.api.services.technique_registry import get_technique, register_technique

_SOURCE = (
    "Relocation & Vedic Astrology — Technique 03 (Map Line Reading), "
    "after 'How to Read AstroCartography Maps with Relocated Charts'"
)

_PLANETS = ("sun", "moon", "mercury", "venus", "mars", "jupiter",
            "saturn", "uranus", "neptune", "pluto", "rahu", "ketu")


def init_map_line_reading() -> None:
    if get_technique("map_line_reading", 1) is not None:
        return

    # R1 — identify the line (any in-orb planet line at the location).
    if get_rule("LINE-READ-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="LINE-READ-001",
                rule_version="1.0",
                rule_name="Identify In-Orb Line",
                source_text=(
                    "A line present on the map is identified by its planet label; "
                    "it applies only when within its orb at the location."
                ),
                priority=1,
                category="map_line_reading",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=tuple(
                            Condition(
                                f"relocation.planet.{p}.line_in_orb",
                                "==",
                                True,
                                f"{p.title()} line is in orb at the location.",
                            )
                            for p in _PLANETS
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.line.identified": "true"},
                    description="At least one planet line is in orb and identifiable.",
                ),
                explanation=(
                    "The planet of an in-orb line is identified from its map label or "
                    "color code."
                ),
                tags=("relocation", "line_reading"),
            )
        )

    # R3 — cusp determines the life area (Ascendant vs Midheaven axis).
    if get_rule("LINE-READ-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="LINE-READ-003",
                rule_version="1.0",
                rule_name="Cusp Determines Life Area",
                source_text=(
                    "The line's cusp reads its life area: Ascendant (self), "
                    "Descendant (relationships), MC (career/status), IC (home). A "
                    "planet on an angular cusp is extra powerful."
                ),
                priority=2,
                category="map_line_reading",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=tuple(
                            Condition(
                                f"relocation.planet.{p}.axis",
                                "in",
                                ("asc", "mc", "both"),
                                f"{p.title()} line is on the Ascendant/Midheaven axis.",
                            )
                            for p in _PLANETS
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.line.cusp_domain": "readable"},
                    description="An axial planet line maps to a life-area cusp.",
                ),
                explanation=(
                    "The axis (asc/mc) of an in-orb line fixes which life domain the "
                    "planet's energy expresses through."
                ),
                tags=("relocation", "line_reading"),
            )
        )

    # R4 — tighten orb strengthens the effect (modifier).
    if get_rule("LINE-READ-004") is None:
        register_rule(
            RuleDefinition(
                rule_id="LINE-READ-004",
                rule_version="1.0",
                rule_name="Tight Orb Strengthens Effect",
                source_text=(
                    "A tighter orb (closer to the line) strengthens the effect; a "
                    "major line (rank 1) is stronger than a minor one."
                ),
                priority=3,
                category="map_line_reading",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=tuple(
                            Condition(
                                f"relocation.planet.{p}.line_frequency",
                                "==",
                                "major",
                                f"{p.title()} has a major (rank-1) line in orb.",
                            )
                            for p in _PLANETS
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.line.major_strength": "present"},
                    description="A major line is close enough to be extra strong.",
                ),
                explanation=(
                    "Rank-1 (major) lines sit essentially on the angle, strengthening "
                    "the reading."
                ),
                tags=("relocation", "line_reading"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="map_line_reading",
        name="Map Line Reading",
        version=1,
        description=(
            "Reads a single in-orb map line: planet identity, cusp life-area, and "
            "strength by orb, per the longitude coordinate system."
        ),
        tradition="Western Astrology",
        objective="map_line_reading",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.planet.pluto.line_in_orb",
            "relocation.planet.pluto.axis",
            "relocation.planet.pluto.line_frequency",
            "relocation.lines.in_orb_count",
        ),
        dependencies=("relocation_engine",),
        rule_refs=(
            TechniqueRuleRef("LINE-READ-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("LINE-READ-003", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("LINE-READ-004", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "aspect lines are not computed by the engine; only axial (asc/mc) lines.",
        ),
    )
    register_technique(tech)


init_map_line_reading()
