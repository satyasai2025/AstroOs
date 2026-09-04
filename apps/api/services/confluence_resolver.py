"""
AstroOS — Deterministic Confluence Resolver with Redundancy Adjustment
======================================================================
The mathematical arbiter of the Shastric MoE Engine:
  1. Partitions Claims into PROMISE, TIMING, INTENSITY, and MODALITY.
  2. Applies Redundancy Adjustment (Effective-N): Two rules relying on the same
     underlying planet/house are discounted for mutual correlation.
  3. Timing Windows: Computes strict temporal INTERSECTION (never averages).
  4. Confidence Calibration: Emits ordinal bands (DEFER, LOW, MODERATE, HIGH)
     with explicit contradiction audits and abstention paths.
"""

from __future__ import annotations

from datetime import date
import math
import uuid
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from apps.api.domain.epistemic_claim import (
    Claim,
    ConfidenceBand,
    ConfluenceMetrics,
    ResolvedEpistemicState,
)


class ConfluenceResolver:
    """
    Deterministic Epistemic Confluence Engine.
    Operates strictly without stochastic, probabilistic hallucination, or LLM inference.
    """

    @classmethod
    def resolve(
        cls,
        claims: Sequence[Claim],
        domain: str,
        event_type: str,
        calibration_basis: str = "AstroOS Gold-Standard Benchmark (Rodden AA)",
    ) -> ResolvedEpistemicState:
        """Resolves a set of disparate Shastric expert claims into an immutable epistemic state."""
        prediction_id = f"pred-{uuid.uuid4().hex[:8]}"

        if not claims:
            return ResolvedEpistemicState(
                prediction_id=prediction_id,
                domain=domain,
                event_type=event_type,
                has_promise=False,
                confidence_band="DEFER",
                direction_score=0.0,
                timing_window=None,
                confluence=ConfluenceMetrics(
                    raw_claims_count=0,
                    effective_n=0.0,
                    mean_direction=0.0,
                    agreement_ratio=0.0,
                    contradiction_count=0,
                    redundancy_discount=0.0,
                ),
                primary_evidence=(),
                contradictions=(),
                modalities=(),
                fail_conditions=("Zero expert claims submitted",),
                calibration_basis=calibration_basis,
                abstention_reason="No expert evidence available for this domain and query.",
            )

        # 1. Partition Claims by Type
        promise_claims = [c for c in claims if c.claim_type == "promise"]
        timing_claims = [c for c in claims if c.claim_type == "timing"]
        modality_claims = [c for c in claims if c.claim_type == "modality"]
        intensity_claims = [c for c in claims if c.claim_type == "intensity"]

        # 2. Compute Effective-N with Redundancy Adjustment for Promise Claims
        effective_n, redundancy_discount = cls._compute_effective_n(promise_claims)

        # 3. Direction and Contradiction Analysis
        pos_claims = [c for c in promise_claims if c.direction > 0.1]
        neg_claims = [c for c in promise_claims if c.direction < -0.1]

        weighted_pos = sum(c.direction * c.expert_internal_confidence for c in pos_claims)
        weighted_neg = sum(abs(c.direction) * c.expert_internal_confidence for c in neg_claims)
        total_weight = sum(c.expert_internal_confidence for c in promise_claims)

        if total_weight > 0:
            mean_direction = (weighted_pos - weighted_neg) / total_weight
        else:
            mean_direction = 0.0

        agreement_ratio = (
            max(weighted_pos, weighted_neg) / (weighted_pos + weighted_neg)
            if (weighted_pos + weighted_neg) > 0
            else 0.0
        )

        contradiction_count = min(len(pos_claims), len(neg_claims))

        confluence_metrics = ConfluenceMetrics(
            raw_claims_count=len(promise_claims),
            effective_n=round(effective_n, 2),
            mean_direction=round(mean_direction, 3),
            agreement_ratio=round(agreement_ratio, 3),
            contradiction_count=contradiction_count,
            redundancy_discount=round(redundancy_discount, 3),
        )

        # 4. Resolve Timing Window (Strict Intersection, Never Average)
        timing_window, timing_caveat = cls._intersect_timing_windows(timing_claims)

        # 5. Determine Confidence Band & Promise Existence
        has_promise = False
        abstention_reason: Optional[str] = None
        fail_conditions: List[str] = []

        if timing_caveat:
            fail_conditions.append(timing_caveat)

        if effective_n < 1.8 or mean_direction <= 0.15:
            confidence_band: ConfidenceBand = "DEFER"
            has_promise = False
            abstention_reason = (
                f"Insufficient independent shastric evidence (Effective-N={effective_n:.1f}, "
                f"Mean Direction={mean_direction:+.2f}). Shastric promise is not confirmed."
            )
        elif effective_n < 3.2 or agreement_ratio < 0.70:
            confidence_band = "LOW"
            has_promise = mean_direction > 0.25
            if contradiction_count > 0:
                fail_conditions.append(f"Active shastric contradiction detected ({contradiction_count} dissenting claims)")
        elif effective_n < 4.5 or agreement_ratio < 0.85:
            confidence_band = "MODERATE"
            has_promise = True
        else:
            confidence_band = "HIGH"
            has_promise = True

        # If timing is completely null/disjoint for a predicted event
        if has_promise and timing_window is None and timing_claims:
            fail_conditions.append("Timing windows between dasha and transit are completely disjoint")
            if confidence_band == "HIGH":
                confidence_band = "MODERATE"

        # 6. Build Structured Evidence & Contradiction Records
        primary_evidence = tuple(
            {
                "expert_id": c.expert_id,
                "direction": c.direction,
                "confidence": c.expert_internal_confidence,
                "rule_sources": list(c.rule_sources),
                "support": c.support,
                "underlying_factors": list(c.underlying_factors),
            }
            for c in (pos_claims if mean_direction >= 0 else neg_claims)
        )

        contradictions = tuple(
            {
                "expert_id": c.expert_id,
                "direction": c.direction,
                "confidence": c.expert_internal_confidence,
                "rule_sources": list(c.rule_sources),
                "support": c.support,
                "underlying_factors": list(c.underlying_factors),
            }
            for c in (neg_claims if mean_direction >= 0 else pos_claims)
        )

        modalities = tuple(str(c.support.get("descriptor", c.expert_id)) for c in modality_claims)

        return ResolvedEpistemicState(
            prediction_id=prediction_id,
            domain=domain,
            event_type=event_type,
            has_promise=has_promise,
            confidence_band=confidence_band,
            direction_score=round(mean_direction, 3),
            timing_window=timing_window,
            confluence=confluence_metrics,
            primary_evidence=primary_evidence,
            contradictions=contradictions,
            modalities=modalities,
            fail_conditions=tuple(fail_conditions),
            calibration_basis=calibration_basis,
            abstention_reason=abstention_reason,
        )

    @classmethod
    def _compute_effective_n(cls, claims: List[Claim]) -> Tuple[float, float]:
        """
        Computes Effective-N by discounting overlapping underlying factors.
        Uses pairwise Jaccard similarity across underlying factor sets.
        """
        if not claims:
            return 0.0, 0.0

        raw_n = len(claims)
        if raw_n == 1:
            return 1.0, 0.0

        factor_sets = [set(c.underlying_factors) for c in claims]
        weights = []

        for i, s_i in enumerate(factor_sets):
            overlap_sum = 0.0
            for j, s_j in enumerate(factor_sets):
                if i != j:
                    union = s_i.union(s_j)
                    intersection = s_i.intersection(s_j)
                    jaccard = len(intersection) / len(union) if union else 0.0
                    overlap_sum += jaccard
            # Individual claim weight discounted by its average redundancy
            w_i = 1.0 / (1.0 + overlap_sum)
            weights.append(w_i)

        effective_n = sum(weights)
        redundancy_discount = (raw_n - effective_n) / raw_n if raw_n > 0 else 0.0
        return max(1.0, effective_n), redundancy_discount

    @classmethod
    def _intersect_timing_windows(
        cls, timing_claims: List[Claim]
    ) -> Tuple[Optional[Tuple[date, date]], Optional[str]]:
        """
        Intersects temporal windows across active timing claims (e.g. Dasha window and Gochar window).
        Returns None if windows are mutually disjoint.
        """
        valid_windows = [c.timing_window for c in timing_claims if c.timing_window is not None]
        if not valid_windows:
            return None, None

        current_start, current_end = valid_windows[0]

        for w_start, w_end in valid_windows[1:]:
            latest_start = max(current_start, w_start)
            earliest_end = min(current_end, w_end)

            if latest_start <= earliest_end:
                current_start, current_end = latest_start, earliest_end
            else:
                # Disjoint intersection!
                return None, f"Temporal disjointness: [{current_start} to {current_end}] does not overlap with [{w_start} to {w_end}]"

        return (current_start, current_end), None
