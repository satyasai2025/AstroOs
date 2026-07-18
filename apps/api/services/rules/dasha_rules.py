"""
AstroOS — Dasha-Based Rules (Module 13 Phase B)

Rules correlating active dasha periods with planetary activations.
Uses dasha.* facts produced by FactBuilder._build_dasha_facts().
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.services.rule_registry import register_rule

register_rule(RuleDefinition(
    rule_id="RULE-DASHA-001",
    rule_version="1.0",
    rule_name="Jupiter Mahadasha Active — Wisdom Period",
    source_text="Classical Parashari Dasha Phala — Jupiter's period activates wisdom and expansion significations",
    priority=8,
    category="dasha",
    conditions=(
        Condition("dasha.current_lord", "==", "jupiter", "Jupiter is the current dasha lord"),
    ),
    conclusion=Conclusion(
        derived_facts={"timing.wisdom_period_active": True},
        description="Jupiter mahadasha classically activates wisdom, growth, and spiritual significations across all houses",
    ),
    explanation="The planet ruling the current mahadasha period becomes a focal significator across all areas of life.",
    tags=("dasha", "jupiter", "timing"),
))

register_rule(RuleDefinition(
    rule_id="RULE-DASHA-002",
    rule_version="1.0",
    rule_name="Saturn Mahadasha Active — Discipline Period",
    source_text="Classical Parashari Dasha Phala — Saturn's period activates discipline and restructuring",
    priority=8,
    category="dasha",
    conditions=(
        Condition("dasha.current_lord", "==", "saturn", "Saturn is the current dasha lord"),
    ),
    conclusion=Conclusion(
        derived_facts={"timing.discipline_period_active": True},
        description="Saturn mahadasha classically activates discipline, delay, and karmic restructuring themes",
    ),
    explanation="Saturn's period is traditionally a time of hard work, learning through experience, and gradual maturation.",
    tags=("dasha", "saturn", "timing"),
))

register_rule(RuleDefinition(
    rule_id="RULE-DASHA-003",
    rule_version="1.0",
    rule_name="Venus Mahadasha Active — Relationship Period",
    source_text="Classical Parashari Dasha Phala — Venus's period activates relationships and comfort",
    priority=7,
    category="dasha",
    conditions=(
        Condition("dasha.current_lord", "==", "venus", "Venus is the current dasha lord"),
    ),
    conclusion=Conclusion(
        derived_facts={"timing.relationship_period_active": True},
        description="Venus mahadasha classically activates relationships, comfort, and aesthetic significations",
    ),
    explanation="Venus rules relationships, arts, and material comforts — its period brings these themes to the foreground.",
    tags=("dasha", "venus", "timing"),
))
