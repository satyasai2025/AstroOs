"""
AstroOS — Compound Rules (Module 13 Phase 2)

Rules with 2+ conditions spanning different fact categories — a
genuine step up from Phase 1's mostly single-condition rules,
demonstrating AND semantics across dignity/yoga/strength/transit facts
together. Still pure declarative data — RuleEngine's generic mechanism
requires every condition to pass, with no special-casing for "compound"
rules; they're just rules whose `conditions` tuple happens to have more
than one entry.
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.services.rule_registry import register_rule

register_rule(RuleDefinition(
    rule_id="RULE-COMPOUND-001",
    rule_version="1.0",
    rule_name="Jupiter Exalted in Lagna",
    source_text="Classical Parashari principle — dignity and house placement compound in effect",
    priority=10,
    category="compound",
    conditions=(
        Condition("planet.jupiter.exalted", "==", True, "Jupiter is exalted"),
        Condition("planet.jupiter.house", "==", 1, "Jupiter is in the 1st house"),
    ),
    conclusion=Conclusion(
        derived_facts={"fortune.jupiter_grace": "very_high"},
        description="Exalted Jupiter placed in the lagna is a classically outstanding combination — both dignity and house placement reinforce each other",
    ),
    explanation="Two independently strong factors (exaltation, lagna placement) compounding on the same planet.",
    tags=("compound", "jupiter", "exaltation", "lagna"),
))

register_rule(RuleDefinition(
    rule_id="RULE-COMPOUND-002",
    rule_version="1.0",
    rule_name="Jupiter Strong by Both Shadbala and Ashtakavarga",
    source_text="Classical principle — Shadbala and Ashtakavarga are independent strength measures that corroborate each other when both are high",
    priority=8,
    category="compound",
    conditions=(
        Condition("shadbala.jupiter.total", ">", 3.5, "Jupiter's Shadbala total exceeds 3.5 Rupas"),
        Condition("ashtakavarga.jupiter.bindu", ">=", 5, "Jupiter has 5 or more Ashtakavarga bindus"),
    ),
    conclusion=Conclusion(
        derived_facts={"jupiter.convergent_strength": "very_high"},
        description="Two independent classical strength systems agreeing is stronger corroboration than either alone",
    ),
    explanation="Shadbala measures positional/temporal strength; Ashtakavarga measures sign-level support from all 8 contributors — genuinely independent systems, so agreement between them is meaningful.",
    tags=("compound", "jupiter", "shadbala", "ashtakavarga"),
))

register_rule(RuleDefinition(
    rule_id="RULE-COMPOUND-003",
    rule_version="1.0",
    rule_name="Ruchaka Yoga With Mars Direct",
    source_text="Classical principle — retrograde motion is classically read as modifying a yoga's expression",
    priority=7,
    category="compound",
    conditions=(
        Condition("yoga.BPHS-PM-001.present", "==", True, "Ruchaka Yoga is present"),
        Condition("planet.mars.retrograde", "==", False, "Mars is direct (not retrograde)"),
    ),
    conclusion=Conclusion(
        derived_facts={"physical_vitality.direct_expression": "high"},
        description="Ruchaka Yoga with Mars direct (not retrograde) classically supports a more outward, immediate expression of the yoga's results",
    ),
    explanation="Combines a yoga's presence (Module 8) with a planetary state fact (Module 2's retrograde computation) not used in the yoga's own definition.",
    tags=("compound", "mars", "ruchaka_yoga", "retrograde"),
))

register_rule(RuleDefinition(
    rule_id="RULE-COMPOUND-004",
    rule_version="1.0",
    rule_name="Sade Sati With Weak Natal Saturn",
    source_text="Classical principle — a transit's impact is read as more pronounced when the transiting planet is natally weak",
    priority=7,
    category="compound",
    conditions=(
        Condition("transit.saturn.sade_sati", "==", True, "Saturn's Sade Sati is currently active"),
        Condition("ashtakavarga.saturn.bindu", "<=", 3, "Saturn has 3 or fewer natal Ashtakavarga bindus"),
    ),
    conclusion=Conclusion(
        derived_facts={"life_period.heightened_pressure": True},
        description="Sade Sati combined with a natally weak Saturn (by Ashtakavarga) is classically read as a more demanding version of the transit",
    ),
    explanation="Combines a current transit condition (Module 11) with a natal strength measure (Module 10) — the transit's intensity is read in light of natal support, not in isolation.",
    tags=("compound", "saturn", "sade_sati", "ashtakavarga"),
))
