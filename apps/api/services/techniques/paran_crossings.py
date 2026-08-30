"""
AstroOS — Technique Fixture: Paran Lines (Crossing Lines / X-Marks)

Interprets paran lines — formed where two natal lines cross — which carry
the combined energy of both planets, within a very tight orb.

The engine detects paran crossings as planet pairs simultaneously angular
in mundo and reports orb-gated activity via `relocation.lines.paran.*`.

Source: RAG technique 09-paran-crossings.md ("How to read your
Astrocartograpy Map", "What is Astrocartography?").
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
    "Relocation & Vedic Astrology — Technique 09 (Paran Crossings), "
    "after 'How to read your Astrocartograpy Map' and 'What is Astrocartography?'"
)


def init_paran_crossings() -> None:
    if get_technique("paran_crossings", 1) is not None:
        return

    # R1 — paran = combined energy of the two crossing natal lines.
    if get_rule("PARAN-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="PARAN-001",
                rule_version="1.0",
                rule_name="Paran Combines Two Energies",
                source_text=(
                    "A paran line is where two natal lines cross and carries the "
                    "combined energy of both planets (e.g. a Jupiter-Pluto paran "
                    "carries both Jupiter and Pluto energy)."
                ),
                priority=1,
                category="paran_crossings",
                conditions=(
                    Condition(
                        "relocation.lines.paran.count",
                        ">=",
                        1,
                        "At least one paran line is in orb at the location.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.paran.combined_energy": "active"},
                    description="An in-orb paran adds both planets' energies.",
                ),
                explanation=(
                    "Paran energy is combined, not doubled: both crossing planets' "
                    "themes are present."
                ),
                tags=("relocation", "paran"),
            )
        )

    # R2 — orb gate: a crossing out of orb does not apply.
    if get_rule("PARAN-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="PARAN-002",
                rule_version="1.0",
                rule_name="Paran Orb Gate",
                source_text=(
                    "A paran affects only locations within its very tight orb "
                    "(~15 miles); outside it, the paran does not apply even if "
                    "visible on the map."
                ),
                priority=1,
                category="paran_crossings",
                conditions=(
                    ConditionGroup(
                        operator="AND",
                        conditions=(
                            Condition(
                                "relocation.paran.count",
                                ">=",
                                1,
                                "At least one paran crossing exists.",
                            ),
                            Condition(
                                "relocation.lines.paran.count",
                                "==",
                                0,
                                "No paran line is within the tight orb.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.paran.out_of_orb": "true"},
                    description="Paran crossings exist but are out of orb.",
                ),
                explanation=(
                    "A crossing visible on the map is excluded from the reading when "
                    "the location is outside its tight orb."
                ),
                tags=("relocation", "paran"),
            )
        )

    # R3 — X-marks-the-spot bonus (needs a supportive-line classifier).
    if get_rule("PARAN-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="PARAN-003",
                rule_version="1.0",
                rule_name="X-Marks-The-Spot",
                source_text=(
                    "A local-space pathway (or supportive line) crossing a supportive "
                    "astro-cartography/geodetic energy marks a spot that energizes "
                    "destiny."
                ),
                priority=2,
                category="paran_crossings",
                conditions=(
                    ConditionGroup(
                        operator="AND",
                        conditions=(
                            Condition(
                                "relocation.local_space.count",
                                ">=",
                                1,
                                "Local-space map facts are available.",
                            ),
                            Condition(
                                "relocation.map.supportive.count",
                                ">=",
                                1,
                                "A supportive major-map energy is classified.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.paran.x_marks_spot": "true"},
                    description="A supportive crossing energizes destiny.",
                ),
                explanation=(
                    "Where a local-space pathway crosses a supportive energy, the spot "
                    "energizes destiny; requires a supportive-line classifier."
                ),
                tags=("relocation", "paran"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="paran_crossings",
        name="Paran Lines (Crossing Lines / X-Marks)",
        version=1,
        description=(
            "Reads paran crossings as combined two-planet energies, gated by the "
            "tight paran orb, with the X-marks-the-spot bonus for supportive crossings."
        ),
        tradition="Western Astrology",
        objective="relocation_paran",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.paran.count",
            "relocation.lines.paran.count",
            "relocation.lines.paran.planets",
            "relocation.local_space.count",
        ),
        dependencies=("relocation_engine", "supportive_location_classifier"),
        rule_refs=(
            TechniqueRuleRef("PARAN-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("PARAN-002", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("PARAN-003", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "paran energy is combined, not doubled; never interpret a paran as a "
            "single-planet line.",
        ),
    )
    register_technique(tech)


init_paran_crossings()
