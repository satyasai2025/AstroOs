"""
AstroOS — Technique Fixture: Panch Mahapurusha Yogas (BPHS Ch. 75)

Decouples Yoga Existence / Formation from Strength Potency and Affliction:
  1. Primary Rule: Structural Formation / Existence (Kendra + Own/Exalted Sign)
  2. Supporting Rule: Peak Exaltation Dignity (Strength Modifier)
  3. Contradicting Rule: Solar Combustion Affliction (Strength Reduction / Impairment)
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

_SOURCE = "Brihat Parashara Hora Shastra, Ch. 75 (Panch Mahapurusha Yogas)"


def _register_mahapurusha_technique(
    technique_id: str,
    name: str,
    planet: str,
    code: str,
    desc: str,
) -> None:
    if get_technique(technique_id, 1) is not None:
        return

    # 1. Structural Formation / Existence (Binary)
    rule_id_form = f"MAHA-{code}-001"
    if get_rule(rule_id_form) is None:
        rule = RuleDefinition(
            rule_id=rule_id_form,
            rule_version="1.0",
            rule_name=f"{name} Structural Formation",
            source_text=f"BPHS 75: {planet.capitalize()} placed in a Kendra from Lagna (1, 4, 7, 10) in own sign or exaltation forms {name}.",
            priority=8,
            category="panch_mahapurusha",
            conditions=(
                Condition(f"planet.{planet}.house", "in", (1, 4, 7, 10), f"{planet.capitalize()} in a Kendra house (1, 4, 7, 10)"),
                ConditionGroup(
                    operator="OR",
                    conditions=(
                        Condition(f"planet.{planet}.exalted", "==", True, f"{planet.capitalize()} is exalted"),
                        Condition(f"planet.{planet}.own_sign", "==", True, f"{planet.capitalize()} is in own sign"),
                    ),
                ),
            ),
            conclusion=Conclusion(
                derived_facts={f"yoga.{technique_id}.exists": "true"},
                description=f"{name} is structurally formed in the natal chart.",
            ),
            explanation=f"{planet.capitalize()} fulfills the classical requirement of angular placement in a dignity sign.",
            tags=("panch_mahapurusha", "existence", planet),
        )
        register_rule(rule)

    # 2. Strength Modifier: Exaltation Potency (Supporting)
    rule_id_exalt = f"MAHA-{code}-EXALT"
    if get_rule(rule_id_exalt) is None:
        rule_exalt = RuleDefinition(
            rule_id=rule_id_exalt,
            rule_version="1.0",
            rule_name=f"{name} Peak Exaltation Strength",
            source_text=f"{planet.capitalize()} is exalted, elevating the yoga's functional strength to maximum potency.",
            priority=5,
            category="panch_mahapurusha",
            conditions=(
                Condition(f"planet.{planet}.exalted", "==", True, f"{planet.capitalize()} is in its highest exaltation sign"),
            ),
            conclusion=Conclusion(
                derived_facts={f"yoga.{technique_id}.strength": "peak_exalted"},
                description=f"{planet.capitalize()} operates at peak exaltation strength.",
            ),
            explanation=f"Exaltation provides maximum directional and positional dignity to {name}.",
            tags=("panch_mahapurusha", "strength", planet),
        )
        register_rule(rule_exalt)

    # 3. Affliction Modifier: Combustion Impairment (Contradicting)
    rule_id_combust = f"MAHA-{code}-COMBUST"
    if get_rule(rule_id_combust) is None:
        rule_combust = RuleDefinition(
            rule_id=rule_id_combust,
            rule_version="1.0",
            rule_name=f"{name} Combustion Impairment",
            source_text=f"{planet.capitalize()} is combust by the Sun, reducing the manifestation power of {name}.",
            priority=5,
            category="panch_mahapurusha",
            conditions=(
                Condition(f"planet.{planet}.combust", "==", True, f"{planet.capitalize()} is combust (Asta) by Sun"),
            ),
            conclusion=Conclusion(
                derived_facts={f"yoga.{technique_id}.affliction": "combust"},
                description=f"{name} potency is weakened due to solar combustion.",
            ),
            explanation="Combustion deprives the planet of outward rays, causing the yoga's results to manifest with internal struggle.",
            tags=("panch_mahapurusha", "affliction", planet),
        )
        register_rule(rule_combust)

    tech = TechniqueDefinition(
        technique_id=technique_id,
        name=name,
        version=1,
        description=desc,
        tradition="Parashari",
        objective="panch_mahapurusha",
        source_references=(_SOURCE,),
        required_inputs=(
            f"planet.{planet}.house",
            f"planet.{planet}.exalted",
            f"planet.{planet}.own_sign",
            f"planet.{planet}.combust",
        ),
        dependencies=("D1",),
        rule_refs=(
            TechniqueRuleRef(rule_id=rule_id_form, rule_version="1.0", role=RuleRole.PRIMARY, provenance=ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef(rule_id=rule_id_exalt, rule_version="1.0", role=RuleRole.SUPPORTING, provenance=ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef(rule_id=rule_id_combust, rule_version="1.0", role=RuleRole.CONTRADICTING, provenance=ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
    )
    register_technique(tech)


def init_panch_mahapurusha() -> None:
    _register_mahapurusha_technique(
        "ruchaka_yoga",
        "Ruchaka Yoga",
        "mars",
        "RUCH",
        "Mars in Kendra in Aries, Scorpio, or Capricorn gives executive daring, military/athletic leadership, and high physical vitality.",
    )
    _register_mahapurusha_technique(
        "bhadra_yoga",
        "Bhadra Yoga",
        "mercury",
        "BHAD",
        "Mercury in Kendra in Gemini or Virgo gives intellectual mastery, mathematical and communicative eloquence, and longevity.",
    )
    _register_mahapurusha_technique(
        "hamsa_yoga",
        "Hamsa Yoga",
        "jupiter",
        "HAMS",
        "Jupiter in Kendra in Cancer, Sagittarius, or Pisces confers spiritual wisdom, societal respect, righteous character, and grace.",
    )
    _register_mahapurusha_technique(
        "malavya_yoga",
        "Malavya Yoga",
        "venus",
        "MAL",
        "Venus in Kendra in Taurus, Libra, or Pisces gives refined aesthetic genius, marital prosperity, artistic grace, and material comfort.",
    )
    _register_mahapurusha_technique(
        "shasha_yoga",
        "Shasha Yoga",
        "saturn",
        "SHAS",
        "Saturn in Kendra in Libra, Capricorn, or Aquarius confers organizational authority, perseverance, command over masses, and enduring legacy.",
    )


init_panch_mahapurusha()