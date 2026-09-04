"""
AstroOS — Technique Fixture: Comfort Zones (Moon/Venus 9th-Harmonic)

Identifies locations where a person "just feels good" — places that feel
friendly, bonded, "like home" — via Moon/Venus in 9th-harmonic relation
(multiples of 40°) to an angular cusp, distinct from where one "shines"
(Sun angular).

Source: RAG technique 06-comfort-zones.md ("Relocational Astrology: How
to Pick a Place").

Purely declarative rules over RelocationEngine facts (9th-harmonic
relations of Moon/Venus to the ASC/MC angles and angle harmonic labels).
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
    "Relocation & Vedic Astrology — Technique 06 (Comfort Zones), "
    "after 'Relocational Astrology: How to Pick a Place'"
)


def init_comfort_zones() -> None:
    if get_technique("comfort_zones", 1) is not None:
        return

    # R1 — Moon or Venus in 9th-harmonic aspect to an angular cusp.
    if get_rule("COMFORT-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="COMFORT-001",
                rule_version="1.0",
                rule_name="Moon/Venus 9th-Harmonic To Angle",
                source_text=(
                    "Moon or Venus at a 9th-harmonic angle (multiples of 40°: 40, 80, "
                    "120) to an angular cusp marks a comfort zone where one feels good "
                    "and bonded."
                ),
                priority=1,
                category="comfort_zones",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition(
                                "relocation.planet.moon.ninth_harmonic_to_angle",
                                "==",
                                True,
                                "Moon is in 9th-harmonic relation to an angle.",
                            ),
                            Condition(
                                "relocation.planet.venus.ninth_harmonic_to_angle",
                                "==",
                                True,
                                "Venus is in 9th-harmonic relation to an angle.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.comfort_zone": "true"},
                    description="The location is a comfort zone.",
                ),
                explanation=(
                    "A 9th-harmonic relation of Moon or Venus to an angle means the "
                    "person feels at ease, bonded, at home."
                ),
                tags=("relocation", "comfort"),
            )
        )

    # R2 — round-number line labels indicate comfort.
    if get_rule("COMFORT-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="COMFORT-002",
                rule_version="1.0",
                rule_name="Round-Number Label Comfort Signal",
                source_text=(
                    "A map line label that is a round multiple of 10 (e.g. 140°) is a "
                    "9th-harmonic comfort signal (140° = 40° from the opposite cusp)."
                ),
                priority=2,
                category="comfort_zones",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition(
                                "relocation.ascendant.harmonic_family",
                                "==",
                                "ninth",
                                "The Ascendant label is a round multiple of 10.",
                            ),
                            Condition(
                                "relocation.midheaven.harmonic_family",
                                "==",
                                "ninth",
                                "The Midheaven label is a round multiple of 10.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.comfort_zone.round_label": "true"},
                    description="A round-number label confirms the comfort signal.",
                ),
                explanation=(
                    "Round multiples of 10 in the angle label correspond to the "
                    "9th-harmonic comfort family."
                ),
                tags=("relocation", "comfort"),
            )
        )

    # R3 — Venus vs Moon comfort flavor.
    if get_rule("COMFORT-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="COMFORT-003",
                rule_version="1.0",
                rule_name="Venus Comfort Flavor",
                source_text=(
                    "When Venus is the comfort indicator, the zone brings beauty and "
                    "joy; personal preference is a modifier."
                ),
                priority=3,
                category="comfort_zones",
                conditions=(
                    Condition(
                        "relocation.planet.venus.ninth_harmonic_to_angle",
                        "==",
                        True,
                        "Venus is in 9th-harmonic relation to an angle.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.comfort_zone.venus": "true"},
                    description="Venus-flavoured comfort zone.",
                ),
                explanation=(
                    "Venus comfort brings beauty and joy; some people prefer it over "
                    "Moon comfort."
                ),
                tags=("relocation", "comfort"),
            )
        )

    if get_rule("COMFORT-004") is None:
        register_rule(
            RuleDefinition(
                rule_id="COMFORT-004",
                rule_version="1.0",
                rule_name="Moon Comfort Flavor",
                source_text=(
                    "When Moon is the comfort indicator, the zone suits sentimental, "
                    "family and heritage interests."
                ),
                priority=3,
                category="comfort_zones",
                conditions=(
                    Condition(
                        "relocation.planet.moon.ninth_harmonic_to_angle",
                        "==",
                        True,
                        "Moon is in 9th-harmonic relation to an angle.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.comfort_zone.moon": "true"},
                    description="Moon-flavoured comfort zone.",
                ),
                explanation=(
                    "Moon comfort suits family, sentiment and heritage-oriented "
                    "interests."
                ),
                tags=("relocation", "comfort"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="comfort_zones",
        name="Comfort Zones (Moon/Venus 9th-Harmonic)",
        version=1,
        description=(
            "Marks locations where Moon or Venus sits in 9th-harmonic relation to an "
            "angle: places that feel friendly, bonded, 'like home'."
        ),
        tradition="Western Astrology",
        objective="relocation_comfort",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.planet.moon.ninth_harmonic_to_angle",
            "relocation.planet.venus.ninth_harmonic_to_angle",
            "relocation.ascendant.harmonic_family",
            "relocation.midheaven.harmonic_family",
            "relocation.planet.moon.angular_cusp_orb",
        ),
        dependencies=("relocation_engine",),
        rule_refs=(
            TechniqueRuleRef("COMFORT-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("COMFORT-002", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("COMFORT-003", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("COMFORT-004", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "comfort zones are distinct from Sun-angular 'shine' zones; do not treat "
            "a square or opposition to the angle as a comfort zone.",
        ),
    )
    register_technique(tech)


init_comfort_zones()
