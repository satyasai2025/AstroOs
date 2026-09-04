"""
AstroOS — Clinical Oncology, Genetic Mutations & Surgical Resilience Technique
=============================================================================
Implementation of contemporary clinical medical astrology principles covering:
  - Neurofibromatosis & Genetic Nerve Mutations (Afflicted Mercury + Ketu)
  - Cellular Proliferation, Tumors & Malignancies (Rahu-Jupiter Axis & Functional Malefics)
  - High BAV Exalted Mars: Pain Threshold, Immune Resilience & Yuddha Jeevana
  - 3rd-8th House Parivartana: Lifelong Physical Struggle against Chronic Illness
  - Shoola Yoga & Dusthana Afflictions: Karmic Hospitalization
  - Ayudha Drekkana (Surgical Cuts) vs Sarpa Drekkana (Metastatic Spread)
  - D30 Trishamsha Tissue Malignancy (Venus-Jupiter-Rahu Afflictions)
  - Saham Crisis Points (Roga, Mrityu, Punyakarma in 8th)
  - Dasha Trajectory: Rahu-Jupiter Escalation vs Rahu-Saturn Fortified Defense
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

_SOURCE = "Clinical Oncology & Medical Genetics Astrological Guidelines (Contemporary Practitioner Synthesis)"

_PENDING_FACTS = (
    "yoga.shoola_yoga_with_dusthana",           # MED-YOGA-005: Planets in 3 signs connected to 8th/12th
    "drekkana.multiple_in_ayudha_drekkana",      # MED-DREK-006A: Moon, Mars, Saturn, Jupiter in Ayudha Drekkana
    "drekkana.in_sarpa_drekkana_6th_or_10th",   # MED-DREK-006B: Sarpa Drekkana creeping spread
    "d30.venus_jupiter_rahu_tissue_affliction",  # MED-D30-007: D30 tissue-level cellular mutation
    "saham.mrityu_saham_afflicted_mercury_guru", # MED-SAHAM-008: Mrityu Saham with weak Mercury/Jupiter
    "sudarshana.tri_lagna_8th_12th_affliction",  # Sudarshana tri-lagna structural support failure
)


def _register(rule: RuleDefinition) -> None:
    """Idempotent register for technique rules."""
    if get_rule(rule.rule_id) is None:
        register_rule(rule)


# ── MED-ONCO-001 — Rahu-Jupiter Axis: Cellular Proliferation & Malignancy ────
_register(RuleDefinition(
    rule_id="MED-ONCO-001",
    rule_version="1.0",
    rule_name="Rahu-Jupiter Axis Malignancy & Tumor Proliferation",
    source_text=(
        "The combination, conjunction, or mutual aspect of Rahu (agent of cellular mutation, "
        "cancer, and metastasis) and Jupiter (expansion/growths, functional malefic for Makara) "
        "acts as the primary planetary driver for tumors, abnormal cellular growth, and malignancy."
    ),
    priority=9,
    category="medical_oncology",
    conditions=(
        ConditionGroup(operator="OR", conditions=(
            Condition("aspect.rahu_jupiter_axis", "==", True, "Rahu-Jupiter mutual aspect or conjunction"),
            ConditionGroup(operator="AND", conditions=(
                Condition("planet.rahu.house", "in", (6, 8, 12), "Rahu in dusthana (6/8/12)"),
                Condition("planet.jupiter.house", "in", (6, 8, 12), "Jupiter in dusthana (6/8/12)"),
            )),
            Condition("planet.rahu.house", "==", 12, "Rahu in 12th (oncology hospitalization/advanced clinical therapies)"),
        )),
    ),
    conclusion=Conclusion(
        derived_facts={"medical.tumor_malignancy_risk": "indicated"},
        description="High vulnerability for abnormal cellular proliferation, tumors, and malignancy.",
    ),
    explanation="Rahu provides the mutagenic catalyst while Jupiter provides unchecked cellular expansion.",
    tags=("oncology", "cancer", "rahu", "jupiter", "tumors"),
))

# ── MED-GEN-002 — Debilitated Mercury & Ketu: Genetic Nerve Mutation ──────────
_register(RuleDefinition(
    rule_id="MED-GEN-002",
    rule_version="1.0",
    rule_name="Genetic Nerve Mutation & Peripheral Nerve Sheath Vulnerability",
    source_text=(
        "Mercury rules the central and peripheral nervous system. When debilitated (Pisces/3rd house) "
        "with low strength, combined with Ketu (rare/genetic abnormalities, debilitated in 6th house), "
        "it directly indicates genetic nerve disorders (Neurofibromatosis, nerve sheath tumors)."
    ),
    priority=8,
    category="medical_genetics",
    conditions=(
        ConditionGroup(operator="OR", conditions=(
            ConditionGroup(operator="AND", conditions=(
                Condition("planet.mercury.debilitated", "==", True, "Mercury debilitated"),
                Condition("planet.ketu.house", "in", (3, 6, 8), "Ketu in 3rd/6th/8th house"),
            )),
            ConditionGroup(operator="AND", conditions=(
                Condition("planet.mercury.rashi", "==", "pisces", "Mercury in Pisces (Meena)"),
                Condition("planet.mercury.house", "==", 3, "Mercury in 3rd house"),
            )),
        )),
    ),
    conclusion=Conclusion(
        derived_facts={"medical.genetic_nerve_mutation": "indicated"},
        description="Vulnerability for genetic nerve mutations, neurofibromatosis, and peripheral nerve disorders.",
    ),
    explanation="Debilitated Mercury weakens neural architecture, and Ketu introduces anomalous genetic mutations.",
    tags=("genetics", "mercury", "ketu", "nerves", "neurofibromatosis"),
))

# ── MED-SURG-003 — Exalted Mars 8/8 BAV: Surgical Resilience & Yuddha Jeevana ──
_register(RuleDefinition(
    rule_id="MED-SURG-003",
    rule_version="1.0",
    rule_name="Exalted Mars 8/8 BAV: Pain Threshold & Treatment Survival",
    source_text=(
        "Mars represents physical constitution, fire element, blood, pain threshold, and surgical intervention. "
        "When Mars is exalted in Lagna with maximum Bhinnashtakavarga strength (8/8 bindus), it confers extraordinary "
        "pain tolerance, intense physical fighting spirit (Yuddha Jeevana), and survival through aggressive clinical therapies."
    ),
    priority=8,
    category="medical_resilience",
    conditions=(
        ConditionGroup(operator="AND", conditions=(
            Condition("planet.mars.exalted", "==", True, "Mars exalted (Capricorn/Makara)"),
            Condition("planet.mars.house", "==", 1, "Mars in 1st house (Lagna)"),
        )),
    ),
    conclusion=Conclusion(
        derived_facts={"medical.surgical_resilience": "exceptional", "medical.pain_tolerance": "high"},
        description="Exceptional physical constitution, extraordinary pain threshold, and resilience through invasive therapies.",
    ),
    explanation="Exalted Mars in Lagna turns the physical body into a fortress of endurance, granting survival through severe trials.",
    tags=("mars", "lagna", "resilience", "surgery", "vitality"),
))

# ── MED-HOUSE-004 — 3rd-8th House Parivartana: Lifelong Physical Battle ──────
_register(RuleDefinition(
    rule_id="MED-HOUSE-004",
    rule_version="1.0",
    rule_name="3rd-8th House Parivartana: Chronic Physical Struggle",
    source_text=(
        "3rd House represents physical effort, active fighting back, and stamina. 8th House represents chronic illness, "
        "deep suffering, and major surgeries. A mutual exchange (Parivartana) between 3rd and 8th lords indicates that life "
        "becomes a continuous, lifelong physical struggle against chronic, severe medical conditions."
    ),
    priority=7,
    category="medical_chronicity",
    conditions=(
        Condition("yoga.parivartana_3rd_8th", "==", True, "Parivartana between 3rd and 8th house lords"),
    ),
    conclusion=Conclusion(
        derived_facts={"medical.chronic_battle": "lifelong_effort"},
        description="Lifelong physical fight and effort against deep-seated chronic medical conditions.",
    ),
    explanation="The exchange links the house of courage and physical effort (3rd) with the house of chronic vulnerability (8th).",
    tags=("parivartana", "3rd_house", "8th_house", "chronic", "endurance"),
))

# ── MED-YOGA-005 — Shoola Yoga & Karmic Hospitalization ────────────────────────
_register(RuleDefinition(
    rule_id="MED-YOGA-005",
    rule_version="1.0",
    rule_name="Shoola Yoga: Severe Karmic Physical Trial & Hospitalization",
    source_text=(
        "Shoola Yoga (planets clustered in only 3 signs) connected to the 8th or 12th lord acts as a severe "
        "karmic affliction leading to intensive medical intervention, physical suffering, and prolonged hospitalization."
    ),
    priority=7,
    category="medical_karma",
    conditions=(
        Condition("yoga.shoola_yoga_with_dusthana", "==", True, "Shoola Yoga connected to 8th/12th lords"),
    ),
    conclusion=Conclusion(
        derived_facts={"medical.karmic_hospitalization": "indicated"},
        description="Karmic physical affliction with severe trials and prolonged clinical hospitalization.",
    ),
    explanation="Clustering in 3 signs limits balance, and 8th/12th involvement concentrates stress on bodily integrity.",
    tags=("shoola_yoga", "karma", "hospitalization", "dusthana"),
))

# ── MED-DREK-006 — Ayudha vs Sarpa Drekkana: Surgical Cuts vs Metastasis ───────
_register(RuleDefinition(
    rule_id="MED-DREK-006",
    rule_version="1.0",
    rule_name="Drekkana Modifiers: Ayudha (Invasive Surgery) & Sarpa (Metastatic Spread)",
    source_text=(
        "Ayudha Drekkana (Moon, Mars, Saturn, Jupiter) signifies invasive surgeries, cutting-edge clinical oncology, "
        "and medical cuts. Sarpa Drekkana (planets in 6th/10th) causes disease to creep silently like a serpent, "
        "manifesting as recurrence and distant metastasis."
    ),
    priority=6,
    category="medical_varga",
    conditions=(
        ConditionGroup(operator="OR", conditions=(
            Condition("drekkana.multiple_in_ayudha_drekkana", "==", True, "Multiple planets in Ayudha Drekkana"),
            Condition("drekkana.in_sarpa_drekkana_6th_or_10th", "==", True, "Planets in Sarpa Drekkana in 6th/10th house"),
        )),
    ),
    conclusion=Conclusion(
        derived_facts={"medical.drekkana_clinical_signature": "active"},
        description="Drekkana clinical signature: Ayudha indicates surgical interventions; Sarpa indicates insidious spread/metastasis.",
    ),
    explanation="D3 Drekkana decanates reveal the physical manifestation modality (surgical cutting vs insidious spreading).",
    tags=("drekkana", "d3", "surgery", "metastasis", "sarpa"),
))

# ── MED-D30-007 — D30 Trimshamsha: Tissue Malignancy (Venus-Jupiter-Rahu) ─────
_register(RuleDefinition(
    rule_id="MED-D30-007",
    rule_version="1.0",
    rule_name="D30 Trimshamsha: Deep Cellular & Tissue Malignancy",
    source_text=(
        "D30 (Trimshamsha) diagnoses deep structural weaknesses, genetic susceptibility, and tissue afflictions. "
        "Venus rules bodily tissues (dhatus); affliction to Venus, Jupiter, and Rahu in D30 highlights tissue-level "
        "malignancies and deep cellular mutations."
    ),
    priority=6,
    category="medical_varga",
    conditions=(
        Condition("d30.venus_jupiter_rahu_tissue_affliction", "==", True, "D30 Venus-Jupiter-Rahu affliction"),
    ),
    conclusion=Conclusion(
        derived_facts={"medical.d30_tissue_malignancy": "confirmed"},
        description="D30 confirms cellular mutation and tissue-level malignancy vulnerability.",
    ),
    explanation="Trimshamsha reveals karmic and tissue-level vulnerabilities not obvious in D1.",
    tags=("d30", "trimshamsha", "tissue", "cellular", "malignancy"),
))

# ── MED-SAHAM-008 — Sahams: Roga & Mrityu Crisis Activation ───────────────────
_register(RuleDefinition(
    rule_id="MED-SAHAM-008",
    rule_version="1.0",
    rule_name="Sensitive Points: Roga & Mrityu Saham Affliction",
    source_text=(
        "Roga Saham shows the root cause of physical illness. Mrityu Saham associated with weak Mercury/Jupiter "
        "highlights acute clinical crises. Punyakarma Saham in the 8th house indicates past-life karmic burdens "
        "manifesting as chronic physical endurance rather than sudden fatal outcomes."
    ),
    priority=5,
    category="medical_sahams",
    conditions=(
        Condition("saham.mrityu_saham_afflicted_mercury_guru", "==", True, "Mrityu Saham afflicted with weak Mercury/Jupiter"),
    ),
    conclusion=Conclusion(
        derived_facts={"medical.saham_crisis_active": "indicated"},
        description="Saham activation indicates acute physical crisis requiring intensive clinical intervention.",
    ),
    explanation="Sensitive Arabic parts (Sahams) pinpoint exact clinical crisis triggers.",
    tags=("sahams", "roga_saham", "mrityu_saham", "crisis"),
))

# ── MED-DASHA-009 — Dasha Trajectory: Rahu-Jupiter vs Rahu-Saturn ─────────────
_register(RuleDefinition(
    rule_id="MED-DASHA-009",
    rule_version="1.0",
    rule_name="Dasha Trajectory: Acute Malignancy vs Fortified Clinical Management",
    source_text=(
        "Rahu-Jupiter Period: High danger for cancer/tumor escalation, rapid disease spread, and acute diagnosis windows. "
        "Rahu-Saturn Period: Transition from acute crisis to structured endurance. Saturn as Lagna lord brings fortified "
        "defenses, clinical discipline, organized long-term treatment, and survival-oriented management."
    ),
    priority=6,
    category="medical_timing",
    conditions=(
        ConditionGroup(operator="OR", conditions=(
            ConditionGroup(operator="AND", conditions=(
                Condition("dasha.active_mahadasha_lord", "==", "Rahu"),
                Condition("dasha.active_antardasha_lord", "==", "Jupiter"),
            )),
            ConditionGroup(operator="AND", conditions=(
                Condition("dasha.active_mahadasha_lord", "==", "Rahu"),
                Condition("dasha.active_antardasha_lord", "==", "Saturn"),
            )),
        )),
    ),
    conclusion=Conclusion(
        derived_facts={"medical.oncology_dasha_trajectory": "active"},
        description="Active oncology timing phase: Rahu-Jupiter indicates rapid escalation/diagnosis; Rahu-Saturn indicates structured clinical endurance.",
    ),
    explanation="Rahu-Jupiter drives unchecked cellular growth, while Rahu-Saturn anchors institutional oncology management.",
    tags=("dasha", "rahu", "jupiter", "saturn", "oncology", "timing"),
))


# ── The technique definition ──────────────────────────────────────────────────

CLINICAL_ONCOLOGY_TECHNIQUE = TechniqueDefinition(
    technique_id="clinical_oncology_genetics",
    name="Clinical Oncology, Genetic Mutations & Surgical Resilience",
    version=1,
    description=(
        "Comprehensive clinical medical astrology technique synthesizing contemporary oncology, "
        "genetic nerve mutations (Neurofibromatosis), surgical endurance (Exalted Mars 8/8 BAV), "
        "D30 Trimshamsha tissue affliction, Ayudha/Sarpa Drekkana modalities, and Dasha trajectories."
    ),
    tradition="Parashari",
    objective="medical_oncology_genetics",
    source_references=(_SOURCE,),
    required_inputs=(
        "planet.rahu.house", "planet.jupiter.house", "aspect.rahu_jupiter_axis",
        "planet.mercury.debilitated", "planet.mercury.rashi", "planet.mercury.house",
        "planet.ketu.house", "planet.mars.exalted", "planet.mars.house",
        "yoga.parivartana_3rd_8th", "dasha.active_mahadasha_lord", "dasha.active_antardasha_lord",
        *_PENDING_FACTS,
    ),
    dependencies=("D1", "D3", "D9", "D12", "D27", "D30", "dasha", "transits", "sahams"),
    rule_refs=(
        TechniqueRuleRef("MED-ONCO-001", "1.0", RuleRole.PRIMARY,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("MED-GEN-002", "1.0", RuleRole.PRIMARY,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("MED-SURG-003", "1.0", RuleRole.PRIMARY,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("MED-HOUSE-004", "1.0", RuleRole.SUPPORTING,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("MED-YOGA-005", "1.0", RuleRole.SUPPORTING,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("MED-DREK-006", "1.0", RuleRole.SUPPORTING,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("MED-D30-007", "1.0", RuleRole.PRIMARY,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("MED-SAHAM-008", "1.0", RuleRole.SUPPORTING,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
        TechniqueRuleRef("MED-DASHA-009", "1.0", RuleRole.PRIMARY,
                         ProvenanceStatus.SOURCE_DERIVED, source_reference=_SOURCE),
    ),
    provenance=ProvenanceStatus.UNTESTED,
    status="research",
    unresolved_inconsistencies=(
        "Ayudha Drekkana and Sarpa Drekkana evaluation require granular D3 classification facts.",
        "D30 Venus-Jupiter-Rahu tissue affliction requires granular D30 multi-planet conjunction facts.",
        "Roga and Mrityu Sahams require planetary longitude calculation of Arabic parts.",
    ),
)

if get_technique(CLINICAL_ONCOLOGY_TECHNIQUE.technique_id) is None:
    register_technique(CLINICAL_ONCOLOGY_TECHNIQUE)
