"""
AstroOS — Epistemic Claim & Resolved State Domain Models
========================================================
Implements the Epistemic Contract between Shastric Rule Experts, the Deterministic
Confluence Resolver, and the Constrained LLM Narrative Synthesis Layer.

Core Invariants Enforced:
  1. Separate "Truth Assembly" (Rules & Deterministic Resolver) from "Narrative Assembly" (LLM).
  2. Claims are partitioned by ClaimType:
     - PROMISE: Natal potential & capacity (confluence-aggregated).
     - TIMING: Temporal windows (intersection/overlap logic, NEVER averaged).
     - INTENSITY: Magnitude & severity of impact.
     - MODALITY: Structural expression & manifestation narrative.
  3. Redundancy Adjustment: Tracks underlying factors to compute Effective-N.
  4. Explicit Refusal/Abstention: Direct support for NO_PROMISE state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Literal, Optional, Tuple

ClaimType = Literal["promise", "timing", "intensity", "modality"]
ConfidenceBand = Literal["DEFER", "LOW", "MODERATE", "HIGH"]


@dataclass(frozen=True)
class Claim:
    """The standardized, typed artifact emitted by every Shastric rule expert."""
    expert_id: str                                  # e.g. "jha.d1_bhavachalita", "vimsottari.pd_sookshma"
    domain: str                                     # "career", "marriage", "health", "property", "bereavement"
    event_type: str                                 # "career.promotion", "health.surgery", "relocation"
    claim_type: ClaimType                           # "promise" | "timing" | "intensity" | "modality"
    direction: float                                # -1.0 (severe denial/affliction) to +1.0 (strong affirmation)
    support: Dict[str, Any]                         # Diagnostic details: yogas, houses, degrees, speeds
    rule_sources: Tuple[str, ...]                   # Shastric canonical citations (e.g. "BPHS Ch. 29 Sl. 14")
    expert_internal_confidence: float               # 0.0 to 1.0 expert-level certainty
    preconditions: Dict[str, Any] = field(default_factory=dict)  # Required preconditions (e.g. {"birth_accuracy": "< 5m"})
    timing_window: Optional[Tuple[date, date]] = None            # (start_date, end_date) if claim_type == "timing"
    underlying_factors: Tuple[str, ...] = field(default_factory=tuple)  # Factors used, e.g. ("jupiter", "10th_house", "amk")


@dataclass(frozen=True)
class ConfluenceMetrics:
    """Detailed mathematical evidence breakdown."""
    raw_claims_count: int
    effective_n: float                              # Redundancy-corrected evidence count
    mean_direction: float                           # Weighted directional alignment (-1.0 to +1.0)
    agreement_ratio: float                          # 0.0 to 1.0 agreement across independent streams
    contradiction_count: int                        # Number of actively contradicting claims
    redundancy_discount: float                      # Percentage of evidence discounted due to shared underlying factors


@dataclass(frozen=True)
class ResolvedEpistemicState:
    """
    The definitive, deterministic, and immutable state emitted by the Confluence Resolver.
    This is the ONLY data artifact permitted into the LLM synthesis layer.
    """
    prediction_id: str
    domain: str
    event_type: str
    has_promise: bool                               # False if confidence_band == "DEFER" or direction <= 0.0
    confidence_band: ConfidenceBand                 # "DEFER" | "LOW" | "MODERATE" | "HIGH"
    direction_score: float                          # -1.0 to +1.0 net directional score
    timing_window: Optional[Tuple[date, date]]      # Intersected temporal window
    confluence: ConfluenceMetrics
    primary_evidence: Tuple[Dict[str, Any], ...]    # Verified claims supporting the conclusion
    contradictions: Tuple[Dict[str, Any], ...]      # Verified claims opposing the conclusion
    modalities: Tuple[str, ...]                     # Verified behavioral/situational descriptors
    fail_conditions: Tuple[str, ...]                # Required boundary caveats (e.g. "BTR required")
    calibration_basis: str                          # Empirical audit provenance
    abstention_reason: Optional[str] = None         # Populated if has_promise == False
