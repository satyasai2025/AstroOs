"""
AstroOS — Hypothesis Generator (Phase E)

Generates testable astrological hypotheses from chart data. Uses
pre-defined templates and fills them with chart-specific details to
produce falsifiable predictions that can be validated against
datasets like GC-MASTER or RS-EVENT.

Knowledge Graph Integration (Task #13):
  When a KnowledgeGraphEngine instance is provided, each hypothesis
  queries the graph for entity data (planets, rashis, houses mentioned
  in the chart) and appends KG-sourced evidence to the hypothesis
  evidence list. The `graph_grounded` flag is set to True when KG data
  was successfully retrieved.

Calculator Integration Pattern (Task #13):
  AI services that need computed astrological values (shadbala,
  ashtakavarga, yoga, dasha) should call into the corresponding
  calculator engine directly — e.g. ShadbalaEngine, AshtakavargaEngine,
  YogaEngine, DashaEngine. The fallback chain is:
    Try AI generator → low-confidence/empty → fallback to rule-based
    calculator → still fails → return structural error.
  See apps/api/services/ai_fallback.py for the AIFallbackHandler class
  that implements this pattern.

All methods are static — no state.
"""

from __future__ import annotations

from typing import Any, Optional

from apps.api.domain.ai_phase_e import GeneratedHypothesis, HypothesisTemplate
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.yoga import YogaResult
from apps.api.services.knowledge_graph_engine import KnowledgeGraphEngine

# ── Pre-defined hypothesis templates ──────────────────────────────────────────

_HYPOTHESIS_TEMPLATES: tuple[HypothesisTemplate, ...] = (
    HypothesisTemplate(
        hypothesis_id="HYP-001",
        title="Exaltation Strength Correlation",
        description="Planets in exaltation produce measurably stronger positive life outcomes in their signification areas.",
        domain="dignity",
        conditions=("planet is exalted", "planet's signification domain has measurable events"),
        expected_outcome="Exalted planets show 2x the event confirmation rate of neutral planets in their domain.",
        test_method="Compare verification.confidence_score between exalted and non-exalted planet event pairs.",
        classical_references=("BPHS Ch. 23",),
        priority=8,
    ),
    HypothesisTemplate(
        hypothesis_id="HYP-002",
        title="Kendra-Trikona Synergy",
        description="Raja yoga combinations (kendra lord + trikona lord association) produce career/status events at significantly higher rates.",
        domain="yoga",
        conditions=("kendra lord associates with trikona lord", "event tracking over 10+ years"),
        expected_outcome="Charts with Raja Yoga show 3x career-event density vs charts without.",
        test_method="Compare career-event frequency between Raja Yoga charts and controls.",
        classical_references=("BPHS Ch. 41", "JaIMINI Sutra 4.1"),
        priority=9,
    ),
    HypothesisTemplate(
        hypothesis_id="HYP-003",
        title="Shadbala Threshold Accuracy",
        description="The classical shadbala threshold of 5 rupas (required bala) meaningfully separates effective from ineffective planetary periods.",
        domain="strength",
        conditions=("planet has computed shadbala", "planet rules a dasha period with recorded events"),
        expected_outcome="Planets with shadbala > 5 rupas have 70%+ event alignment in their dasha periods.",
        test_method="Sample n=50 event-dasha pairs, compare alignment rates above and below 5 rupa threshold.",
        classical_references=("BPHS Ch. 27", "Saravali Ch. 5"),
        priority=7,
    ),
    HypothesisTemplate(
        hypothesis_id="HYP-004",
        title="Ashtakavarga Bindu Prediction",
        description="Higher bindu counts in sarvashtakavarga correlate with more favorable event outcomes in those houses.",
        domain="ashtakavarga",
        conditions=("sarvashtakavarga computed", "events recorded per house"),
        expected_outcome="Houses with bindu count > 30 show 2x positive event ratio vs houses with bindu count < 25.",
        test_method="Classify events by house, correlate sarvashtakavarga bindu count with event sentiment.",
        classical_references=("BPHS Ch. 34", "Phaladeepika Ch. 19"),
        priority=6,
    ),
    HypothesisTemplate(
        hypothesis_id="HYP-005",
        title="Sade Sati Event Density",
        description="Saturn's transit through 12th, 1st, and 2nd from natal moon (Sade Sati) shows measurable event density increase in challenging life domains.",
        domain="transit",
        conditions=("saturn in sade sati", "event tracking during transit period"),
        expected_outcome="Event frequency during Sade Sati years is 1.5x higher than non-Sade-Sati years, with skew toward challenging categories.",
        test_method="Compare event counts per year during Sade Sati vs adjacent non-Sade-Sati periods.",
        classical_references=("BPHS Ch. 28", "Jataka Tattva"),
        priority=9,
    ),
    HypothesisTemplate(
        hypothesis_id="HYP-006",
        title="Dasha Lord Effect Strength",
        description="Dasha periods ruled by naturally beneficial planets (Jupiter, Venus, Moon) produce more confirmed positive events than periods ruled by malefics.",
        domain="dasha",
        conditions=("dasha tree computed", "events recorded across multiple dasha periods"),
        expected_outcome="Benefic-ruled dashas have 60%+ positive event ratio vs 40% for malefic-ruled dashas.",
        test_method="Classify dasha periods by lord's natural benefic/malefic nature, compare event sentiment ratios.",
        classical_references=("BPHS Ch. 45", "Vriddha Karika"),
        priority=8,
    ),
    HypothesisTemplate(
        hypothesis_id="HYP-007",
        title="Varga Consistency Hypothesis",
        description="Planets occupying the same rashi across multiple varga charts (varga samvada) show stronger real-world expression of their significations.",
        domain="varga",
        conditions=("multi-varga chart available", "planet in same rashi in 3+ vargas"),
        expected_outcome="Varga-samvada planets have 1.5x the verification confidence of non-samvada planets.",
        test_method="Compare verification confidence scores for samvada vs non-samvada planets.",
        classical_references=("Jaimini Sutra 1.2", "BPHS Ch. 7"),
        priority=6,
    ),
    HypothesisTemplate(
        hypothesis_id="HYP-008",
        title="Debilitation Compensation",
        description="Debilitated planets in D1 that occupy dignified positions in D9 (Navamsha) show compensation — reduced negative impact in their significations.",
        domain="dignity",
        conditions=("planet debilitated in D1", "planet exalted/own-sign in D9"),
        expected_outcome="Debilitated D1 + dignified D9 planets show neutral event alignment (not significantly positive or negative).",
        test_method="Compare event alignment for debilitated-D1/dignified-D9 vs debilitated-D1/debilitated-D9.",
        classical_references=("BPHS Ch. 7 Debilitation Cancellation", "Saravali Ch. 20"),
        priority=7,
    ),
)


