"""
AstroOS — Grounded AI Shastric Explanation Narrator
===================================================

Canonical Reference: docs/CANONICAL_PREDICTION_FRAMEWORK.md (Step 9 & Explainability)
Translates Evidence Packages and Calibrated Prediction Verdicts into
structured, hallucination-free, auditable Shastric explanations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from apps.api.services.phalita_core.canonical_facts_generator import CanonicalFacts
from apps.api.services.phalita_core.evidence_aggregator import DomainEvidencePackage
from apps.api.services.phalita_core.prediction_calibrator import CalibratedPredictionVerdict


@dataclass(frozen=True)
class ShastricGroundedExplanation:
    domain: str
    target_date_iso: str
    signal_score_display: str               # e.g., "7.45 / 9.0 (HIGH_PROMINENCE)"
    confidence_display: str                 # e.g., "85.0% (±0.30)"
    executive_verdict: str
    astronomical_grounding_narrative: str
    shastric_classical_citations: Tuple[str, ...]
    temporal_dasha_synthesis: str
    friction_and_delay_analysis: str
    siddhantic_counsel: str
    full_markdown_report: str


class ShastricExplanationNarrator:
    """
    Builds transparent, mathematically anchored explanations.
    """

    @classmethod
    def generate_explanation(
        cls,
        facts: CanonicalFacts,
        evidence: DomainEvidencePackage,
        verdict: CalibratedPredictionVerdict,
    ) -> ShastricGroundedExplanation:
        """
        Creates fully grounded, provenance-backed explanation.
        """
        dom_title = verdict.domain.capitalize()
        score_str = f"{verdict.calibrated_signal_score:.2f} / 9.0 ({verdict.signal_tier})"
        conf_str = f"{verdict.confidence_percentage:.1f}% (±{verdict.confidence_margin_delta:.2f})"

        # 1. Executive Verdict
        if verdict.signal_tier == "HIGH_PROMINENCE":
            exec_verdict = (
                f"Strong planetary confluence indicates high manifestation prominence for {dom_title} "
                f"at target date {verdict.target_date_iso} (Calibrated Signal Score: {score_str})."
            )
        elif verdict.signal_tier == "MODERATE_PROMINENCE":
            exec_verdict = (
                f"Moderate planetary alignment observed for {dom_title} at target date {verdict.target_date_iso}. "
                f"Natal promise is active with minor delay/friction factors (Calibrated Signal Score: {score_str})."
            )
        else:
            exec_verdict = (
                f"Planetary indicators for {dom_title} remain dormant or encounter structural friction "
                f"at target date {verdict.target_date_iso} (Calibrated Signal Score: {score_str})."
            )

        # 2. Astronomical Grounding Narrative
        anchors_str = "; ".join(
            f"{a.identifier} ({a.recorded_value})"
            for a in evidence.primary_astronomical_anchors[:4]
        )
        astro_narrative = (
            f"Nativity has Ascendant in {facts.ascendant_rashi} ({facts.ascendant_degree:.2f}°) and Moon in {facts.chandra_rashi}. "
            f"Karakamsha Lagna is established in {facts.karakamsha_lagna_rashi}. "
            f"Key astronomical anchors: {anchors_str}."
        )

        # 3. Shastric Classical Citations
        citations = tuple(
            f"{r.rule_name} [{r.sanskrit_source}]: {r.rationale}"
            for r in evidence.supporting_shastric_rules
        )

        # 4. Temporal Dasha Synthesis
        active_dasha_str = f"{facts.active_d1_dasha.get('MD')}-{facts.active_d1_dasha.get('AD')}-{facts.active_d1_dasha.get('PD')}"
        dasha_narrative = (
            f"Active D1 Vimshottari period is {active_dasha_str}. "
            f"Mahadasha lord ({facts.active_d1_dasha.get('MD')}) establishes broad temporal jurisdiction, "
            f"while Antardasha lord ({facts.active_d1_dasha.get('AD')}) gates event activation."
        )

        # 5. Friction & Delay Analysis
        if evidence.inhibiting_shastric_rules:
            friction_str = "; ".join(r.rationale for r in evidence.inhibiting_shastric_rules)
        else:
            friction_str = "No major Upagraha or Dusthana structural afflictions identified."

        # 6. Full Markdown Report
        md_report = f"""### Shastric Analysis: {dom_title} Domain
* **Target Date:** {verdict.target_date_iso}
* **Calibrated Signal Score:** {score_str}
* **Confidence Level:** {conf_str}
* **Provenance Reference:** `{verdict.evidence_provenance_id}`

#### 1. Executive Verdict
{exec_verdict}

#### 2. Astronomical Grounding
{astro_narrative}

#### 3. Active Dasha & Timing Matrix
{dasha_narrative}

#### 4. Shastric Rule Derivations & Classical Citations
""" + "\n".join(f"- **{c}**" for c in citations) + f"""

#### 5. Inhibiting Factors & Obstacle Audit
{friction_str}

#### 6. Siddhantic Guidance
{verdict.siddhantic_actionable_guidance}
"""

        return ShastricGroundedExplanation(
            domain=verdict.domain,
            target_date_iso=verdict.target_date_iso,
            signal_score_display=score_str,
            confidence_display=conf_str,
            executive_verdict=exec_verdict,
            astronomical_grounding_narrative=astro_narrative,
            shastric_classical_citations=citations,
            temporal_dasha_synthesis=dasha_narrative,
            friction_and_delay_analysis=friction_str,
            siddhantic_counsel=verdict.siddhantic_actionable_guidance,
            full_markdown_report=md_report.strip(),
        )
