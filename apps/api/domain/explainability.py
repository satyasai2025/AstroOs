"""
AstroOS — Research & Prediction Explainability Domain Models (Priority 17)

Defines domain dataclasses for:
  - Factor Layers (NATAL_PROMISE, DASHA_TIMING, TRANSIT_GOCHARA, ASHTAKAVARGA, DIVISIONAL_VARGA, YOGA_CONFIG)
  - Atomic Evidence Factors & normalized percentage contributions (explicitly marked as associational attribution)
  - Classical Shloka / Canonical Textual Justifications with verified status
  - Genuine Recalculation Counterfactual "What-If" Sensitivity Scenarios
  - Prediction Explanation Aggregate Reports with complete P1–P16 lineage provenance
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional


class FactorLayer(str, Enum):
    NATAL_PROMISE = "NATAL_PROMISE"
    DASHA_TIMING = "DASHA_TIMING"
    TRANSIT_GOCHARA = "TRANSIT_GOCHARA"
    ASHTAKAVARGA = "ASHTAKAVARGA"
    DIVISIONAL_VARGA = "DIVISIONAL_VARGA"
    YOGA_CONFIG = "YOGA_CONFIG"


@dataclass(frozen=True)
class AtomicEvidenceFactor:
    """An individual astrological / astronomical factor contributing to a prediction."""
    factor_id: str
    name: str
    layer: FactorLayer
    raw_value: float          # e.g., 0.85
    calibrated_weight: float  # e.g., 0.35
    contribution_percent: float  # e.g., 32.5% (sums to 100% across all factors)
    attribution_type: str     # "ASSOCIATIONAL_ATTRIBUTION" (mathematical decomposition, not causal claim)
    direction: str            # "POSITIVE_REINFORCING" or "INHIBITING_NEGATIVE"
    classical_citation: str   # Exact verified source/chapter/verse, or "PROVENANCE_NOT_VERIFIED"
    citation_verified: bool   # True only if verified from canonical texts (BPHS, Phaladeepika, Jatakaparijata, Jaimini)
    epistemic_grade: str      # GRADE_A_RIGOROUS, etc.
    description: str          # Contextual explanation of factor behavior


@dataclass(frozen=True)
class CounterfactualScenario:
    """A 'what-if' sensitivity scenario derived from actual engine recalculation."""
    scenario_id: str
    perturbed_parameter: str  # e.g. "birth_time_shift_minutes", "transit_date", "dasha_lord_combustion"
    parameter_value: str      # e.g. "+2 min", "TRUE"
    baseline_score: float     # Actual baseline score
    simulated_score: float    # Actual score after rerunning underlying engines
    score_delta_percent: float  # (simulated - baseline) / baseline * 100
    divergence_reason: str    # Engine-derived explanation of divergence
    recalculation_engine_used: str  # e.g. "HoroscopeEngine + DivisionalEngine + DashaEngine"


@dataclass(frozen=True)
class PredictionExplanation:
    """Comprehensive multi-level explainability report for a targeted prediction window."""
    explanation_id: str
    target_objective: str
    event_window_start: date
    event_window_end: date
    composite_confidence_score: float
    plain_summary: str
    classical_justification: str
    empirical_synthesis: str
    provenance_lineage: tuple[str, ...]  # Traceable chain: ["P1 Ephemeris", "P2 D1 Chart", "P6 Dasha", "P8 Orchestrator", "P10 Calibration", "P12 Confluence", "P16 Evidence"]
    atomic_factors: tuple[AtomicEvidenceFactor, ...]
    counterfactuals: tuple[CounterfactualScenario, ...]
    generated_at: datetime
