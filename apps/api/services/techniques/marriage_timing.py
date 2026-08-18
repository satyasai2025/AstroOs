"""
AstroOS — Technique Fixture: Parashari Marriage Timing

Evaluates marriage timing triggers based on:
  1. Venus (Karaka) Mahadasha or Antardasha activation
  2. Venus placement in Kendra (1/4/7/10) or 7th house
  3. Jupiter benefic influence / placement in angle or 7th

Purely declarative rules evaluated on canonical facts.
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

_SOURCE = "Brihat Parashara Hora Shastra, Ch. 18 (Judgement of 7th House & Vivaha)"


def init_marriage_timing() -> None:
    if get_technique("marriage_timing", 1) is not None:
        return

    # Primary Rule 1: Venus Dasha activation
    if get_rule("MARR-VIM-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="MARR-VIM-001",
                rule_version="1.0",
                rule_name="Venus Dasha Activation",
                source_text="Venus being the natural karaka of marriage, its dasha period triggers marriage potentials.",
                priority=8,
                category="marriage_timing",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition("dasha.current_mahadasha", "==", "venus", "Current Mahadasha lord is Venus"),
                            Condition("dasha.antardasha_lord", "==", "venus", "Current Antardasha lord is Venus"),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"timing.marriage_dasha": "active"},
                    description="Venus Dasha period active for marriage.",
                ),
                explanation="Venus Mahadasha or Antardasha activates the natural significations of marriage and partnerships.",
                tags=("marriage", "dasha"),
            )
        )

    # Primary Rule 2: 7th House Lord Dasha activation
    if get_rule("MARR-7TH-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="MARR-7TH-001",
                rule_version="1.0",
                rule_name="Venus in Angular / 7th Placement",
                source_text="Venus placed in the 1st, 4th, 7th, or 10th house supports timely marriage.",
                priority=7,
                category="marriage_timing",
                conditions=(
                    Condition("planet.venus.house", "in", (1, 4, 7, 10), "Venus in a Kendra house (1, 4, 7, 10)"),
                ),
                conclusion=Conclusion(
                    derived_facts={"timing.venus_angular": "true"},
                    description="Angular Venus indicates strong relationship potential.",
                ),
                explanation="Venus situated in a Kendra provides strength to matrimonial prospects.",
                tags=("marriage", "houses"),
            )
        )

    # Supporting Rule: Jupiter benefic influence on 7th
    if get_rule("MARR-JUP-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="MARR-JUP-001",
                rule_version="1.0",
                rule_name="Jupiter Auspicious Aspect on 7th",
                source_text="Jupiter occupying houses 1, 3, 7, or 11 casts aspect or occupies the 7th house.",
                priority=5,
                category="marriage_timing",
                conditions=(
                    Condition("planet.jupiter.house", "in", (1, 3, 7, 11), "Jupiter influencing the 7th house"),
                ),
                conclusion=Conclusion(
                    derived_facts={"timing.jupiter_blessing": "present"},
                    description="Jupiter aspects or occupies the 7th house of marriage.",
                ),
                explanation="Jupiter's benefic aspect or placement sanctifies the 7th house, facilitating alliance.",
                tags=("marriage", "jupiter"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="marriage_timing",
        name="Parashari Marriage Timing",
        version=1,
        description="Comprehensive evaluation of marriage activation through Dasha lord, Venus placement, and Jupiterian beneficence.",
        tradition="Parashari",
        objective="marriage_timing",
        source_references=(_SOURCE,),
        required_inputs=("planet.venus.house", "planet.jupiter.house"),
        dependencies=("D1", "dasha"),
        rule_refs=(
            TechniqueRuleRef("MARR-VIM-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("MARR-7TH-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("MARR-JUP-001", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
    )
    register_technique(tech)


init_marriage_timing()