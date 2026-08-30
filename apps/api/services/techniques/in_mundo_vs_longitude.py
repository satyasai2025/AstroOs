"""
AstroOS — Technique Fixture: In-Mundo vs Longitude Map Systems

Distinguishes the two astro-map coordinate systems — longitude-based
(matches the relocated chart) and In-Mundo (Jim Lewis's original
Astro*Carto*Graphy, horizon/meridian planes) — and governs that a single
system is used throughout an evaluation.

Source: RAG technique 08-in-mundo-vs-longitude.md ("AstroCartography and
In Mundo Planet Positions", "Introduction to Relocational Astrology and
AstroCartography").

Purely declarative rules over RelocationEngine coordinate-system facts.
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
    "Relocation & Vedic Astrology — Technique 08 (In-Mundo vs Longitude), "
    "after 'AstroCartography and In Mundo Planet Positions' and "
    "'Introduction to Relocational Astrology and AstroCartography'"
)


def init_in_mundo_vs_longitude() -> None:
    if get_technique("in_mundo_vs_longitude", 1) is not None:
        return

    # R1 — longitude map matches the relocated chart.
    if get_rule("SYS-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="SYS-001",
                rule_version="1.0",
                rule_name="Longitude Map Matches Relocated Chart",
                source_text=(
                    "A longitude-based map is another picture of the same information "
                    "as the relocated chart: a line marks where a planet's longitude "
                    "is on an angular cusp."
                ),
                priority=1,
                category="in_mundo_vs_longitude",
                conditions=(
                    Condition(
                        "relocation.coordinate_system",
                        "==",
                        "longitude",
                        "The active map coordinate system is longitude.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.system.longitude_matches_relocated": "true"},
                    description="Longitude lines reproduce the relocated chart.",
                ),
                explanation=(
                    "Longitude lines mark where a planet's ecliptic longitude meets an "
                    "angular cusp, reproducible via the relocated chart."
                ),
                tags=("relocation", "coordinate_system"),
            )
        )

    # R2 — In-Mundo uses horizon and meridian planes.
    if get_rule("SYS-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="SYS-002",
                rule_version="1.0",
                rule_name="In-Mundo Uses Horizon/Meridian",
                source_text=(
                    "In-Mundo lines mark where the planet is physically on the "
                    "horizon (setting/rising) or on the meridian plane, NOT where its "
                    "ecliptic longitude is on a cusp."
                ),
                priority=1,
                category="in_mundo_vs_longitude",
                conditions=(
                    Condition(
                        "relocation.in_mundo.available",
                        "==",
                        True,
                        "In-Mundo facts are available for the target location.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.system.in_mundo.horizon_meridian": "true"},
                    description="In-Mundo lines are horizon/meridian-based.",
                ),
                explanation=(
                    "In-Mundo lines describe physical horizon/meridian contact, which "
                    "need not match the chart wheel."
                ),
                tags=("relocation", "coordinate_system"),
            )
        )

    # R3 — do not mix coordinate systems in one evaluation.
    if get_rule("SYS-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="SYS-003",
                rule_version="1.0",
                rule_name="Never Mix Coordinate Systems",
                source_text=(
                    "Pick ONE coordinate system for an evaluation; never compare a "
                    "longitude-line location to an In-Mundo line location as if the "
                    "same fact."
                ),
                priority=1,
                category="in_mundo_vs_longitude",
                conditions=(
                    Condition(
                        "relocation.coordinate_system",
                        "in",
                        ("longitude", "in_mundo"),
                        "A single coordinate system is selected for the evaluation.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.system.single_system": "true"},
                    description="Evaluation uses one coordinate system.",
                ),
                explanation=(
                    "The engine's fact set carries a single coordinate system; "
                    "longitude and in-mundo lines must never be compared as one fact."
                ),
                tags=("relocation", "coordinate_system"),
            )
        )

    # R4 — consistency recommendation.
    if get_rule("SYS-004") is None:
        register_rule(
            RuleDefinition(
                rule_id="SYS-004",
                rule_version="1.0",
                rule_name="Recommend Longitude For Chart-Wheel Consistency",
                source_text=(
                    "When the user wants the map and chart wheel to agree, recommend "
                    "the longitude system; In-Mundo is coherent only if the whole "
                    "practice uses horizon-based positions."
                ),
                priority=2,
                category="in_mundo_vs_longitude",
                conditions=(
                    Condition(
                        "relocation.preference.chart_wheel_consistency",
                        "==",
                        True,
                        "The user wants map and chart wheel to agree.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.system.recommend_longitude": "true"},
                    description="Longitude recommended for chart-wheel consistency.",
                ),
                explanation=(
                    "The longitude system matches the relocated chart; In-Mundo is "
                    "consistent only with an entirely horizon-based practice."
                ),
                tags=("relocation", "coordinate_system"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="in_mundo_vs_longitude",
        name="In-Mundo vs Longitude Map Systems",
        version=1,
        description=(
            "Distinguishes longitude-based and In-Mundo map systems, enforces a "
            "single system per evaluation, and recommends longitude for chart-wheel "
            "consistency."
        ),
        tradition="Western Astrology",
        objective="relocation_coordinate_system",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.coordinate_system",
            "relocation.in_mundo.available",
            "relocation.planet.uranus.in_mundo_angular_status",
            "relocation.planet.uranus.line_coordinate_system",
        ),
        dependencies=("relocation_engine",),
        rule_refs=(
            TechniqueRuleRef("SYS-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("SYS-002", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("SYS-003", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("SYS-004", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "no source rule declares one system universally correct; longitude "
            "matches the relocated chart and is 'definitely correct' as a picture of "
            "it, while In-Mundo 'may also be correct' but tells something different.",
        ),
    )
    register_technique(tech)


init_in_mundo_vs_longitude()
