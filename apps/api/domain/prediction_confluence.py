"""
AstroOS — Unified Multi-System Prediction Synthesis & Confluence Domain (Module 23, Priority 8)

Pure domain models for:
1. Multi-system analytical synthesis (Parashari, KP, SBC, Classical Rules, Ashtakavarga, Empirical Backtests)
2. Deterministic Confluence Matrix (k/N agreement and veto detection)
3. 3-Tier Evidence Provenance (Calculated Ephemeris, Classical Literature, Empirical Backtest)
4. Peak timing window intersection
5. Seamless freezing into immutable P7 Prediction Validation snapshots
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from apps.api.domain.prediction_validation import PredictionCategory


class ProvenanceType(str, Enum):
    CALCULATED_EPHEMERIS = "CALCULATED_EPHEMERIS"
    CLASSICAL_LITERATURE = "CLASSICAL_LITERATURE"
    EMPIRICAL_BACKTEST = "EMPIRICAL_BACKTEST"


class SystemSupportStatus(str, Enum):
    SUPPORTING = "SUPPORTING"
    CONTRADICTING_VETO = "CONTRADICTING_VETO"
    NEUTRAL = "NEUTRAL"
    UNAVAILABLE = "UNAVAILABLE"


class SynthesizedVerdict(str, Enum):
    UNANIMOUS_CONFLUENCE = "UNANIMOUS_CONFLUENCE"
    STRONG_CONFLUENCE = "STRONG_CONFLUENCE"
    MODERATE_CONFLUENCE = "MODERATE_CONFLUENCE"
    CONFLICTED_VETO = "CONFLICTED_VETO"
    WEAK_UNCONVERGED = "WEAK_UNCONVERGED"


def compute_synthesis_hash(synthesis_dict: dict[str, Any]) -> str:
    """Computes a deterministic SHA-256 checksum over synthesized multi-system prediction evidence."""
    canonical_json = json.dumps(synthesis_dict, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SystemContribution:
    """Individual astrological system's evidence and support status."""
    system_id: str  # "PARASHARI_DASHA", "GOCHARA_TRANSIT", "KP_CSL", "SBC_VEDHA", "CLASSICAL_YOGA", "ASHTAKAVARGA"
    system_name: str
    support_status: SystemSupportStatus
    provenance_type: ProvenanceType
    primary_houses: list[int]
    active_significators: list[str]
    rule_or_factor: str
    rationale: str
    veto_reason: Optional[str] = None
    evidence_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConfluenceMatrix:
    """Deterministic confluence evaluation across all analytical systems."""
    supporting_count: int  # k
    veto_count: int  # c
    neutral_count: int
    total_systems: int  # N
    confluence_ratio: float  # k / N
    active_vetoes: list[str]
    synthesized_verdict: SynthesizedVerdict
    verdict_rationale: str


@dataclass(frozen=True)
class SynthesizedTimingWindow:
    """Exact intersected temporal window for peak event fructification."""
    window_start: datetime
    window_end: datetime
    peak_fructification_date: datetime
    dasha_sub_period: str
    transit_trigger: str
    sbc_trigger_moment: str


@dataclass(frozen=True)
class EmpiricalTrackRecord:
    """Historical empirical validation metrics derived from P7 backtests."""
    historical_hit_rate: float
    historical_precision: Optional[float]
    sample_size: int
    wilson_95_ci: tuple[float, float]
    sample_size_warning: Optional[str] = None
    matched_cohort_name: str = ""


@dataclass(frozen=True)
class UnifiedPredictionSynthesis:
    """
    Master synthesized prediction combining all analytical engines into an auditable evidence chain.
    """
    synthesis_id: str
    chart_id: str
    subject_name: str
    category: PredictionCategory
    synthesized_event_description: str
    confluence_matrix: ConfluenceMatrix
    system_contributions: list[SystemContribution]
    synthesized_timing_window: SynthesizedTimingWindow
    empirical_track_record: EmpiricalTrackRecord
    provenance_breakdown: dict[str, list[str]]
    synthesis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    synthesis_hash: str = ""

    def __post_init__(self):
        if not self.synthesis_hash:
            synthesis_blob = {
                "synthesis_id": self.synthesis_id,
                "chart_id": self.chart_id,
                "subject_name": self.subject_name,
                "category": self.category.value,
                "synthesized_event_description": self.synthesized_event_description,
                "confluence_verdict": self.confluence_matrix.synthesized_verdict.value,
                "confluence_ratio": self.confluence_matrix.confluence_ratio,
                "supporting_count": self.confluence_matrix.supporting_count,
                "veto_count": self.confluence_matrix.veto_count,
                "active_vetoes": self.confluence_matrix.active_vetoes,
                "contributions": [
                    {
                        "system_id": sc.system_id,
                        "support_status": sc.support_status.value,
                        "provenance_type": sc.provenance_type.value,
                        "rule_or_factor": sc.rule_or_factor,
                    }
                    for sc in self.system_contributions
                ],
                "timing_peak": self.synthesized_timing_window.peak_fructification_date.isoformat(),
            }
            object.__setattr__(self, "synthesis_hash", compute_synthesis_hash(synthesis_blob))