class HypothesisGenerator:
    """Generates testable astrological hypotheses from chart data."""

    @staticmethod
    def get_templates() -> tuple[HypothesisTemplate, ...]:
        """Return all available hypothesis templates."""
        return _HYPOTHESIS_TEMPLATES

    @staticmethod
    def get_template(hypothesis_id: str) -> Optional[HypothesisTemplate]:
        """Get a single template by ID."""
        for t in _HYPOTHESIS_TEMPLATES:
            if t.hypothesis_id == hypothesis_id:
                return t
        return None

    @staticmethod
    def generate_for_chart(
        chart: D1Chart,
        yogas: Optional[list[YogaResult]] = None,
        domain_filter: Optional[str] = None,
        max_hypotheses: int = 5,
        knowledge_graph: Optional[KnowledgeGraphEngine] = None,
    ) -> list[GeneratedHypothesis]:
        """
        Generate concrete, testable hypotheses from a chart using the
        pre-defined templates. Each hypothesis is filled with chart-specific
        evidence and predictions.

        When *knowledge_graph* is provided, KG-sourced entity data is
        appended to each hypothesis's supporting evidence and the
        *graph_grounded* flag is set to True for successful lookups.
        """
        hypotheses: list[GeneratedHypothesis] = []
        present_yoga_ids = {y.yoga_id for y in (yogas or []) if y.is_present}

        # Rank by template priority (highest first) before applying the
        # max_hypotheses cap, so truncation keeps the most significant
        # applicable hypotheses rather than whichever happen to be declared
        # first in _HYPOTHESIS_TEMPLATES.
        candidates = [
            t for t in _HYPOTHESIS_TEMPLATES
            if not domain_filter or t.domain == domain_filter
        ]
        candidates.sort(key=lambda t: t.priority, reverse=True)

        for template in candidates:
            if len(hypotheses) >= max_hypotheses:
                break

            hypothesis = HypothesisGenerator._fill_template(
                template, chart, present_yoga_ids, knowledge_graph,
            )
            if hypothesis is not None:
                hypotheses.append(hypothesis)

        return hypotheses

    @staticmethod
    def _fill_template(
        template: HypothesisTemplate,
        chart: D1Chart,
        present_yoga_ids: set[str],
        knowledge_graph: Optional[KnowledgeGraphEngine] = None,
    ) -> Optional[GeneratedHypothesis]:
        """Fill a hypothesis template with chart-specific details."""
        supporting: list[str] = []
        contradicting: list[str] = []
        related_rules: list[str] = []
        related_yogas: list[str] = []
        graph_grounded = False

        if template.hypothesis_id == "HYP-001":
            # Check if any planet is exalted.
            exalted = [p for p in chart.planets if p.dignity and p.dignity.value == "exalted"]
            if exalted:
                for p in exalted[:3]:
                    supporting.append(f"{p.planet.capitalize()} is exalted in {p.rashi}")
                    related_rules.append(f"RULE-DIGNITY-00{p.house_number % 5 + 1}")
                    # KG evidence: look up planet entity for dignity relationships.
                    if knowledge_graph is not None:
                        graph_grounded |= HypothesisGenerator._add_kg_dignity_evidence(
                            knowledge_graph, p.planet, p.rashi, supporting,
                        )
            else:
                return None  # No exalted planets — skip this hypothesis.

        elif template.hypothesis_id == "HYP-002":
            # Check for raja yoga presence.
            raja_yogas = {y for y in present_yoga_ids if "raja" in y.lower()}
            if raja_yogas:
                supporting.append(f"Raja yoga detected: {', '.join(raja_yogas)}")
                related_yogas.extend(raja_yogas)
                # KG evidence: look up house categories for kendra/trikona context.
                if knowledge_graph is not None:
                    for h_num in [1, 4, 5, 7, 9, 10]:
                        entity = knowledge_graph.get_entity(f"BHAVA-{h_num}")
                        if entity is not None:
                            tags = entity.node.metadata.get("category_tags", [])
                            supporting.append(
                                f"KG: House {h_num} is a {', '.join(tags)} house."
                            )
                            graph_grounded = True
            else:
                return None

        elif template.hypothesis_id == "HYP-003":
            # Always testable — basic strength metric.
            supporting.append("Shadbala values are computed for all classical seven planets.")
            supporting.append("Threshold comparison can be run against any event dataset.")
            related_rules.extend(["RULE-STRENGTH-001", "RULE-STRENGTH-002"])
            # KG evidence: look up bala components.
            if knowledge_graph is not None:
                for component_key in ["sthana_bala", "dik_bala", "kala_bala", "cheshta_bala", "naisargika_bala", "drik_bala"]:
                    entity = knowledge_graph.get_entity(f"BALA-{component_key.upper().replace('_', '-')}")
                    if entity is not None:
                        supporting.append(
                            f"KG: {entity.node.label} is a recognised shadbala component "
                            f"(category: {entity.node.metadata.get('category', 'unknown')})."
                        )
                        graph_grounded = True

        elif template.hypothesis_id == "HYP-004":
            # Check ashtakavarga availability.
            supporting.append("Sarvashtakavarga bindu counts are computed per house.")
            supporting.append("Event categorization by house is the standard approach.")
            related_rules.append("RULE-STRENGTH-003")
            # KG evidence: look up houses.
            if knowledge_graph is not None:
                for h_num in range(1, 13):
                    entity = knowledge_graph.get_entity(f"BHAVA-{h_num}")
                    if entity is not None:
                        tags = entity.node.metadata.get("category_tags", [])
                        if "dusthana" in tags:
                            supporting.append(
                                f"KG: House {h_num} is a dusthana house — typically challenging life domains."
                            )
                            graph_grounded = True

        elif template.hypothesis_id == "HYP-005":
            # Check if Saturn data exists.
            saturn = next((p for p in chart.planets if p.planet == "saturn"), None)
            if saturn:
                supporting.append(f"Saturn is in {saturn.rashi} house {saturn.house_number} in the natal chart.")
                # KG evidence: look up Saturn in the ontology.
                if knowledge_graph is not None:
                    entity = knowledge_graph.get_entity("GRAHA-SATURN")
                    if entity is not None:
                        cls = entity.node.metadata.get("natural_classification", "unknown")
                        supporting.append(
                            f"KG: Saturn is classified as {cls} in the ontology."
                        )
                        graph_grounded = True
            else:
                return None

        elif template.hypothesis_id == "HYP-006":
            # Always testable if dasha tree exists.
            supporting.append("Dasha tree computed for the chart's birth data.")
            supporting.append("Dasha lords can be classified as benefic or malefic.")
            related_rules.extend(["RULE-DASHA-001", "RULE-DASHA-002", "RULE-DASHA-003"])
            # KG evidence: look up planet classifications.
            if knowledge_graph is not None:
                for planet_name in ["jupiter", "venus", "moon", "saturn", "mars"]:
                    entity = knowledge_graph.get_entity(f"GRAHA-{planet_name.upper()}")
                    if entity is not None:
                        cls = entity.node.metadata.get("natural_classification", "unknown")
                        supporting.append(
                            f"KG: {planet_name.capitalize()} is naturally {cls}."
                        )
                        graph_grounded = True

        elif template.hypothesis_id == "HYP-007":
            # Varga consistency check — always testable.
            supporting.append("Varga charts (D2-D60) can be compared for rashi consistency.")
            supporting.append("Varga samvada indicates concentrated signification expression.")
            related_yogas.extend([y for y in present_yoga_ids if "varga" in y.lower()])
            # KG evidence: look up varga entities.
            if knowledge_graph is not None:
                for varga_name in ["D2", "D3", "D9", "D10", "D12", "D30", "D60"]:
                    entity = knowledge_graph.get_entity(f"VARGA-{varga_name}")
                    if entity is not None:
                        div = entity.node.metadata.get("divisor", "?")
                        supporting.append(
                            f"KG: {varga_name} (divisor {div}) is available for varga comparison."
                        )
                        graph_grounded = True

        elif template.hypothesis_id == "HYP-008":
            # Check for debilitated planets in D1.
            debilitated = [p for p in chart.planets if p.dignity and p.dignity.value == "debilitated"]
            if debilitated:
                for p in debilitated[:2]:
                    supporting.append(f"{p.planet.capitalize()} is debilitated in D1 ({p.rashi})")
                    # KG evidence: look up debilitation compensation relationships.
                    if knowledge_graph is not None:
                        graph_grounded |= HypothesisGenerator._add_kg_dignity_evidence(
                            knowledge_graph, p.planet, p.rashi, supporting,
                        )
            else:
                return None

        else:
            return None

        # If we got here, the hypothesis is applicable.
        supporting.append(f"Classical reference: {', '.join(template.classical_references)}.")

        return GeneratedHypothesis(
            hypothesis_id=template.hypothesis_id,
            title=template.title,
            description=template.description,
            domain=template.domain,
            supporting_evidence=tuple(supporting),
            contradicting_evidence=tuple(contradicting),
            testable_prediction=template.expected_outcome,
            suggested_dataset="RS-EVENT" if template.domain in ("dasha", "transit") else "GC-MASTER",
            priority=template.priority,
            related_rules=tuple(related_rules),
            related_yogas=tuple(related_yogas),
            confidence="high" if template.priority >= 8 else "medium",
            graph_grounded=graph_grounded,
        )

    @staticmethod
    def _add_kg_dignity_evidence(
        kg: KnowledgeGraphEngine,
        planet_name: str,
        rashi_name: str,
        evidence: list[str],
    ) -> bool:
        """Query the KG for dignity relationships of *planet_name* and append
        findings to *evidence*. Returns True if any KG data was found."""
        found = False
        planet_entity = kg.get_entity(f"GRAHA-{planet_name.upper()}")
        if planet_entity is not None:
            cls = planet_entity.node.metadata.get("natural_classification", "unknown")
            evidence.append(f"KG: {planet_name.capitalize()} is naturally {cls}.")
            found = True
            for rel in planet_entity.relationships:
                if rel.relationship_type in ("Owns", "ExaltedIn", "DebilitatedIn", "MoolatrikonaIn"):
                    evidence.append(
                        f"KG: {planet_name.capitalize()} {rel.relationship_type} {rel.target_id}"
                    )
        # Also look up the rashi for element/modality context.
        rashi_entity = kg.get_entity(f"RASHI-{rashi_name.upper()}")
        if rashi_entity is not None:
            element = rashi_entity.node.metadata.get("element", "?")
            modality = rashi_entity.node.metadata.get("modality", "?")
            evidence.append(
                f"KG: {rashi_name.capitalize()} is a {modality} {element} sign."
            )
            found = True
        return found
