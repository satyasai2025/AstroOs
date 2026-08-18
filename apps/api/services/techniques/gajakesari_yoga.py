"""
AstroOS — Reference Technique Fixture: Gajakesari Yoga (Parashari)

A classical Raja Yoga technique with decoupled Existence vs Strength vs Affliction:
  1. Primary Rule GAJA-001: Structural Formation (Jupiter in Kendra 1/4/7/10 from Moon)
  2. Supporting Rule GAJA-002: Dignity Strength Modifier (Jupiter in Exaltation/Own Sign)
  3. Contradicting Rule GAJA-003: Combustion Affliction (Jupiter combust by Sun reduces potency)
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

_SOURCE = "Brihat Parashara Hora Shastra, Ch. 36 & Phaladeepika, Ch. 6 (Gajakesari Yoga)"


def init_gajakesari() -> None:
    if get_technique("gajakesari_yoga", 1) is not None:
        return

    # 1. Structural Formation (Binary Existence)
    if get_rule("GAJA-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="GAJA-001",
                rule_version="1.0",
                rule_name="Gajakesari Yoga Formation (Kendra from Moon)",
                source_text="BPHS 36.3: When Jupiter is in a Kendra (1st, 4th, 7th, or 10th house) from the Moon, Gajakesari Yoga is formed.",
                priority=9,
                category="raja_yoga",
                conditions=(
                    Condition("planet.moon.house", "in", (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), "Moon house is known"),
                    Condition("planet.jupiter.house", "in", (1, 4, 7, 10), "Jupiter is situated in an angular Kendra house (1, 4, 7, 10)"),
                ),
                conclusion=Conclusion(
                    derived_facts={"yoga.gajakesari.exists": "true"},
                    description="Gajakesari Yoga is structurally formed in the chart.",
                ),
                explanation="Mutual Kendra relationship between Moon and Jupiter creates the elephant-lion majesty of Gajakesari.",
                tags=("yoga", "raja_yoga", "gajakesari"),
            )
        )

    # 2. Dignity & Strength Potency Modifier (Supporting)
    if get_rule("GAJA-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="GAJA-002",
                rule_version="1.0",
                rule_name="Jupiter Dignity Strength Modifier",
                source_text="When Jupiter is exalted (Cancer) or in own sign (Sagittarius/Pisces), Gajakesari operates at peak strength.",
                priority=5,
                category="raja_yoga",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition("planet.jupiter.exalted", "==", True, "Jupiter is exalted in Cancer"),
                            Condition("planet.jupiter.own_sign", "==", True, "Jupiter is in own sign"),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"yoga.gajakesari.strength": "dignified"},
                    description="Dignified Jupiter magnifies Gajakesari's renown and wisdom.",
                ),
                explanation="High essential dignity ensures noble conduct, enduring wealth, and scholarly respect.",
                tags=("yoga", "strength", "jupiter"),
            )
        )

    # 3. Combustion Affliction Modifier (Contradicting)
    if get_rule("GAJA-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="GAJA-003",
                rule_version="1.0",
                rule_name="Jupiter Combustion Affliction",
                source_text="Combustion of Jupiter by the Sun reduces the manifest potency of Gajakesari.",
                priority=5,
                category="raja_yoga",
                conditions=(
                    Condition("planet.jupiter.combust", "==", True, "Jupiter is combust (Asta)"),
                ),
                conclusion=Conclusion(
                    derived_facts={"yoga.gajakesari.affliction": "combust"},
                    description="Combustion impairs the outer brilliance of Gajakesari.",
                ),
                explanation="Combustion causes wisdom and benefits to remain latent or delayed.",
                tags=("yoga", "affliction", "jupiter"),
            )
        )

    register_technique(
        TechniqueDefinition(
            technique_id="gajakesari_yoga",
            name="Gajakesari Yoga",
            version=1,
            description="Classical Parashari Raja Yoga formed by Jupiter in a Kendra from the Moon, with separate dignity strength and combustion modifiers.",
            tradition="Parashari",
            objective="raja_yoga",
            source_references=(_SOURCE,),
            required_inputs=(
                "planet.moon.house",
                "planet.jupiter.house",
                "planet.jupiter.exalted",
                "planet.jupiter.own_sign",
                "planet.jupiter.combust",
            ),
            dependencies=("D1",),
            rule_refs=(
                TechniqueRuleRef("GAJA-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
                TechniqueRuleRef("GAJA-002", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
                TechniqueRuleRef("GAJA-003", "1.0", RuleRole.CONTRADICTING, ProvenanceStatus.SOURCE_DERIVED),
            ),
            provenance=ProvenanceStatus.SOURCE_DERIVED,
            status="research",
        )
    )


init_gajakesari()