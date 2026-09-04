"""
AstroOS — Technique Fixture: Midpoints to Angles (Isograph)

Identifies locations where a midpoint (halfway between two planets) falls
on an angular cusp (Asc/Desc or MC/IC axis) — incredibly powerful,
especially when two midpoints hit the same axis (a "planetary picture" /
isograph).

Source: RAG technique 11-midpoints-to-angles.md ("Relocational Astrology:
How to Pick a Place").

Purely declarative rules over RelocationEngine midpoint facts and the
midpoint axis aggregates (midpoints.asc.* / midpoints.mc.*).
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
    "Relocation & Vedic Astrology — Technique 11 (Midpoints to Angles), "
    "after 'Relocational Astrology: How to Pick a Place'"
)


def init_midpoints_to_angles() -> None:
    if get_technique("midpoints_to_angles", 1) is not None:
        return

    # R1 — a midpoint on the Ascendant or Midheaven is powerful.
    if get_rule("MID-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="MID-001",
                rule_version="1.0",
                rule_name="Midpoint On Angle Is Powerful",
                source_text=(
                    "A midpoint (of two planets) falling on the Ascendant or "
                    "Midheaven is incredibly powerful — a strong point of symmetry."
                ),
                priority=1,
                category="midpoints_to_angles",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition(
                                "relocation.midpoints.asc.count",
                                ">=",
                                1,
                                "A midpoint is in orb of the Ascendant axis.",
                            ),
                            Condition(
                                "relocation.midpoints.mc.count",
                                ">=",
                                1,
                                "A midpoint is in orb of the Midheaven axis.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.midpoint.to_angle": "active"},
                    description="A midpoint falls on an angular cusp.",
                ),
                explanation=(
                    "A midpoint on an angle focuses the combined energy of its two "
                    "planets through that life area."
                ),
                tags=("relocation", "midpoints"),
            )
        )

    # R2 — two midpoints on the same axis = planetary picture (isograph).
    if get_rule("MID-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="MID-002",
                rule_version="1.0",
                rule_name="Planetary Picture (Isograph)",
                source_text=(
                    "Two distinct midpoints both hitting the same axis (Asc/Desc or "
                    "MC/IC) is an incredibly powerful point of symmetry — stronger "
                    "than a single midpoint."
                ),
                priority=1,
                category="midpoints_to_angles",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition(
                                "relocation.midpoints.asc.double",
                                "==",
                                True,
                                "Two midpoints on the Ascendant/Descendant axis.",
                            ),
                            Condition(
                                "relocation.midpoints.mc.double",
                                "==",
                                True,
                                "Two midpoints on the Midheaven/IC axis.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.midpoint.isograph": "active"},
                    description="A double-midpoint isograph on one axis.",
                ),
                explanation=(
                    "Two midpoints on the same axis create a pronounced planetary "
                    "picture, stronger than any single midpoint."
                ),
                tags=("relocation", "midpoints"),
            )
        )

    # R3 — interpret each constituent planet's theme.
    if get_rule("MID-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="MID-003",
                rule_version="1.0",
                rule_name="Midpoint Theme Interpretation",
                source_text=(
                    "Read the combined energy of the two constituent planets (e.g. "
                    "Sun-Jupiter = growth/popularity; Saturn-Neptune = ascetic/"
                    "spiritual path)."
                ),
                priority=2,
                category="midpoints_to_angles",
                conditions=(
                    Condition(
                        "relocation.midpoints.asc.count",
                        ">=",
                        1,
                        "At least one midpoint is on the Ascendant axis.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.midpoint.theme_interpretation": "active"},
                    description="Constituent-planet themes apply to the location.",
                ),
                explanation=(
                    "The two planets forming an in-orb midpoint carry a combined "
                    "theme through the axis life area."
                ),
                tags=("relocation", "midpoints"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="midpoints_to_angles",
        name="Midpoints to Angles (Planetary Picture / Isograph)",
        version=1,
        description=(
            "Flags midpoints on the angles (single powerful, double isograph "
            "strongest) and reads the combined constituent-planet themes."
        ),
        tradition="Western Astrology",
        objective="relocation_midpoints",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.midpoints.asc.count",
            "relocation.midpoints.mc.count",
            "relocation.midpoints.asc.double",
            "relocation.midpoints.mc.double",
            "relocation.midpoint.sun_jupiter.asc_orb",
        ),
        dependencies=("relocation_engine",),
        rule_refs=(
            TechniqueRuleRef("MID-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("MID-002", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("MID-003", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "an advanced, source-documented method; most astrologers do not place "
            "this much weight on midpoints — apply only where its preconditions hold.",
        ),
    )
    register_technique(tech)


init_midpoints_to_angles()
