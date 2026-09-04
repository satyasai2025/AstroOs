"""
AstroOS — Technique Fixture: Harmonic Interpretation (5th / 7th / 9th)

Interprets map-line labels by harmonic family: 9th-harmonic (comfort),
5th-harmonic (creative/playful), 7th-harmonic (discipline/training). The
format is exclusive — a label belongs to exactly one family.

Source: RAG technique 12-harmonic-interpretation.md ("Relocational
Astrology: How to Pick a Place").

Purely declarative rules over RelocationEngine angle harmonic-family
facts (`relocation.ascendant.harmonic_family` / `.midheaven.harmonic_family`).
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
    "Relocation & Vedic Astrology — Technique 12 (Harmonic Interpretation), "
    "after 'Relocational Astrology: How to Pick a Place'"
)


def init_harmonic_interpretation() -> None:
    if get_technique("harmonic_interpretation", 1) is not None:
        return

    # R1 — round-number labels (multiples of 10) = 9th harmonic = comfort.
    if get_rule("HARM-001") is None:
        register_rule(
            RuleDefinition(
                rule_id="HARM-001",
                rule_version="1.0",
                rule_name="Round Label = 9th Harmonic Comfort",
                source_text=(
                    "A line label that is a multiple of 10 (10, 20, 30, 40...), e.g. "
                    "140°, is a 9th-harmonic comfort-zone signal."
                ),
                priority=1,
                category="harmonic_interpretation",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition(
                                "relocation.ascendant.harmonic_family",
                                "==",
                                "ninth",
                                "The Ascendant label is 9th harmonic.",
                            ),
                            Condition(
                                "relocation.midheaven.harmonic_family",
                                "==",
                                "ninth",
                                "The Midheaven label is 9th harmonic.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.harmonic.ninth.comfort": "true"},
                    description="9th-harmonic comfort signal at the location.",
                ),
                explanation=(
                    "Round multiples of 10 correspond to the 9th harmonic — a comfort "
                    "zone for the person."
                ),
                tags=("relocation", "harmonic"),
            )
        )

    # R2 — 72 / 108 / 144 = 5th harmonic = creative, playful.
    if get_rule("HARM-002") is None:
        register_rule(
            RuleDefinition(
                rule_id="HARM-002",
                rule_version="1.0",
                rule_name="72/108/144 = 5th Harmonic Creative",
                source_text=(
                    "A line label of 72, 108, or 144 (5th harmonic) is creative and "
                    "playful; relevant for artistic people."
                ),
                priority=1,
                category="harmonic_interpretation",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition(
                                "relocation.ascendant.harmonic_family",
                                "==",
                                "fifth",
                                "The Ascendant label is 5th harmonic.",
                            ),
                            Condition(
                                "relocation.midheaven.harmonic_family",
                                "==",
                                "fifth",
                                "The Midheaven label is 5th harmonic.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.harmonic.fifth.creative": "true"},
                    description="5th-harmonic creative/playful signal.",
                ),
                explanation=(
                    "72/108/144 labels are the 5th harmonic — creative and playful "
                    "energy, good for artistic people."
                ),
                tags=("relocation", "harmonic"),
            )
        )

    # R3 — labels with minutes = 7th harmonic = discipline, training.
    if get_rule("HARM-003") is None:
        register_rule(
            RuleDefinition(
                rule_id="HARM-003",
                rule_version="1.0",
                rule_name="Minute Label = 7th Harmonic Discipline",
                source_text=(
                    "A line label with a minutes component (e.g. 128°34') is the 7th "
                    "harmonic — discipline/training; good for military, sports "
                    "champions, perfection work."
                ),
                priority=1,
                category="harmonic_interpretation",
                conditions=(
                    ConditionGroup(
                        operator="OR",
                        conditions=(
                            Condition(
                                "relocation.ascendant.harmonic_family",
                                "==",
                                "seventh",
                                "The Ascendant label is 7th harmonic.",
                            ),
                            Condition(
                                "relocation.midheaven.harmonic_family",
                                "==",
                                "seventh",
                                "The Midheaven label is 7th harmonic.",
                            ),
                        ),
                    ),
                ),
                conclusion=Conclusion(
                    derived_facts={"relocation.harmonic.seventh.discipline": "true"},
                    description="7th-harmonic discipline/training signal.",
                ),
                explanation=(
                    "Labels with a minutes component are the 7th harmonic — good for "
                    "discipline, training and perfection work."
                ),
                tags=("relocation", "harmonic"),
            )
        )

    tech = TechniqueDefinition(
        technique_id="harmonic_interpretation",
        name="Harmonic Interpretation (5th / 7th / 9th)",
        version=1,
        description=(
            "Classifies a line label into its exclusive harmonic family: 9th "
            "(comfort), 5th (creative/playful), or 7th (discipline/training)."
        ),
        tradition="Western Astrology",
        objective="relocation_harmonic",
        source_references=(_SOURCE,),
        required_inputs=(
            "relocation.ascendant.harmonic_family",
            "relocation.midheaven.harmonic_family",
            "relocation.ascendant.label",
            "relocation.midheaven.label",
        ),
        dependencies=("relocation_engine",),
        rule_refs=(
            TechniqueRuleRef("HARM-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("HARM-002", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("HARM-003", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
        ),
        provenance=ProvenanceStatus.SOURCE_DERIVED,
        status="research",
        unresolved_inconsistencies=(
            "label format is exclusive: no two harmonic rules apply to the same "
            "label; higher harmonics beyond 9th are not used.",
        ),
    )
    register_technique(tech)


init_harmonic_interpretation()
