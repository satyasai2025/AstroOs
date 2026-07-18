"""
AstroOS — Varga-Based Rules (Module 13 Phase B)

Rules using varga.* facts produced by FactBuilder._build_varga_facts().
Divisional chart placements provide deeper confirmation or modification
of D1 interpretations.
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.services.rule_registry import register_rule

register_rule(RuleDefinition(
    rule_id="RULE-VARGA-001",
    rule_version="1.0",
    rule_name="Sun in Leo in Both D1 and D9 — Varga Bala Strong",
    source_text="Classical Varga principle — same sign in both D1 and D9 strengthens a planet, a concept called varga bala or varga samvada",
    priority=7,
    category="varga",
    conditions=(
        Condition("planet.sun.house", "!=", 0, "Sun is placed somewhere in D1"),
        Condition("varga.sun.D9.rashi", "==", "leo", "Sun in Leo in D9 (Navamsha)"),
    ),
    conclusion=Conclusion(
        derived_facts={"sun.varga_bala": "strong"},
        description="Sun occupying Leo in both D1 and D9 (varga samvada) classically strengthens its significations considerably",
    ),
    explanation="Varga samvada — a planet occupying the same sign in multiple divisional charts — classically indicates a concentrated, reinforced expression of that planet's significations.",
    tags=("varga", "sun", "D9", "varga_bala"),
))

register_rule(RuleDefinition(
    rule_id="RULE-VARGA-002",
    rule_version="1.0",
    rule_name="Jupiter in D9 Navamsha of Exaltation — Strong Wisdom",
    source_text="Classical Varga principle — a planet's D9 placement modifies the D1 reading; navamsha exaltation strengthens even a middling D1 position",
    priority=6,
    category="varga",
    conditions=(
        Condition("varga.jupiter.D9.rashi", "==", "cancer", "Jupiter's D9 (Navamsha) is in Cancer — its exaltation rashi"),
    ),
    conclusion=Conclusion(
        derived_facts={"jupiter.navamsha_dignity": "very_high"},
        description="Jupiter in Cancer navamsha (its exaltation rashi) classically elevates wisdom and spiritual significations even if D1 placement is ordinary",
    ),
    explanation="The D9 (Navamsha) is the most important divisional chart for assessing a planet's innate strength and spiritual quality.",
    tags=("varga", "jupiter", "D9", "navamsha", "dignity"),
))

register_rule(RuleDefinition(
    rule_id="RULE-VARGA-003",
    rule_version="1.0",
    rule_name="Venus in D9 Rashi of Debilitation — Relationship Refinement",
    source_text="Classical Varga principle — a planet in its debilitation navamsha indicates a refined, lessons-oriented expression of its significations",
    priority=5,
    category="varga",
    conditions=(
        Condition("varga.venus.D9.rashi", "==", "virgo", "Venus's D9 (Navamsha) is in Virgo — its debilitation rashi"),
    ),
    conclusion=Conclusion(
        derived_facts={"relationships.navamsha_refinement": "indicated"},
        description="Venus in Virgo navamsha classically suggests relationships as a domain of service, analysis, and refinement rather than ease",
    ),
    explanation="A planet in its debilitation rashi in a divisional chart suggests that the significations develop through challenges, not that they are denied.",
    tags=("varga", "venus", "D9", "navamsha", "relationships"),
))

register_rule(RuleDefinition(
    rule_id="RULE-VARGA-004",
    rule_version="1.0",
    rule_name="Same Planet Rashi Across D1 and D60 — Deep Pattern",
    source_text="Classical Varga principle — the D60 (Shashtiamsha) reveals karmic patterns; a planet in the same rashi in D1 and D60 indicates a strong karmic thread",
    priority=5,
    category="varga",
    conditions=(
        Condition("varga.moon.D60.rashi", "==", "taurus", "Moon in Taurus in D60 (Shashtiamsha)"),
        Condition("planet.moon.rashi", "==", "taurus", "Moon in Taurus in D1"),
    ),
    conclusion=Conclusion(
        derived_facts={"karmic.moon_stability": "deep_rooted"},
        description="Moon in the same rashi in both D1 and D60 suggests a deeply rooted, stable karmic pattern around emotional nature and mind",
    ),
    explanation="The D60 (Shashtiamsha) reveals karmic predispositions from previous births — agreement with D1 suggests continuity of pattern across lives.",
    tags=("varga", "moon", "D60", "karmic"),
))
