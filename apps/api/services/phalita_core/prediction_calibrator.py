"""
AstroOS — Calibrated Prediction Engine
======================================

Canonical Reference: docs/CANONICAL_PREDICTION_FRAMEWORK.md (Step 9 & 10)
Synthesizes DomainEvidencePackages and MoE expert gating to produce
the authoritative Calibrated Signal Score (0 to 9) and actionable verdicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from apps.api.services.phalita_core.evidence_aggregator import DomainEvidencePackage
from apps.api.services.phalita_core.phalita_moe_orchestrator import (
    PhalitaMoEConsultationVerdict,
    PhalitaMoEOrchestrator,
)


@dataclass(frozen=True)
class CalibratedPredictionVerdict:
    domain: str
    target_date_iso: str
    calibrated_signal_score: float             # 0.0 to 9.0 scale (Calibrated Signal Score, NOT raw probability)
    signal_tier: str                           # "HIGH_PROMINENCE", "MODERATE_PROMINENCE", "DORMANT_LOW_PROMINENCE"
    confidence_percentage: float               # e.g., 85.0%
    confidence_margin_delta: float             # e.g., ±0.45
    primary_shastric_promisers: Tuple[str, ...]
    primary_inhibiting_factors: Tuple[str, ...]
    evidence_provenance_id: str
    siddhantic_actionable_guidance: str


class PredictionCalibrator:
    """
    Synthesizes Evidence Packages with Shastric MoE orchestration into Calibrated Signal Scores.
    """

    @classmethod
    def calibrate_prediction(
        cls,
        evidence: DomainEvidencePackage,
        moe_verdict: PhalitaMoEConsultationVerdict,
    ) -> CalibratedPredictionVerdict:
        """
        Calibrates raw evidence with MoE consultation into a structured Calibrated Signal Score.
        """
        # Baseline from MoE orchestrator (0 to 9)
        base_moe_score = moe_verdict.final_cognitive_score

        # Rule evidence delta
        pos_signal = sum(r.signal_delta * r.confidence_weight for r in evidence.supporting_shastric_rules)
        neg_signal = sum(r.signal_delta * r.confidence_weight for r in evidence.inhibiting_shastric_rules)
        rule_net_mod = (pos_signal + neg_signal) * 0.35

        # Blended Calibrated Signal Score (Clamped to 0.0 to 9.0)
        raw_signal = base_moe_score + rule_net_mod
        calibrated_score = max(0.0, min(9.0, raw_signal))
        calibrated_score = round(calibrated_score, 2)

        # Determine Signal Tier
        if calibrated_score >= 6.5:
            tier = "HIGH_PROMINENCE"
        elif calibrated_score >= 4.5:
            tier = "MODERATE_PROMINENCE"
        else:
            tier = "DORMANT_LOW_PROMINENCE"

        # Compute Confidence & Margin
        ev_count = len(evidence.supporting_shastric_rules) + len(evidence.inhibiting_shastric_rules)
        conf_pct = min(95.0, max(50.0, 60.0 + (ev_count * 5.0)))
        margin = round(max(0.20, (100.0 - conf_pct) / 50.0), 2)

        promisers = tuple(r.rationale for r in evidence.supporting_shastric_rules[:4])
        inhibitors = tuple(r.rationale for r in evidence.inhibiting_shastric_rules[:3])

        guidance = moe_verdict.actionable_recommendation

        return CalibratedPredictionVerdict(
            domain=evidence.domain,
            target_date_iso=evidence.target_date_iso,
            calibrated_signal_score=calibrated_score,
            signal_tier=tier,
            confidence_percentage=round(conf_pct, 1),
            confidence_margin_delta=margin,
            primary_shastric_promisers=promisers,
            primary_inhibiting_factors=inhibitors,
            evidence_provenance_id=evidence.evidence_provenance_hash,
            siddhantic_actionable_guidance=guidance,
        )
