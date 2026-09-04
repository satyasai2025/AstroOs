"""
AstroOS — Technique Fixture: Line-Type Hierarchy

Establishes the relative strength and orb of each map-line type so a
location reading ranks influences correctly. The engine only emits the
longitude-system line types it can compute (`natal` and `paran`);
local-space and geodetic lines are separate producers, so their rules
surface as INSUFFICIENT_DATA until those facts exist.

Source: RAG technique 02-line-type-hierarchy.md ("How to read your
Astrocartograpy Map").

Purely declarative rules evaluated on `relocation.lines.*` aggregate
facts and `relocation.planet.<p>.line_*` facts produced by the
RelocationEngine.
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
    "Relocation & Vedic Astrology — Technique 02 (Line-Type Hierarchy), "
    "after 'How to read your Astrocartograpy Map'"
)

_NATAL_PLANETS = ("sun", "moon", "mercury", "venus", "mars", "jupiter",
                  "saturn", "uranus", "neptune", "pluto", "rahu", "ketu")


def init_line_type_hierarchy() -> None:
    if get_technique("line_type_hierarchy", 1) is not None:
        return

    # R1 — natal lines are the strongest lines.
    if get_rule("LINE-HIER-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="LINE-HIER-001",
                rule_version="1.0",
                rule_name="Natal Lines Are Strongest",
                source_text=(
                    "Natal lines are the 'strongest and most dominant lines you will "
                    "experience'; they dominate the location when within their 700-mile orb."
                ),
                priority=1,
                category="line_type_hierarchy",
                conditions=(
                    Condition(
                        "relocation.lines.natal.count",
                        ">=",
                        1,
                        "At least one natal line is in orb at the location.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.hierarchy.natal_dominant": "true"},
                    description="In-orb natal lines dominate the location reading.",
                ),
                explanation=(
                    "Natal lines carry the largest orb and the strongest influence of "
                    "any line type."
                ),
                tags=("relocation", "line_hierarchy"),
            )
        )

    # R5 — closest in-orb line is strongest (within type).
    if get_rule("LINE-HIER-005") is None:
        register_rule(
            RuleDefinition(
                rule_id="LINE-HIER-005",
                rule_version="1.0",
                rule_name="Closest In-Orb Line Is Strongest",
                source_text=(
                    "Within a line type, line_rank orders influence: rank 1 (closest) "
                    "is the strongest, then rank 2, then the furthest."
                ),
                priority=2,
                category="line_type_hierarchy",
                conditions=(
                    Condition(
                        "relocation.lines.natal.count",
                        ">=",
                        2,
                        "More than one natal line is in orb (ties broken by rank).",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.hierarchy.closest_strongest": "true"},
                    description="Proximity orders strength within a line type.",
                ),
                explanation=(
                    "The closer the line, the stronger the effect; closest = rank 1."
                ),
                tags=("relocation", "line_hierarchy"),
            )
        )

    # R4 — paran lines have a very small orb.
    if get_rule("LINE-HIER-004") is None:
        register_rule(
            RuleDefinition(
                rule_id="LINE-HIER-004",
                rule_version="1.0",
                rule_name="Paran Lines Are Tight",
                source_text=(
                    "Paran lines (crossing natal lines) affect a location only within "
                    "a very small orb (~15 miles)."
                ),
                priority=3,
                category="line_type_hierarchy",
                conditions=(
                    Condition(
                        "relocation.lines.paran.count",
                        ">=",
                        1,
                        "A paran line is in orb at the location.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.hierarchy.paran_active": "true"},
                    description="An in-orb paran line affects the location.",
                ),
                explanation=(
                    "Paran lines are narrow; only locations within their tight orb "
                    "experience them."
                ),
                tags=("relocation", "line_hierarchy"),
            )
        )

    # Local-space / geodetic line types are separate producers; a rule
    # referencing them evaluates to INSUFFICIENT_DATA until those facts exist.
    if get_rule("LINE-HIER-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="LINE-HIER-002",
                rule_version="1.0",
                rule_name="Local-Space Lines Weaker Than Natal",
                source_text=(
                    "A local-space line in its ~100-mile orb is meaningful but weaker "
                    "than an in-orb natal line, even if physically closer."
                ),
                priority=2,
                category="line_type_hierarchy",
                conditions=(
                    Condition(
                        "relocation.lines.local_space.count",
                        ">=",
                        1,
                        "At least one local-space line is in orb.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.hierarchy.local_space_active": "true"},
                    description="An in-orb local-space line affects the location.",
                ),
                explanation=(
                    "Local-space lines are weaker than natal lines; this rule requires "
                    "local-space line facts from a separate producer."
                ),
                tags=("relocation", "line_hierarchy"),
            )
        )

    if get_rule("LINE-HIER-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="LINE-HIER-003",
                rule_version="1.0",
                rule_name="Geodetic Lines Minor",
                source_text=(
                    "Geodetic lines have a small orb (100-200 miles) and are treated "
                    "as minor; out of orb, they do not affect the location."
                ),
                priority=2,
                category="line_type_hierarchy",
                conditions=(
                    Condition(
                        "relocation.lines.geodetic.count",
                        ">=",
                        1,
                        "At least one geodetic line is in orb.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.hierarchy.geodetic_active": "true"},
                    description="An in-orb geodetic line affects the location.",
                ),
                explanation=(
                    "Geodetic lines require a separate producer; this rule evaluates "
                    "as INSUFFICIENT_DATA until geodetic line facts exist."
                ),
                tags=("relocation", "line_hierarchy"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="line_type_hierarchy",
        name="Line-Type Hierarchy",
        version=1,
        description=(
            "Ranks map-line influences by type strength and proximity: natal lines "
            "dominant, then local space, then geodetic, then tight paran lines."
        ),
        tradition="Western Astrology",
        objective="relocation_hierarchy",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.lines.natal.count",
            "relocation.lines.paran.count",
            "relocation.lines.in_orb_count",
            "relocation.planet.jupiter.line_rank",
            "relocation.planet.jupiter.line_type",
        ),
        dependencies=("relocation_engine",),
        rule_refs=(
            TechniqueRuleRef("LINE-HIER-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("LINE-HIER-005", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("LINE-HIER-002", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("LINE-HIER-003", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("LINE-HIER-004", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "line_rank applies within line type only; it does not let a local-space "
            "line outrank a natal line.",
        ),
    )
    register_technique(tech)


init_line_type_hierarchy()
