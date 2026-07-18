"""
AstroOS — Temporal & Dignity Rules (Module 13 Phase B)

Rules using temporal dignities and planetary state combinations.
Demonstrates IN/NOT IN operators and ConditionGroup OR patterns.
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, ConditionGroup, Conclusion, RuleDefinition
from apps.api.services.rule_registry import register_rule

register_rule(RuleDefinition(
    rule_id="RULE-TEMPORAL-001",
    rule_version="1.0",
    rule_name="Benefic in Kendras — Strong Foundation",
    source_text="Classical Parashari principle — natural benefics in angular houses strengthen the chart's foundation",
    priority=6,
    category="temporal",
    conditions=(
        Condition("planet.jupiter.house", "in", [1, 4, 7, 10], "Jupiter in a kendra (1/4/7/10)"),
    ),
    conclusion=Conclusion(
        derived_facts={"foundation.kendra_benefic": True},
        description="A natural benefic in a kendra classically strengthens the chart's overall foundation and stability",
    ),
    explanation="Kendras (angular houses) are the pillars of the chart; a benefic there reinforces the native's core strengths.",
    tags=("temporal", "jupiter", "kendra"),
))

register_rule(RuleDefinition(
    rule_id="RULE-TEMPORAL-002",
    rule_version="1.0",
    rule_name="Malefic Not in Kendras — Reduced Obstruction",
    source_text="Classical Parashari principle — malefics in kendras can create obstruction unless they are yogakarakas",
    priority=5,
    category="temporal",
    conditions=(
        Condition("planet.mars.house", "not_in", [1, 4, 7, 10], "Mars NOT in a kendra (1/4/7/10)"),
    ),
    conclusion=Conclusion(
        derived_facts={"foundation.kendra_malefic_obstruction": "reduced"},
        description="A malefic not occupying a kendra reduces the potential for kendra-born obstruction",
    ),
    explanation="Malefics in kendras can create doshas unless they are lords of trines — their absence from kendras is generally favorable.",
    tags=("temporal", "mars", "kendra"),
))

register_rule(RuleDefinition(
    rule_id="RULE-TEMPORAL-003",
    rule_version="1.0",
    rule_name="Exalted or Own-Sign Planet in Kendra — Strong Dignity",
    source_text="Classical principle — dignity and angular placement compound",
    priority=8,
    category="temporal",
    conditions=(
        ConditionGroup("OR", (
            Condition("planet.jupiter.exalted", "==", True, "Jupiter is exalted"),
            Condition("planet.jupiter.own_sign", "==", True, "Jupiter is in own sign"),
        )),
        Condition("planet.jupiter.house", "in", [1, 4, 7, 10], "Jupiter in a kendra"),
    ),
    conclusion=Conclusion(
        derived_facts={"jupiter.compounded_dignity": "very_high"},
        description="An exalted or own-sign Jupiter in a kendra creates a compounded strength rare in classical evaluation",
    ),
    explanation="This rule demonstrates ConditionGroup OR: either exaltation OR own-sign combined with kendra placement produces the result.",
    tags=("temporal", "jupiter", "dignity", "kendra", "compound"),
))

register_rule(RuleDefinition(
    rule_id="RULE-TEMPORAL-004",
    rule_version="1.0",
    rule_name="Multiple Malefics in Angular Houses — Kendra Dosha",
    source_text="Classical Parashari principle — several natural malefics occupying kendras can indicate structural challenges",
    priority=6,
    category="temporal",
    conditions=(
        Condition("planet.mars.house", "in", [1, 4, 7, 10], "Mars in a kendra"),
        Condition("planet.saturn.house", "in", [1, 4, 7, 10], "Saturn in a kendra"),
    ),
    conclusion=Conclusion(
        derived_facts={"structural.kendra_malefic_dosha": "indicated"},
        description="Multiple natural malefics occupying angular houses classically indicates heightened structural life challenges",
    ),
    explanation="Saturn and Mars together in kendras is a classical marker of kendra dosha, read as a life requiring extra effort in foundational areas.",
    tags=("temporal", "mars", "saturn", "kendra", "dosha"),
))
