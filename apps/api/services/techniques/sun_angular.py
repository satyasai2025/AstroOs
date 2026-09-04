"""
AstroOS — Technique Fixture: Sun Angular ("You Shine")

Identifies locations where the Sun is angular (especially on the
Ascendant or Midheaven) — places where a person "shines": in their
element, with presence, magnetism, and the ability to get jobs, meet
people, and express themselves.

Source: RAG technique 10-sun-angular.md ("Relocational Astrology: How to
Pick a Place").

Purely declarative rules over RelocationEngine Sun facts.
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

_SOURCE = (
    "Relocation & Vedic Astrology — Technique 10 (Sun Angular), "
    "after 'Relocational Astrology: How to Pick a Place'"
)


def init_sun_angular() -> None:
    if get_technique("sun_angular", 1) is not None:
        return

    # R1 — Sun on Ascendant or Midheaven = prime shine location.
    if get_rule("SUN-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="SUN-001",
                rule_version="1.0",
                rule_name="Sun Conjunct Asc/MC Shines",
                source_text=(
                    "Sun conjunct (angular on) the Ascendant or Midheaven marks a "
                    "place where the person shines: in their element, foreground, "
                    "presence and magnetism; good for jobs, meeting people, expression."
                ),
                priority=1,
                category="sun_angular",
                conditions=(
                    ConditionGroup(
                        operator="AND",
                        conditions=(
                            Condition(
                                "relocation.planet.sun.line_in_orb",
                                "==",
                                True,
                                "The Sun line is in orb of an angle.",
                            ),
                            Condition(
                                "relocation.planet.sun.axis",
                                "in",
                                ("asc", "mc", "both"),
                                "The Sun is on the Ascendant or Midheaven axis.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.sun.angular.shine": "true"},
                    description="Prime shine location: Sun on Ascendant/MC.",
                ),
                explanation=(
                    "A Sun conjunct the Ascendant or Midheaven gives presence, "
                    "magnetism and impact — one of the very important great spots."
                ),
                tags=("relocation", "sun"),
            )
        )

    # R3 — any place on the Sun line is excellent.
    if get_rule("SUN-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="SUN-003",
                rule_version="1.0",
                rule_name="On The Sun Line Is Excellent",
                source_text=(
                    "Being on one's Sun line (conjunction line) even when not exactly "
                    "angular on Asc/MC is fantastic — 'you're on your sun line'."
                ),
                priority=2,
                category="sun_angular",
                conditions=(
                    Condition(
                        "relocation.planet.sun.line_in_orb",
                        "==",
                        True,
                        "The Sun line is in orb at the location.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.sun.line_active": "true"},
                    description="The Sun line is in orb and strongly favourable.",
                ),
                explanation=(
                    "On the Sun line, self-expression and impact are strong regardless "
                    "of the exact axis."
                ),
                tags=("relocation", "sun"),
            )
        )

    # R2 — Sun trine/sextile an angular cusp is also excellent.
    if get_rule("SUN-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="SUN-002",
                rule_version="1.0",
                rule_name="Sun Trine/Sextile Angle",
                source_text=(
                    "Sun trine or sextile the Ascendant, MC, IC or Descendant (e.g. "
                    "Sun trine MC = sextile IC) is favourable but weaker than a "
                    "conjunction; still excellent."
                ),
                priority=3,
                category="sun_angular",
                conditions=(
                    Condition(
                        "relocation.planet.sun.trine_sextile_angle",
                        "==",
                        True,
                        "The Sun is in trine or sextile to an angle.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.sun.harmonic.active": "true"},
                    description="Sun trine/sextile to an angle is favourable.",
                ),
                explanation=(
                    "A Sun trine or sextile to an angle supports presence, weaker than "
                    "a conjunction but still excellent."
                ),
                tags=("relocation", "sun"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="sun_angular",
        name="Sun Angular (You Shine)",
        version=1,
        description=(
            "Marks shine locations: Sun conjunct Ascendant/MC (prime), on the Sun "
            "line, or in trine/sextile to an angle."
        ),
        tradition="Western Astrology",
        objective="relocation_sun_angular",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.planet.sun.angular_status",
            "relocation.planet.sun.angular_cusp_orb",
            "relocation.planet.sun.line_in_orb",
            "relocation.planet.sun.axis",
            "relocation.planet.sun.trine_sextile_angle",
        ),
        dependencies=("relocation_engine",),
        rule_refs=(
            TechniqueRuleRef("SUN-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("SUN-003", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("SUN-002", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "a square to an angle does not negate the Sun-line benefit; prioritize "
            "'what really works' over worrying about a square.",
        ),
    )
    register_technique(tech)


init_sun_angular()
