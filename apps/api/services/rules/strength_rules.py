"""
AstroOS — Strength-Based Rules (Module 13 Phase 1)

Rules over shadbala.* and ashtakavarga.* facts — demonstrating the Rule
Engine consuming Module 9 and Module 10 output through the Fact Layer.

Thresholds here are pragmatic, not asserted as exact classical
"Required Bala" cutoffs — Module 9's ShadbalaEngine still has known
gaps (Varsha/Masa lord unimplemented), so a rule requiring the full
classical threshold would rarely fire even on genuinely strong charts.
Flagged in each rule's explanation rather than left implicit.
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.services.rule_registry import register_rule

register_rule(RuleDefinition(
    rule_id="RULE-STRENGTH-001",
    rule_version="1.0",
    rule_name="Strong Jupiter via Shadbala",
    source_text="BPHS Ch. 27 — Shadbala, Required Bala concept",
    priority=6,
    category="strength",
    conditions=(
        Condition("shadbala.jupiter.total", ">", 3.5, "Jupiter's Shadbala total exceeds 3.5 Rupas"),
    ),
    conclusion=Conclusion(
        derived_facts={"career.wisdom_capacity": "strong"},
        description="A comparatively strong Jupiter (by Shadbala) supports sound judgment and access to opportunity",
    ),
    explanation=(
        "Threshold is pragmatic, not the full classical Required Bala for Jupiter (~6.5 Rupas) — "
        "this codebase's Shadbala coverage has known gaps (Varsha/Masa lord unimplemented), so the "
        "full classical threshold would rarely fire even on genuinely strong charts."
    ),
    tags=("shadbala", "jupiter", "strength"),
))

register_rule(RuleDefinition(
    rule_id="RULE-STRENGTH-002",
    rule_version="1.0",
    rule_name="Strong Saturn via Shadbala",
    source_text="BPHS Ch. 27 — Shadbala, Required Bala concept",
    priority=5,
    category="strength",
    conditions=(
        Condition("shadbala.saturn.total", ">", 3.5, "Saturn's Shadbala total exceeds 3.5 Rupas"),
    ),
    conclusion=Conclusion(
        derived_facts={"discipline.endurance_capacity": "strong"},
        description="A comparatively strong Saturn (by Shadbala) supports endurance and disciplined effort over time",
    ),
    explanation="Same pragmatic-threshold caveat as RULE-STRENGTH-001 — see that rule's explanation.",
    tags=("shadbala", "saturn", "strength"),
))

register_rule(RuleDefinition(
    rule_id="RULE-STRENGTH-003",
    rule_version="1.0",
    rule_name="High Jupiter Ashtakavarga Bindus",
    source_text="Classical Ashtakavarga principle — 6+ bindus in a planet's own sign is considered strong",
    priority=6,
    category="strength",
    conditions=(
        Condition("ashtakavarga.jupiter.bindu", ">=", 6, "Jupiter has 6 or more bindus in its current sign"),
    ),
    conclusion=Conclusion(
        derived_facts={"jupiter.ashtakavarga_strength": "high"},
        description="6 or more bindus is classically considered a strong Ashtakavarga placement",
    ),
    explanation="Bhinnashtakavarga bindu count in the sign Jupiter currently occupies (natal), out of a possible 8.",
    tags=("ashtakavarga", "jupiter", "strength"),
))

register_rule(RuleDefinition(
    rule_id="RULE-STRENGTH-004",
    rule_version="1.0",
    rule_name="Low Saturn Ashtakavarga Bindus",
    source_text="Classical Ashtakavarga principle — 2 or fewer bindus is considered a weak placement",
    priority=5,
    category="strength",
    conditions=(
        Condition("ashtakavarga.saturn.bindu", "<=", 2, "Saturn has 2 or fewer bindus in its current sign"),
    ),
    conclusion=Conclusion(
        derived_facts={"saturn.ashtakavarga_strength": "weak"},
        description="2 or fewer bindus is classically considered a weak Ashtakavarga placement, more sensitive to transit stress",
    ),
    explanation="Bhinnashtakavarga bindu count in the sign Saturn currently occupies (natal), out of a possible 8.",
    tags=("ashtakavarga", "saturn", "strength"),
))
