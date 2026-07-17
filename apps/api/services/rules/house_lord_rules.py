"""
AstroOS — House-Lord Placement Rules (Module 13 Phase 2)

New rule category using house.{N}.lord_house — a small FactBuilder-side
derivation (which house a house's already-computed lord currently
occupies) added specifically to enable these classically important
"lord placement" rules without RuleEngine needing indirect/templated
fact-key lookups.
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.services.rule_registry import register_rule

register_rule(RuleDefinition(
    rule_id="RULE-HOUSELORD-001",
    rule_version="1.0",
    rule_name="10th Lord in 10th House",
    source_text="Classical Parashari principle — a house lord placed in its own house is strong and self-reinforcing",
    priority=7,
    category="house_lord",
    conditions=(
        Condition("house.10.lord_house", "==", 10, "10th lord occupies the 10th house"),
    ),
    conclusion=Conclusion(
        derived_facts={"career.self_made_success": "high"},
        description="A self-placed 10th lord classically indicates career success built through the native's own direct effort",
    ),
    explanation="The 10th lord occupying its own house is a strong, stable placement for career significations.",
    tags=("house_lord", "10th_house", "career"),
))

register_rule(RuleDefinition(
    rule_id="RULE-HOUSELORD-002",
    rule_version="1.0",
    rule_name="1st Lord in 1st House",
    source_text="Classical Parashari principle — a house lord placed in its own house is strong and self-reinforcing",
    priority=6,
    category="house_lord",
    conditions=(
        Condition("house.1.lord_house", "==", 1, "1st lord (lagna lord) occupies the 1st house"),
    ),
    conclusion=Conclusion(
        derived_facts={"personality.strong_self_identity": "high"},
        description="A self-placed lagna lord classically indicates a strong, well-defined sense of self",
    ),
    explanation="The lagna lord occupying the lagna itself is considered one of the strongest possible lagna-lord placements.",
    tags=("house_lord", "1st_house", "lagna", "personality"),
))

register_rule(RuleDefinition(
    rule_id="RULE-HOUSELORD-003",
    rule_version="1.0",
    rule_name="9th Lord in 9th House",
    source_text="Classical Parashari principle — a house lord placed in its own house is strong and self-reinforcing",
    priority=6,
    category="house_lord",
    conditions=(
        Condition("house.9.lord_house", "==", 9, "9th lord occupies the 9th house"),
    ),
    conclusion=Conclusion(
        derived_facts={"fortune.self_reinforcing": "high"},
        description="A self-placed 9th lord classically strengthens fortune, dharma, and higher learning significations",
    ),
    explanation="The 9th lord (house of fortune/dharma) occupying its own house is a strong, stable placement.",
    tags=("house_lord", "9th_house", "fortune"),
))

register_rule(RuleDefinition(
    rule_id="RULE-HOUSELORD-004",
    rule_version="1.0",
    rule_name="7th Lord in 1st House",
    source_text="Classical Parashari principle — a house lord's placement colors the significations of the house it lands in",
    priority=5,
    category="house_lord",
    conditions=(
        Condition("house.7.lord_house", "==", 1, "7th lord occupies the 1st house"),
    ),
    conclusion=Conclusion(
        derived_facts={"relationships.partnership_orientation": "high"},
        description="The 7th lord (partnerships) placed in the 1st house classically brings partnership themes strongly into the personality itself",
    ),
    explanation="A house lord's placement in the lagna brings that house's significations directly into the native's self-expression.",
    tags=("house_lord", "7th_house", "1st_house", "relationships"),
))
