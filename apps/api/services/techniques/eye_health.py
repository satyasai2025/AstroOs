"""
AstroOS — First Technique Fixture: Ocular Health (Astro-EyeHealth)

The FIRST imported technique, now reconciled against the ACTUAL source PDF
("Medical Astrology Technique for Ocular Health, Retinal Disorders, and
Hereditary Vision Impairment"). It contains no framework logic — only data:
rules (into the code rule_registry) and a TechniqueDefinition (into the
technique_registry). The next technique is a sibling file exactly like this.

──────────────────────────────────────────────────────────────────────────────
SOURCE FIDELITY — this fixture follows SECTION A of the PDF (the extraction
table, EYE-001..EYE-008), verbatim in `source_text`.

KNOWN SOURCE INCONSISTENCY (preserved, NOT auto-resolved — see the framework
rule): the PDF's Section A and Section B disagree on rule numbering/membership:
  • Section A lists EYE-001..EYE-008.
  • Section B (the "AstroOS-ready skill" rule set) lists only EYE-001..EYE-006:
      - it OMITS Section A's EYE-005 (sibling lineage),
      - it RENUMBERS A's EYE-006 (D12 genetic confirmation) -> B's EYE-005,
        and A's EYE-007 (Jupiter mitigating grace) -> B's EYE-006,
      - it drops A's EYE-008 from the rule set (only mentioned under severity).
  This fixture keeps Section A's numbering AND retains the omitted sibling rule.
  EYE-008 is explicitly DERIVED in the source and stays DERIVED here.

EVALUABILITY — the source's connection/aspect/dispositorship checks and its
divisional-chart (D3/D9/D12) checks require Facts that FactBuilder does not yet
emit. Per the framework's "never infer missing data" rule (and the PDF's own
"Missing-data behavior"), those rules reference explicit not-yet-computed Fact
keys so the engine returns INSUFFICIENT_DATA rather than fabricating a result.
Only the sub-conditions expressible with today's Facts are encoded as evaluable.

SAFETY — the source uses medical language ("complete blindness", "absolute
cancellation", "genetically inherited"). That language is preserved ONLY as
`source_text`/provenance; the machine result uses neutral, symbolic derived
facts. This is astrological indication, not medical diagnosis.
──────────────────────────────────────────────────────────────────────────────
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
from apps.api.services.technique_registry import register_technique

_SOURCE = "Astro-EyeHealth PDF, Section A (extraction table), EYE-001..EYE-008"

# Fact keys the source needs but FactBuilder does not yet emit. Referencing them
# makes the dependent rules return INSUFFICIENT_DATA (honest missing data), never
# a fabricated match. Documented here so the gap is explicit, not hidden.
_PENDING_FACTS = (
    "connection.sun_with_2nd_and_9th",   # EYE-003 paternal lineage connection
    "connection.sun_with_2nd_and_4th",   # EYE-004 maternal lineage connection
    "connection.sun_with_2nd_and_3rd",   # EYE-005 sibling lineage connection
    "d12.lineage_lord_in_2nd_or_12th",   # EYE-006 D12 genetic confirmation
    "aspect.jupiter_grace_on_eye_indicators",  # EYE-007 mitigating grace
    "eye.multichart_affliction_no_jupiter",    # EYE-008 severe outcome (DERIVED)
)


def _register(rule: RuleDefinition) -> None:
    """Idempotent register: fixtures/tests may import more than once."""
    if get_rule(rule.rule_id) is None:
        register_rule(rule)


# ── EYE-001 — Primary Eye Affliction (SOURCE) ─────────────────────────────────
# Source: "Sun or Moon in 8th/12th house, or debilitated, or conjunct
# Rahu/Ketu/malefics; OR 2nd/12th lord debilitated/retrograde." Only the
# luminary placement/debilitation portion is expressible today; the
# Rahu/Ketu-conjunction and 2nd/12th-lord-affliction branches are omitted from
# the evaluable conditions (documented) pending FactBuilder support.
_register(RuleDefinition(
    rule_id="EYE-001",
    rule_version="1.0",
    rule_name="Primary Eye Affliction",
    source_text=(
        "Sun or Moon in 8th/12th house, or debilitated, or conjunct "
        "Rahu/Ketu/malefics; OR 2nd/12th lord debilitated/retrograde. "
        "(Evaluable portion: luminary in 8th/12th or debilitated.)"
    ),
    priority=8,
    category="ocular_health",
    conditions=(
        ConditionGroup(operator="OR", conditions=(
            Condition("planet.sun.house", "in", (8, 12), "Sun in 8th/12th"),
            Condition("planet.moon.house", "in", (8, 12), "Moon in 8th/12th"),
            Condition("planet.sun.debilitated", "==", True, "Sun debilitated"),
            Condition("planet.moon.debilitated", "==", True, "Moon debilitated"),
        )),
    ),
    conclusion=Conclusion(
        derived_facts={"ocular_health.primary_affliction": "indicated"},
        description="Natal promise for vision impairment / progressive eye disease.",
    ),
    explanation="A luminary (Sun=right eye, Moon=left eye) afflicted by dusthana placement or debilitation is the primary ocular-affliction indication.",
    tags=("eye", "luminary", "primary"),
))

# ── EYE-002 — Retinal Affliction (SOURCE) ─────────────────────────────────────
# Source: "Venus afflicted by Mars, placed in Scorpio/enemy signs, or under
# Rahu-Ketu axis." Evaluable: Venus debilitated, or Venus in Scorpio. The
# Mars-conjunction / Rahu-Ketu-axis branches await conjunction facts.
_register(RuleDefinition(
    rule_id="EYE-002",
    rule_version="1.0",
    rule_name="Retinal Affliction",
    source_text=(
        "Venus afflicted by Mars, placed in Scorpio/enemy signs, or under the "
        "Rahu-Ketu axis. (Evaluable portion: Venus debilitated or in Scorpio.)"
    ),
    priority=7,
    category="ocular_health",
    conditions=(
        ConditionGroup(operator="OR", conditions=(
            Condition("planet.venus.debilitated", "==", True, "Venus debilitated"),
            Condition("planet.venus.rashi", "==", "scorpio", "Venus in Scorpio"),
        )),
    ),
    conclusion=Conclusion(
        derived_facts={"ocular_health.retinal_affliction": "indicated"},
        description="Retinal weakness / progressive retinal deterioration.",
    ),
    explanation="An afflicted Venus (natural karaka of retina quality) indicates retinal involvement.",
    tags=("eye", "venus", "retina"),
))

# ── EYE-003 — Paternal Eye Loss Connection (SOURCE; needs connection facts) ────
_register(RuleDefinition(
    rule_id="EYE-003",
    rule_version="1.0",
    rule_name="Paternal Eye Loss Connection",
    source_text="Sun forms a direct connection (conjunction/aspect/dispositorship) with the 2nd Lord AND the 9th Lord/House.",
    priority=6,
    category="ocular_health",
    conditions=(
        Condition("connection.sun_with_2nd_and_9th", "==", True,
                  "Sun connects 2nd Lord and 9th Lord/House"),
    ),
    conclusion=Conclusion(
        derived_facts={"ocular_health.paternal_lineage": "indicated"},
        description="Paternal side suffers severe eye illness or blindness.",
    ),
    explanation="Links the eye significators to the paternal lineage lord (9th).",
    tags=("eye", "lineage", "paternal"),
))

# ── EYE-004 — Maternal Eye Loss Connection (SOURCE; needs connection facts) ────
_register(RuleDefinition(
    rule_id="EYE-004",
    rule_version="1.0",
    rule_name="Maternal Eye Loss Connection",
    source_text="Sun forms a direct connection with the 2nd Lord AND the 4th Lord/House.",
    priority=6,
    category="ocular_health",
    conditions=(
        Condition("connection.sun_with_2nd_and_4th", "==", True,
                  "Sun connects 2nd Lord and 4th Lord/House"),
    ),
    conclusion=Conclusion(
        derived_facts={"ocular_health.maternal_lineage": "indicated"},
        description="Maternal side suffers severe eye illness or blindness.",
    ),
    explanation="Links the eye significators to the maternal lineage lord (4th).",
    tags=("eye", "lineage", "maternal"),
))

# ── EYE-005 — Sibling Eye Loss Connection (SOURCE) ────────────────────────────
# This is the rule Section B OMITS. Retained here from Section A; the omission
# is recorded in unresolved_inconsistencies rather than silently resolved.
_register(RuleDefinition(
    rule_id="EYE-005",
    rule_version="1.0",
    rule_name="Sibling Eye Loss Connection",
    source_text="Sun forms a direct connection with the 2nd Lord AND the 3rd Lord/House. (NOTE: omitted from the PDF's Section B rule set; retained from Section A.)",
    priority=6,
    category="ocular_health",
    conditions=(
        Condition("connection.sun_with_2nd_and_3rd", "==", True,
                  "Sun connects 2nd Lord and 3rd Lord/House"),
    ),
    conclusion=Conclusion(
        derived_facts={"ocular_health.sibling_lineage": "indicated"},
        description="Sibling suffers severe eye illness or vision loss.",
    ),
    explanation="Links the eye significators to the sibling lineage lord (3rd).",
    tags=("eye", "lineage", "sibling"),
))

# ── EYE-006 — Genetic Inheritance Confirmation (SOURCE; needs D12 facts) ───────
_register(RuleDefinition(
    rule_id="EYE-006",
    rule_version="1.0",
    rule_name="Genetic Inheritance Confirmation",
    source_text="In Dwadasamsha (D12), the 9th Lord (paternal) or 4th Lord (maternal) is placed in the 2nd/12th house or connects with eye indicators (Sun/Moon/12th Lord).",
    priority=5,
    category="ocular_health",
    conditions=(
        Condition("d12.lineage_lord_in_2nd_or_12th", "==", True,
                  "D12 lineage lord in 2nd/12th or connecting eye indicators"),
    ),
    conclusion=Conclusion(
        derived_facts={"ocular_health.hereditary_confirmed": "indicated"},
        description="Confirms the eye condition is inherited through that family line.",
    ),
    explanation="D12 cross-verification of hereditary transmission.",
    tags=("eye", "hereditary", "d12"),
))

# ── EYE-007 — Mitigating Grace vs Complete Blindness (SOURCE; exception) ───────
# The PDF frames this as a cancellation ("Complete blindness is CANCELLED").
_register(RuleDefinition(
    rule_id="EYE-007",
    rule_version="1.0",
    rule_name="Mitigating Grace vs Complete Blindness",
    source_text="Jupiter casts a benefic aspect onto afflicted Sun, Moon, or 2nd/12th lords in D1, D9, D3, or D12. THEN complete blindness is cancelled; condition is manageable/treatable. Exception: if Jupiter itself is severely afflicted/debilitated, mitigation strength is reduced.",
    priority=5,
    category="ocular_health",
    conditions=(
        Condition("aspect.jupiter_grace_on_eye_indicators", "==", True,
                  "Jupiter benefic aspect on afflicted eye indicators"),
    ),
    conclusion=Conclusion(
        derived_facts={"ocular_health.mitigation": "jupiter_grace"},
        description="Mitigates severity; prevents complete blindness (source terminology).",
    ),
    explanation="Benefic Jupiter aspect on afflicted eye significators mitigates severity.",
    tags=("eye", "jupiter", "mitigation", "cancellation"),
))

# ── EYE-008 — Irreversible Complete Blindness (DERIVED — stays DERIVED) ────────
# Explicitly DERIVED in the source; never presented as a classical fact.
_register(RuleDefinition(
    rule_id="EYE-008",
    rule_version="1.0",
    rule_name="Severe Multi-Chart Affliction (DERIVED)",
    source_text="DERIVED: Extreme multi-chart afflictions to Sun, Moon, 2nd, 12th, and Venus across D1, D9, D3, D12 with total absence of Jupiter/benefic grace. (Source marks this rule DERIVED, and it is absent from the Section B rule set.)",
    priority=3,
    category="ocular_health",
    conditions=(
        Condition("eye.multichart_affliction_no_jupiter", "==", True,
                  "Extreme multi-chart affliction with no Jupiter grace"),
    ),
    conclusion=Conclusion(
        derived_facts={"ocular_health.severe_outcome": "indicated"},
        description="DERIVED severe-outcome indication (source: 'irreversible complete blindness').",
    ),
    explanation="DERIVED composite of multi-chart affliction with absent benefic grace; labelled DERIVED throughout.",
    tags=("eye", "derived", "severe"),
))


# ── The technique definition ──────────────────────────────────────────────────

EYE_HEALTH_TECHNIQUE = TechniqueDefinition(
    technique_id="eye_health",
    name="Ocular Health & Hereditary Vision Analysis",
    version=1,
    description=(
        "Astro-EyeHealth (Parashari / Medical branch): natal promise for eye "
        "disease, retinal affliction, hereditary transmission of vision loss, "
        "severity, and timing. Symbolic/astrological evidence only — not a "
        "medical diagnosis."
    ),
    tradition="Parashari",
    objective="ocular_health",
    source_references=(_SOURCE,),
    required_inputs=(
        # Evaluable today:
        "planet.sun.house", "planet.moon.house",
        "planet.sun.debilitated", "planet.moon.debilitated",
        "planet.venus.debilitated", "planet.venus.rashi",
        # Required by the source but not yet emitted by FactBuilder:
        *_PENDING_FACTS,
    ),
    dependencies=("D1", "D9", "D3", "D12", "dasha", "transit"),
    rule_refs=(
        TechniqueRuleRef("EYE-001", "1.0", RuleRole.PRIMARY,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("EYE-002", "1.0", RuleRole.PRIMARY,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("EYE-003", "1.0", RuleRole.PRIMARY,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("EYE-004", "1.0", RuleRole.PRIMARY,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("EYE-005", "1.0", RuleRole.PRIMARY,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("EYE-006", "1.0", RuleRole.SUPPORTING,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("EYE-007", "1.0", RuleRole.EXCEPTION,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("EYE-008", "1.0", RuleRole.SUPPORTING,
                         ProvenanceStatus.DERIVED, source_reference="DERIVED (source-marked)"),
    ),
    provenance=ProvenanceStatus.UNTESTED,
    status="research",
    unresolved_inconsistencies=(
        "Section A lists EYE-001..EYE-008; Section B (AstroOS-ready rule set) "
        "lists only EYE-001..EYE-006 and OMITS Section A's EYE-005 (sibling "
        "lineage). The omission is preserved, not resolved: EYE-005 is retained "
        "here from Section A.",
        "Section B renumbers: Section A's EYE-006 (D12 genetic confirmation) -> "
        "Section B EYE-005, and Section A's EYE-007 (Jupiter mitigating grace) "
        "-> Section B EYE-006. This fixture keeps Section A's numbering.",
        "Section A's EYE-008 is marked DERIVED and does not appear in Section "
        "B's rule set (only under severity classification). Retained here as "
        "DERIVED.",
        "EYE-003..EYE-008 require connection/aspect/dispositorship and D3/D9/D12 "
        "divisional Facts that FactBuilder does not yet emit; they report "
        "INSUFFICIENT_DATA rather than being fabricated (matches the source's "
        "own Missing-data behavior).",
    ),
)

register_technique(EYE_HEALTH_TECHNIQUE)
