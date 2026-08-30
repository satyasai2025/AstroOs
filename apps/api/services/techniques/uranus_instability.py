"""
AstroOS — Technique Fixture: Uranus / Excitement-and-Instability Zones

Flags locations where a strong Uranus (or the Saturn-Uranus midpoint)
influence on an angle tends to produce upsets, surprises and instability
for most people. A risk modifier for avoiding or preparing for problem
areas, not an absolute prohibition.

Source: RAG technique 07-uranus-instability.md ("Relocational Astrology:
How to Pick a Place").

Purely declarative rules over RelocationEngine facts (Uranus angular
status, angular-cusp orb, Saturn-Uranus midpoint orbs).
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
    "Relocation & Vedic Astrology — Technique 07 (Uranus Instability Zones), "
    "after 'Relocational Astrology: How to Pick a Place'"
)


def init_uranus_instability() -> None:
    if get_technique("uranus_instability", 1) is not None:
        return

    # R1 — Uranus on an angular cusp = problem area.
    if get_rule("URANUS-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="URANUS-001",
                rule_version="1.0",
                rule_name="Uranus Angular Flag",
                source_text=(
                    "Uranus angular (on Asc, MC, IC, Desc) in the relocated chart "
                    "flags the location as an excitement/instability zone: upsets, "
                    "surprises, things not stabilizing."
                ),
                priority=1,
                category="uranus_instability",
                conditions=(
                    Condition(
                        "relocation.planet.uranus.angular_status",
                        "==",
                        "angular",
                        "Uranus is angular in the relocated chart.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.risk.uranus": "excitement_instability"},
                    description="Uranus angular: excitement/instability zone.",
                ),
                explanation=(
                    "Angular Uranus tends to produce upsets, surprises and "
                    "non-stabilizing conditions for most people."
                ),
                tags=("relocation", "risk"),
            )
        )

    # R2 — Saturn-Uranus midpoint on an angle is also problematic.
    if get_rule("URANUS-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="URANUS-002",
                rule_version="1.0",
                rule_name="Saturn-Uranus Midpoint Flag",
                source_text=(
                    "The Saturn-Uranus midpoint on an angular cusp flags the location "
                    "similarly to Uranus angular."
                ),
                priority=2,
                category="uranus_instability",
                conditions=(
                    Condition(
                        "relocation.midpoint.saturn_uranus.in_orb",
                        "==",
                        True,
                        "Saturn-Uranus midpoint is in orb of the ASC/MC.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.risk.saturn_uranus_midpoint": "active"},
                    description="Saturn-Uranus midpoint on the angle.",
                ),
                explanation=(
                    "A Saturn-Uranus midpoint conjunct an angle carries the same "
                    "unstable-excitement tendency as Uranus angular."
                ),
                tags=("relocation", "risk"),
            )
        )

    # R3 — not an absolute prohibition (softening).
    if get_rule("URANUS-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="URANUS-003",
                rule_version="1.0",
                rule_name="Soft Warning Not A Prohibition",
                source_text=(
                    "A Uranian area that is otherwise very good, or which the person "
                    "says won't bother them, is a soft warning, not a hard no — though "
                    "people often discover it bothers them after all."
                ),
                priority=3,
                category="uranus_instability",
                conditions=(
                    Condition(
                        "relocation.preference.unpredictability",
                        "==",
                        True,
                        "The person explicitly welcomes unpredictability.",
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.risk.uranus.softened": "true"},
                    description="Uranus risk is softened by personal preference.",
                ),
                explanation=(
                    "If the person's goal is excitement/change, the avoid reading is "
                    "softened; most people still find it uncomfortable."
                ),
                tags=("relocation", "risk"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="uranus_instability",
        name="Uranus / Excitement-and-Instability Zones",
        version=1,
        description=(
            "Risk-screens locations for angular Uranus or a Saturn-Uranus midpoint "
            "on the angles, flagging possible upsets and instability as a soft warning."
        ),
        tradition="Western Astrology",
        objective="relocation_risk",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.planet.uranus.angular_status",
            "relocation.planet.uranus.angular_cusp_orb",
            "relocation.midpoint.saturn_uranus.in_orb",
        ),
        dependencies=("relocation_engine",),
        rule_refs=(
            TechniqueRuleRef("URANUS-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("URANUS-002", "1.0", RuleRole.SUPPORTING, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("URANUS-003", "1.0", RuleRole.EXCEPTION, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "applies to relocated/angular Uranus only, not natal Uranus.",
        ),
    )
    register_technique(tech)


init_uranus_instability()
