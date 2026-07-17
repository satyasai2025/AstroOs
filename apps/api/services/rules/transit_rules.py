"""
AstroOS — Transit-Based Rules (Module 13 Phase 1)

Rules over transit.* facts — demonstrating the Rule Engine consuming
Module 11's Transit Engine output through the Fact Layer.
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.services.rule_registry import register_rule

register_rule(RuleDefinition(
    rule_id="RULE-TRANSIT-001",
    rule_version="1.0",
    rule_name="Saturn Sade Sati Active",
    source_text="Classical Gochara principle — Saturn transiting 12th/1st/2nd from natal Moon",
    priority=7,
    category="transit",
    conditions=(
        Condition("transit.saturn.sade_sati", "==", True, "Saturn's Sade Sati is currently active"),
    ),
    conclusion=Conclusion(
        derived_facts={"life_period.pressure_indicated": True},
        description="Sade Sati is classically read as a demanding, restructuring life period, not inherently negative",
    ),
    explanation="Saturn transiting the 12th, 1st, or 2nd house from the natal Moon — a ~7.5 year cycle.",
    tags=("transit", "saturn", "sade_sati"),
))

register_rule(RuleDefinition(
    rule_id="RULE-TRANSIT-002",
    rule_version="1.0",
    rule_name="Saturn Ashtama Shani Active",
    source_text="Classical Gochara principle — Saturn transiting 8th from natal Moon",
    priority=6,
    category="transit",
    conditions=(
        Condition("transit.saturn.ashtama_shani", "==", True, "Saturn's Ashtama Shani is currently active"),
    ),
    conclusion=Conclusion(
        derived_facts={"life_period.transformation_indicated": True},
        description="Ashtama Shani is classically read as a period of significant, often difficult, transformation",
    ),
    explanation="Saturn transiting the 8th house from the natal Moon.",
    tags=("transit", "saturn", "ashtama_shani"),
))

register_rule(RuleDefinition(
    rule_id="RULE-TRANSIT-003",
    rule_version="1.0",
    rule_name="Saturn Transiting Natal 10th House",
    source_text="Classical Gochara principle — the 10th house governs career",
    priority=5,
    category="transit",
    conditions=(
        Condition("transit.saturn.house", "==", 10, "Saturn is transiting the 10th house from natal Moon"),
    ),
    conclusion=Conclusion(
        derived_facts={"career.restructuring_period": True},
        description="Saturn's transit through the 10th house from Moon often coincides with career restructuring or added responsibility",
    ),
    explanation="Saturn's house-from-natal-Moon at the queried transit moment.",
    tags=("transit", "saturn", "career"),
))
