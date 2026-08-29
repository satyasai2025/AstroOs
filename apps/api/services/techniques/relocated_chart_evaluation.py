"""
AstroOS — Technique Fixture: Relocated Chart Evaluation

Evaluates how life experiences would differ at a given location by
computing the relocated chart (same birth instant, changed place) and
reading the resulting house cusps and planet placements.

Source: RAG technique 01-relocated-chart-evaluation.md
("Introduction to Relocational Astrology and AstroCartography").

Purely declarative rules evaluated on `relocation.*` facts produced by
the RelocationEngine. Missing facts are reported by the TechniqueEngine
as INSUFFICIENT_DATA, never invented.
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
    "Relocation & Vedic Astrology — Technique 01 (Relocated Chart Evaluation), "
    "after 'Introduction to Relocational Astrology and AstroCartography'"
)


def init_relocated_chart_evaluation() -> None:
    if get_technique("relocated_chart_evaluation", 1) is not None:
        return

    # R1 — planetary longitudes are invariant under relocation.
    if get_rule("RELO-EVAL-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="RELO-EVAL-001",
                rule_version="1.0",
                rule_name="Planetary Longitudes Invariant",
                source_text=(
                    "Relocation changes place, not time; natal longitudes are "
                    "unchanged by relocation."
                ),
                priority=1,
                category="relocation_evaluation",
                conditions=(
                    Condition(
                        "relocation.evaluated",
                        "==",
                        True,
                        "Relocation facts were computed for the target location.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.longitudes.invariant": "true"},
                    description="All planetary longitudes are carried over unchanged.",
                ),
                explanation=(
                    "Time is fixed, place changes; therefore the planets do not move."
                ),
                tags=("relocation", "foundation"),
            )
        )

    # R2 — house cusps shift with place.
    if get_rule("RELO-EVAL-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="RELO-EVAL-002",
                rule_version="1.0",
                rule_name="House Cusps Shift With Place",
                source_text=(
                    "When the target location differs from the birth place, the "
                    "relocated Ascendant/MC/IC/Descendant differ from the natal angles."
                ),
                priority=1,
                category="relocation_evaluation",
                conditions=(
                    Condition(
                        "relocation.location_changed",
                        "==",
                        True,
                        "Target location differs from the birth place.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.cusps.shifted": "true"},
                    description="Relocated angular cusps differ from the natal ones.",
                ),
                explanation=(
                    "A different place produces a different local horizon, hence a "
                    "different set of house cusps for the same birth instant."
                ),
                tags=("relocation", "houses"),
            )
        )

    # R3 — angular cusp planets are powerful.
    if get_rule("RELO-EVAL-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="RELO-EVAL-003",
                rule_version="1.0",
                rule_name="Angular Cusp Planets Dominant",
                source_text=(
                    "A planet with angular status (on the 1st/4th/7th/10th cusp) is "
                    "especially prominent; the most powerful places are where planets "
                    "sit on the angles."
                ),
                priority=2,
                category="relocation_evaluation",
                conditions=(
                    Condition(
                        "relocation.angular.count",
                        ">=",
                        1,
                        "At least one planet is angular in the relocated chart.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.angular.activation": "true"},
                    description="Angular planets are highlighted at the target location.",
                ),
                explanation=(
                    "Planets conjunct an angular cusp dominate the relocated chart's "
                    "expression at that place."
                ),
                tags=("relocation", "angular"),
            )
        )

    # R4 — house change alters experience.
    if get_rule("RELO-EVAL-004") is None:
        register_rule(
            RuleDefinition(
                rule_id="RELO-EVAL-004",
                rule_version="1.0",
                rule_name="House Change Alters Experience",
                source_text=(
                    "When a planet's house position differs between the natal and the "
                    "relocated chart, the planet expresses through the relocated house "
                    "theme at that location."
                ),
                priority=2,
                category="relocation_evaluation",
                conditions=(
                    Condition(
                        "relocation.house_changed.count",
                        ">=",
                        1,
                        "At least one planet changed houses between natal and relocated.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.house_change.active": "true"},
                    description="House-change themes are expressed at the location.",
                ),
                explanation=(
                    "A planet moving into a different house shifts the life domain "
                    "through which its energy is experienced."
                ),
                tags=("relocation", "houses"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="relocated_chart_evaluation",
        name="Relocated Chart Evaluation",
        version=1,
        description=(
            "Reads the relocated chart: invariant longitudes, shifted cusps, "
            "angular-planet dominance and house-change themes at a target location."
        ),
        tradition="Western Astrology",
        objective="relocation_evaluation",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.evaluated",
            "relocation.location_changed",
            "relocation.ascendant.degree",
            "relocation.midheaven.degree",
            "relocation.angular.count",
            "relocation.house_changed.count",
            "relocation.planet.moon.longitude",
        ),
        dependencies=("relocation_engine",),
        rule_refs=(
            TechniqueRuleRef("RELO-EVAL-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("RELO-EVAL-002", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("RELO-EVAL-003", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("RELO-EVAL-004", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "birth_time_uncertainty degrades all angular and house-cusp conclusions.",
        ),
    )
    register_technique(tech)


init_relocated_chart_evaluation()
