"""
AstroOS — Dignity & House Placement Rules (Module 13 Phase 1)

Representative rules over planet.* and house.* facts. Pure declarative
data, registered via register_rule() — no evaluator functions.
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.services.rule_registry import register_rule

register_rule(RuleDefinition(
    rule_id="RULE-DIGNITY-001",
    rule_version="1.0",
    rule_name="Jupiter in Lagna",
    source_text="Classical Parashari principle — a benefic in the 1st house strengthens its significations",
    priority=5,
    category="dignity",
    conditions=(
        Condition("planet.jupiter.house", "==", 1, "Jupiter in the 1st house"),
    ),
    conclusion=Conclusion(
        derived_facts={"personality.wisdom_influence": "high"},
        description="Jupiter in Lagna strengthens wisdom, optimism, and ethical grounding in the personality",
    ),
    explanation="Jupiter placed in the 1st house directly influences the native's self-expression and outlook.",
    tags=("jupiter", "lagna", "personality"),
))

register_rule(RuleDefinition(
    rule_id="RULE-DIGNITY-002",
    rule_version="1.0",
    rule_name="Jupiter Exalted",
    source_text="Classical dignity principle — exaltation is a planet's strongest placement",
    priority=8,
    category="dignity",
    conditions=(
        Condition("planet.jupiter.exalted", "==", True, "Jupiter is exalted"),
    ),
    conclusion=Conclusion(
        derived_facts={"fortune.jupiter_grace": "high"},
        description="An exalted Jupiter gives strong, unobstructed access to its classical significations",
    ),
    explanation="Exaltation is the single strongest dignity state a planet can occupy.",
    tags=("jupiter", "dignity", "exaltation"),
))

register_rule(RuleDefinition(
    rule_id="RULE-DIGNITY-003",
    rule_version="1.0",
    rule_name="Jupiter in Own Sign",
    source_text="Classical dignity principle — own sign gives stable, self-assured strength",
    priority=6,
    category="dignity",
    conditions=(
        Condition("planet.jupiter.own_sign", "==", True, "Jupiter is in its own sign"),
    ),
    conclusion=Conclusion(
        derived_facts={"personality.wisdom_stability": "high"},
        description="Jupiter in its own sign gives stable, well-grounded access to its significations",
    ),
    explanation="Own-sign placement is a strong, stable dignity state, though not as strong as exaltation.",
    tags=("jupiter", "dignity", "own_sign"),
))

register_rule(RuleDefinition(
    rule_id="RULE-DIGNITY-004",
    rule_version="1.0",
    rule_name="Moon Exalted",
    source_text="Classical dignity principle — exaltation is a planet's strongest placement",
    priority=8,
    category="dignity",
    conditions=(
        Condition("planet.moon.exalted", "==", True, "Moon is exalted"),
    ),
    conclusion=Conclusion(
        derived_facts={"emotional_state.stability": "high"},
        description="An exalted Moon gives strong emotional stability and clarity of mind",
    ),
    explanation="The Moon governs mind and emotion; its exaltation directly strengthens both.",
    tags=("moon", "dignity", "exaltation"),
))

register_rule(RuleDefinition(
    rule_id="RULE-DIGNITY-005",
    rule_version="1.0",
    rule_name="Venus in Own Sign",
    source_text="Classical dignity principle — own sign gives stable, self-assured strength",
    priority=6,
    category="dignity",
    conditions=(
        Condition("planet.venus.own_sign", "==", True, "Venus is in its own sign"),
    ),
    conclusion=Conclusion(
        derived_facts={"relationships.harmony": "high"},
        description="Venus in its own sign gives stable, well-grounded relationship harmony",
    ),
    explanation="Own-sign Venus expresses its significations (relationships, harmony, aesthetics) with stability.",
    tags=("venus", "dignity", "own_sign", "relationships"),
))

register_rule(RuleDefinition(
    rule_id="RULE-DIGNITY-006",
    rule_version="1.0",
    rule_name="Mercury Debilitated",
    source_text="Classical dignity principle — debilitation weakens a planet's significations",
    priority=4,
    category="dignity",
    conditions=(
        Condition("planet.mercury.debilitated", "==", True, "Mercury is debilitated"),
    ),
    conclusion=Conclusion(
        derived_facts={"communication.challenge_indicated": True},
        description="A debilitated Mercury can indicate difficulty in clear communication or analytical decision-making",
    ),
    explanation="Debilitation is a planet's weakest dignity state, classically requiring cancellation (Neecha Bhanga) to fully overcome.",
    tags=("mercury", "dignity", "debilitation", "communication"),
))

register_rule(RuleDefinition(
    rule_id="RULE-HOUSE-001",
    rule_version="1.0",
    rule_name="Sun in 10th House",
    source_text="Classical Parashari principle — the 10th house governs career and public standing",
    priority=7,
    category="house_placement",
    conditions=(
        Condition("planet.sun.house", "==", 10, "Sun in the 10th house"),
    ),
    conclusion=Conclusion(
        derived_facts={"career.leadership": "high"},
        description="Sun in the 10th house classically strengthens authority, leadership, and public standing in career matters",
    ),
    explanation="The Sun's natural significations (authority, government, vitality) directly support 10th-house career matters when placed there.",
    tags=("sun", "10th_house", "career"),
))

register_rule(RuleDefinition(
    rule_id="RULE-HOUSE-002",
    rule_version="1.0",
    rule_name="Mars in 10th House",
    source_text="Classical Parashari principle — the 10th house governs career and public standing",
    priority=6,
    category="house_placement",
    conditions=(
        Condition("planet.mars.house", "==", 10, "Mars in the 10th house"),
    ),
    conclusion=Conclusion(
        derived_facts={"career.drive": "high"},
        description="Mars in the 10th house classically gives strong drive, competitiveness, and initiative in career matters",
    ),
    explanation="Mars's natural significations (courage, initiative, competitiveness) directly support 10th-house career drive when placed there.",
    tags=("mars", "10th_house", "career"),
))

# ── Phase 2: combustion and retrograde rules ──────────────────────────────────
# Using planet.*.combust / planet.*.retrograde — Facts that existed since
# Phase 1 (FactBuilder always builds them) but no Phase 1 rule referenced.

register_rule(RuleDefinition(
    rule_id="RULE-DIGNITY-007",
    rule_version="1.0",
    rule_name="Mercury Combust",
    source_text="Classical Parashari principle — combustion (proximity to the Sun) weakens a planet's independent expression",
    priority=4,
    category="dignity",
    conditions=(
        Condition("planet.mercury.combust", "==", True, "Mercury is combust"),
    ),
    conclusion=Conclusion(
        derived_facts={"communication.combustion_challenge": True},
        description="A combust Mercury can indicate the intellect being overshadowed by ego or external authority (the Sun)",
    ),
    explanation="Combustion is a graded classical affliction — this rule reads the boolean flag only, not the orb-based severity Module 2's combustion calculation actually carries.",
    tags=("mercury", "combustion", "communication"),
))

register_rule(RuleDefinition(
    rule_id="RULE-DIGNITY-008",
    rule_version="1.0",
    rule_name="Venus Combust",
    source_text="Classical Parashari principle — combustion weakens a planet's independent expression",
    priority=4,
    category="dignity",
    conditions=(
        Condition("planet.venus.combust", "==", True, "Venus is combust"),
    ),
    conclusion=Conclusion(
        derived_facts={"relationships.combustion_challenge": True},
        description="A combust Venus can indicate relationship or aesthetic significations being overshadowed",
    ),
    explanation="Same combustion caveat as RULE-DIGNITY-007 — boolean flag only, not orb-graded severity.",
    tags=("venus", "combustion", "relationships"),
))

register_rule(RuleDefinition(
    rule_id="RULE-DIGNITY-009",
    rule_version="1.0",
    rule_name="Jupiter Retrograde",
    source_text="Classical principle — retrograde planets are read as internalized or delayed in their expression",
    priority=4,
    category="dignity",
    conditions=(
        Condition("planet.jupiter.retrograde", "==", True, "Jupiter is retrograde"),
    ),
    conclusion=Conclusion(
        derived_facts={"wisdom.expression_style": "internalized"},
        description="Retrograde Jupiter is classically read as introspective wisdom-seeking rather than outward display of it",
    ),
    explanation="Retrograde motion is a directional fact, not inherently negative — read here as a style difference, not a weakness.",
    tags=("jupiter", "retrograde", "wisdom"),
))

register_rule(RuleDefinition(
    rule_id="RULE-DIGNITY-010",
    rule_version="1.0",
    rule_name="Saturn Retrograde",
    source_text="Classical principle — retrograde planets are read as internalized or delayed in their expression",
    priority=4,
    category="dignity",
    conditions=(
        Condition("planet.saturn.retrograde", "==", True, "Saturn is retrograde"),
    ),
    conclusion=Conclusion(
        derived_facts={"discipline.expression_style": "delayed_but_deepened"},
        description="Retrograde Saturn is classically read as discipline and structure developing more slowly but with greater depth",
    ),
    explanation="Retrograde motion is a directional fact, not inherently negative — read here as a style difference, not a weakness.",
    tags=("saturn", "retrograde", "discipline"),
))
