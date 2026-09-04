"""
AstroOS — Technique Fixture: Major & Minor Frequencies (Twin Maps)

Establishes the two-level energy framework for any location: Major
frequencies (Astro-Cartography map + Geodetic map — the "twin" maps,
equal in importance) and Minor frequencies (Local Space map + Paran map).

The engine currently produces astro-cartography (natal/paran axial lines)
and local-space/paran map facts, but NOT the geodetic map. Rules that
require geodetic evidence therefore surface as INSUFFICIENT_DATA — never
guessed. Supportive/challenging classification is likewise not computed.

Source: RAG technique 04-major-minor-frequencies.md ("What is
Astrocartography?" — Scott Wolfram).
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
    "Relocation & Vedic Astrology — Technique 04 (Major & Minor Frequencies), "
    "after 'What is Astrocartography?' (Scott Wolfram)"
)


def init_major_minor_frequencies() -> None:
    if get_technique("major_minor_frequencies", 1) is not None:
        return

    # R1/R2 — Major frequencies = Astro-Cartography + Geodetic twin maps.
    if get_rule("FREQ-MAJ-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="FREQ-MAJ-001",
                rule_version="1.0",
                rule_name="Major Frequencies Twin Maps",
                source_text=(
                    "A location's primary energy rests on BOTH the astro-cartography "
                    "map and the geodetic map; they are equal in strength and importance."
                ),
                priority=1,
                category="major_minor_frequencies",
                conditions=(
                    ConditionGroup(
                        operator="AND",
                        conditions=(
                            Condition(
                                "relocation.lines.natal.count",
                                ">=",
                                1,
                                "Astro-cartography (natal) lines are active.",
                            ),
                            Condition(
                                "relocation.lines.geodetic.count",
                                ">=",
                                1,
                                "Geodetic lines are active (requires geodetic producer).",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.frequencies.major_twin_active": "true"},
                    description="Both major twin maps are active and equal in weight.",
                ),
                explanation=(
                    "The astro-cartography and geodetic maps must be read together; "
                    "a location is never judged on only one major map."
                ),
                tags=("relocation", "frequencies"),
            )
        )

    # R3 — supportive vs challenging energies per map.
    if get_rule("FREQ-MAJ-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="FREQ-MAJ-002",
                rule_version="1.0",
                rule_name="Classify Supportive vs Challenging",
                source_text=(
                    "Each map separates energies into supportive (promote success) "
                    "and challenging (obstacles); best locations avoid the negatives "
                    "in BOTH maps."
                ),
                priority=2,
                category="major_minor_frequencies",
                conditions=(
                    ConditionGroup(
                        operator="AND",
                        conditions=(
                            Condition(
                                "relocation.map.supportive.count",
                                ">=",
                                1,
                                "Supportive energies classified (needs significator analysis).",
                            ),
                            Condition(
                                "relocation.map.challenging.count",
                                ">=",
                                1,
                                "Challenging energies classified (needs significator analysis).",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.frequencies.classified": "true"},
                    description="Supportive and challenging energies are both assessed.",
                ),
                explanation=(
                    "Supportive/challenging classification is a significator-level "
                    "judgment not yet produced by the engine; this rule is "
                    "INSUFFICIENT_DATA until such facts exist."
                ),
                tags=("relocation", "frequencies"),
            )
        )

    # R4 — Minor frequencies fine-tune (local space + paran).
    if get_rule("FREQ-MIN-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="FREQ-MIN-001",
                rule_version="1.0",
                rule_name="Minor Frequencies Fine-Tune",
                source_text=(
                    "Best locations identified from the major maps are fine-tuned with "
                    "the Local Space map (personal 'trade winds') and the Paran map "
                    "(narrow horizontal bands)."
                ),
                priority=3,
                category="major_minor_frequencies",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition(
                                "relocation.local_space.count",
                                ">=",
                                1,
                                "Local-space map facts are available.",
                            ),
                            Condition(
                                "relocation.paran.count",
                                ">=",
                                1,
                                "Paran map facts are available.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.frequencies.minor_active": "true"},
                    description="Minor-frequency maps are available for fine-tuning.",
                ),
                explanation=(
                    "Local-space and paran maps fine-tune candidate best locations; "
                    "they never override a clear major-map reading."
                ),
                tags=("relocation", "frequencies"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="major_minor_frequencies",
        name="Major & Minor Frequencies (Twin Maps)",
        version=1,
        description=(
            "Evaluates a location with the twin major maps (astro-cartography + "
            "geodetic) and fine-tunes with local-space and paran minor maps."
        ),
        tradition="Western Astrology",
        objective="relocation_frequencies",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.lines.natal.count",
            "relocation.lines.geodetic.count",
            "relocation.paran.count",
            "relocation.local_space.count",
            "relocation.map.supportive.count",
            "relocation.map.challenging.count",
        ),
        dependencies=("relocation_engine",),
        rule_refs=(
            TechniqueRuleRef("FREQ-MAJ-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("FREQ-MAJ-002", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("FREQ-MIN-001", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "geodetic map and supportive/challenging classification are not computed "
            "by the engine; FREQ-MAJ-001/002 evaluate as INSUFFICIENT_DATA until "
            "those producers exist.",
        ),
    )
    register_technique(tech)


init_major_minor_frequencies()
