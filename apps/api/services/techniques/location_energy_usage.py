"""
AstroOS — Technique Fixture: Location Energy Usage (Live / Travel / Import)

Defines the three ways a person can use a supportive location's energy:
live there (strongest), travel there (absorb and return), or connect/import
without going (weakest but supportive).

The technique assumes a supportive location has been identified; the
identification itself is a separate producer (a supportive/challenging
classifier). `relocation.supportive.identified` and the feasibility flags
(`relocation.usage.*`) are caller context facts.

Source: RAG technique 05-location-energy-usage.md ("What is
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
    "Relocation & Vedic Astrology — Technique 05 (Location Energy Usage), "
    "after 'What is Astrocartography?' (Scott Wolfram)"
)


def init_location_energy_usage() -> None:
    if get_technique("location_energy_usage", 1) is not None:
        return

    # R1 — living at the location is the most powerful usage.
    if get_rule("USAGE-LIVE-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="USAGE-LIVE-001",
                rule_version="1.0",
                rule_name="Living Is The Strongest Usage",
                source_text=(
                    "If the person can relocate to the supportive location, living "
                    "there embodies the supportive energy every day — the strongest mode."
                ),
                priority=1,
                category="location_energy_usage",
                conditions=(
                    ConditionGroup(
                        operator="AND",
                        conditions=(
                            Condition(
                                "relocation.supportive.identified",
                                "==",
                                True,
                                "A supportive location has been identified.",
                            ),
                            Condition(
                                "relocation.usage.live",
                                "==",
                                True,
                                "The person can live at the supportive location.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.usage.recommendation": "live"},
                    description="Recommend living at the supportive location.",
                ),
                explanation=(
                    "Living at the location embodies the supportive energy daily; "
                    "the strongest of the three usage modes."
                ),
                tags=("relocation", "usage"),
            )
        )

    # R2 — traveling absorbs and returns energy.
    if get_rule("USAGE-TRAV-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="USAGE-TRAV-001",
                rule_version="1.0",
                rule_name="Traveling Absorbs And Returns",
                source_text=(
                    "If full relocation is not chosen but travel is possible, "
                    "traveling there (vacation, meeting, workshop) absorbs the energy "
                    "and brings it home."
                ),
                priority=2,
                category="location_energy_usage",
                conditions=(
                    ConditionGroup(
                        operator="AND",
                        conditions=(
                            Condition(
                                "relocation.supportive.identified",
                                "==",
                                True,
                                "A supportive location has been identified.",
                            ),
                            Condition(
                                "relocation.usage.travel",
                                "==",
                                True,
                                "Travel to the supportive location is feasible.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.usage.recommendation": "travel"},
                    description="Recommend traveling to absorb and return the energy.",
                ),
                explanation=(
                    "Traveling to the location lets the person absorb its supportive "
                    "energy and carry it home."
                ),
                tags=("relocation", "usage"),
            )
        )

    # R3 — connecting/importing works without visiting.
    if get_rule("USAGE-IMP-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="USAGE-IMP-001",
                rule_version="1.0",
                rule_name="Connecting Imports The Energy",
                source_text=(
                    "If neither living nor traveling is possible, connect with the "
                    "location's culture, food, language, and geography; direct efforts "
                    "there. This imports the location's energy into one's world."
                ),
                priority=3,
                category="location_energy_usage",
                conditions=(
                    ConditionGroup(
                        operator="AND",
                        conditions=(
                            Condition(
                                "relocation.supportive.identified",
                                "==",
                                True,
                                "A supportive location has been identified.",
                            ),
                            Condition(
                                "relocation.usage.import",
                                "==",
                                True,
                                "Connecting/importing without visiting is chosen.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.usage.recommendation": "import"},
                    description="Recommend connecting/importing the location's energy.",
                ),
                explanation=(
                    "Even without physical presence, connecting with the location "
                    "'imports' its energy — weakest but still supportive."
                ),
                tags=("relocation", "usage"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="location_energy_usage",
        name="Location Energy Usage (Live / Travel / Import)",
        version=1,
        description=(
            "Ranks how to act on an identified supportive location: live (strongest), "
            "travel (absorb and return), or import/connect (weakest but supportive)."
        ),
        tradition="Western Astrology",
        objective="relocation_usage",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.supportive.identified",
            "relocation.usage.live",
            "relocation.usage.travel",
            "relocation.usage.import",
            "relocation.map.supportive.count",
        ),
        dependencies=("relocation_engine", "supportive_location_classifier"),
        rule_refs=(
            TechniqueRuleRef("USAGE-LIVE-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("USAGE-TRAV-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("USAGE-IMP-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "supportive-location identification requires a classifier producer that "
            "does not yet exist; `relocation.supportive.identified` is caller context.",
        ),
    )
    register_technique(tech)


init_location_energy_usage()
