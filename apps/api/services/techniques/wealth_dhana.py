"""
AstroOS — Technique Fixture: Classical Dhana Yogas (BPHS Ch. 41)

Granularly models discrete classical lord combinations from BPHS Ch. 41:
  1. DHAN-2-11-001 (Primary): 2nd Lord in 11th OR 11th Lord in 2nd (Dhana-Labha Interconnection)
  2. DHAN-9TH-001 (Supporting): 9th (Bhagya / Fortune) Lord in 1, 2, 5, 9, 10, 11
  3. DHAN-5TH-001 (Supporting): 5th (Purva Punya) Lord in 5, 9, 11
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

_SOURCE = "Brihat Parashara Hora Shastra, Ch. 41 (Dhana Yogas / Combinations for Wealth)"


def init_wealth_dhana() -> None:
    if get_technique("dhana_yoga", 1) is not None:
        return

    # 1. Primary: 2nd Lord in 11th OR 11th Lord in 2nd
    if get_rule("DHAN-2-11-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="DHAN-2-11-001",
                rule_version="1.0",
                rule_name="Dhana-Labha Lord Interconnection (2nd/11th)",
                source_text="BPHS 41.3: If 2nd lord is in 11th house or 11th lord is in 2nd house, abundant wealth accumulation is indicated.",
                priority=8,
                category="wealth_dhana",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition("house.2.lord_house", "==", 11, "2nd house lord is situated in 11th house"),
                            Condition("house.11.lord_house", "==", 2, "11th house lord is situated in 2nd house"),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"wealth.dhana_labha_link": "present"},
                    description="Interconnection between Dhana (2nd) and Labha (11th) houses.",
                ),
                explanation="Capital assets (2nd house) generate recurring income and gains (11th house).",
                tags=("wealth", "dhana_yoga", "bphs"),
            )
        )

    # 2. Supporting: 9th (Fortune / Bhagya) Lord Placement
    if get_rule("DHAN-9TH-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="DHAN-9TH-001",
                rule_version="1.0",
                rule_name="9th Lord in Wealth / Angle / Trine House",
                source_text="BPHS 41.5: 9th lord placed in 1st, 2nd, 5th, 9th, 10th, or 11th house sustains wealth with enduring fortune.",
                priority=6,
                category="wealth_dhana",
                conditions=(
                    Condition("house.9.lord_house", "in", (1, 2, 5, 9, 10, 11), "9th lord placed in 1, 2, 5, 9, 10, 11"),
                ),
                conclusion=Conclusion(
                    derived_facts={"wealth.bhagya_sustained": "true"},
                    description="Lord of fortune actively stabilizes wealth channels.",
                ),
                explanation="Bhagya (9th) lord in auspicious houses prevents wealth dissipation.",
                tags=("wealth", "fortune", "bphs"),
            )
        )

    # 3. Supporting: 5th (Purva Punya) Lord Placement
    if get_rule("DHAN-5TH-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="DHAN-5TH-001",
                rule_version="1.0",
                rule_name="5th Lord in Speculative / Fortune / Gains House",
                source_text="BPHS 41.4: 5th lord placed in 5th, 9th, or 11th house grants wealth through intelligence, speculation, and merit.",
                priority=6,
                category="wealth_dhana",
                conditions=(
                    Condition("house.5.lord_house", "in", (5, 9, 11), "5th lord placed in 5, 9, or 11"),
                ),
                conclusion=Conclusion(
                    derived_facts={"wealth.purva_punya_gains": "true"},
                    description="5th lord in 5, 9, or 11 confers wealth through intellect and past merit.",
                ),
                explanation="Purva Punya (5th) lord placed in trines or gains multiplies speculative luck.",
                tags=("wealth", "speculation", "bphs"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="dhana_yoga",
        name="Classical Dhana Yogas (BPHS Ch. 41)",
        version=1,
        description="Evaluates classical wealth combinations through tested 2nd (Dhana), 11th (Labha), 9th (Bhagya), and 5th (Purva Punya) lord placements.",
        tradition="Parashari",
        objective="wealth",
        source_references=(_SOURCE,),
        required_inputs=(
            "house.2.lord_house",
            "house.11.lord_house",
            "house.9.lord_house",
            "house.5.lord_house",
        ),
        dependencies=("D1",),
        rule_refs=(
            TechniqueRuleRef("DHAN-2-11-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("DHAN-9TH-001", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("DHAN-5TH-001", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
    )
    register_technique(tech)


init_wealth_dhana()