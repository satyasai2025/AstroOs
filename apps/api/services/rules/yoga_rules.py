"""
AstroOS — Yoga-Based Rules (Module 13 Phase 1)

Rules over yoga.* facts — demonstrating the Rule Engine consuming
Module 8's Yoga Engine output through the Fact Layer, never calling
YogaEngine directly.
"""

from __future__ import annotations

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.services.rule_registry import register_rule

register_rule(RuleDefinition(
    rule_id="RULE-YOGA-001",
    rule_version="1.0",
    rule_name="Ruchaka Yoga Present",
    source_text="BPHS — Panch Mahapurusha Yoga",
    priority=9,
    category="yoga",
    conditions=(
        Condition("yoga.BPHS-PM-001.present", "==", True, "Ruchaka Yoga is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"physical_vitality.mars_strength": "high"},
        description="Ruchaka Yoga (Mars Panch Mahapurusha) indicates strong physical courage, drive, and vitality",
    ),
    explanation="One of the 5 classical Panch Mahapurusha Yogas — Mars exalted or in own sign, in a kendra from lagna.",
    tags=("yoga", "mars", "panch_mahapurusha"),
))

register_rule(RuleDefinition(
    rule_id="RULE-YOGA-002",
    rule_version="1.0",
    rule_name="Hamsa Yoga Present",
    source_text="BPHS — Panch Mahapurusha Yoga",
    priority=9,
    category="yoga",
    conditions=(
        Condition("yoga.BPHS-PM-003.present", "==", True, "Hamsa Yoga is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"character.spiritual_inclination": "high"},
        description="Hamsa Yoga (Jupiter Panch Mahapurusha) indicates strong wisdom, ethics, and spiritual inclination",
    ),
    explanation="One of the 5 classical Panch Mahapurusha Yogas — Jupiter exalted or in own sign, in a kendra from lagna.",
    tags=("yoga", "jupiter", "panch_mahapurusha"),
))

register_rule(RuleDefinition(
    rule_id="RULE-YOGA-003",
    rule_version="1.0",
    rule_name="Gajakesari Yoga Present",
    source_text="BPHS — Other Major Yoga",
    priority=7,
    category="yoga",
    conditions=(
        Condition("yoga.BPHS-OMY-001.present", "==", True, "Gajakesari Yoga is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"reputation.fame_intelligence": "high"},
        description="Gajakesari Yoga classically indicates intelligence, good reputation, and steady fortune",
    ),
    explanation="Jupiter in a kendra from the Moon — one of the most widely cited classical yogas.",
    tags=("yoga", "jupiter", "moon", "reputation"),
))

register_rule(RuleDefinition(
    rule_id="RULE-YOGA-004",
    rule_version="1.0",
    rule_name="Kendra-Trikona Raja Yoga Present",
    source_text="BPHS — Raja Yoga",
    priority=8,
    category="yoga",
    conditions=(
        Condition("yoga.BPHS-RY-001.present", "==", True, "Kendra-Trikona Raja Yoga is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"status.social_standing": "high"},
        description="Kendra-Trikona Raja Yoga classically indicates elevated status, authority, and success",
    ),
    explanation="A kendra lord associated with a trikona lord — the central classical Raja Yoga formulation.",
    tags=("yoga", "raja_yoga", "status"),
))

register_rule(RuleDefinition(
    rule_id="RULE-YOGA-005",
    rule_version="1.0",
    rule_name="Sasa Yoga Present",
    source_text="BPHS — Panch Mahapurusha Yoga",
    priority=9,
    category="yoga",
    conditions=(
        Condition("yoga.BPHS-PM-005.present", "==", True, "Sasa Yoga is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"discipline.saturn_strength": "high"},
        description="Sasa Yoga (Saturn Panch Mahapurusha) indicates strong discipline, endurance, and organizational capacity",
    ),
    explanation="One of the 5 classical Panch Mahapurusha Yogas — Saturn exalted or in own sign, in a kendra from lagna.",
    tags=("yoga", "saturn", "panch_mahapurusha"),
))

register_rule(RuleDefinition(
    rule_id="RULE-YOGA-006",
    rule_version="1.0",
    rule_name="Malavya Yoga Present",
    source_text="BPHS — Panch Mahapurusha Yoga",
    priority=9,
    category="yoga",
    conditions=(
        Condition("yoga.BPHS-PM-004.present", "==", True, "Malavya Yoga is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"relationships.venus_strength": "high"},
        description="Malavya Yoga (Venus Panch Mahapurusha) indicates strong grace, comfort, and relationship/artistic significations",
    ),
    explanation="One of the 5 classical Panch Mahapurusha Yogas — Venus exalted or in own sign, in a kendra from lagna.",
    tags=("yoga", "venus", "panch_mahapurusha"),
))

register_rule(RuleDefinition(
    rule_id="RULE-YOGA-007",
    rule_version="1.0",
    rule_name="Bhadra Yoga Present",
    source_text="BPHS — Panch Mahapurusha Yoga",
    priority=9,
    category="yoga",
    conditions=(
        Condition("yoga.BPHS-PM-002.present", "==", True, "Bhadra Yoga is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"intellect.mercury_strength": "high"},
        description="Bhadra Yoga (Mercury Panch Mahapurusha) indicates strong intellect, communication, and analytical capacity",
    ),
    explanation="One of the 5 classical Panch Mahapurusha Yogas — Mercury exalted or in own sign, in a kendra from lagna.",
    tags=("yoga", "mercury", "panch_mahapurusha"),
))

register_rule(RuleDefinition(
    rule_id="RULE-YOGA-008",
    rule_version="1.0",
    rule_name="Dhana Yoga (2nd-11th Lord) Present",
    source_text="BPHS — Dhana Yoga",
    priority=6,
    category="yoga",
    conditions=(
        Condition("yoga.BPHS-DY-001.present", "==", True, "Dhana Yoga (2nd-11th lord association) is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"wealth.accumulation_potential": "high"},
        description="An association between the 2nd and 11th lords classically indicates strong wealth-accumulation potential",
    ),
    explanation="The 2nd house governs accumulated wealth, the 11th governs gains — their lords' association is a classical wealth combination.",
    tags=("yoga", "dhana_yoga", "wealth"),
))

register_rule(RuleDefinition(
    rule_id="RULE-YOGA-009",
    rule_version="1.0",
    rule_name="Neecha Bhanga Raja Yoga (Jupiter) Present",
    source_text="BPHS — Neecha Bhanga Raja Yoga",
    priority=8,
    category="yoga",
    conditions=(
        Condition("yoga.BPHS-NBRY-005.present", "==", True, "Jupiter's Neecha Bhanga Raja Yoga is present"),
    ),
    conclusion=Conclusion(
        derived_facts={"fortune.reversal_of_fortune": "high"},
        description="A cancelled Jupiter debilitation classically produces a notable rise in fortune, often after early-life struggle",
    ),
    explanation="Neecha Bhanga (debilitation-cancellation) can turn a weak placement into an unusually strong one when the classical cancellation conditions are met.",
    tags=("yoga", "neecha_bhanga", "jupiter", "fortune"),
))
