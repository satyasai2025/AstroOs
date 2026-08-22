"""
AstroOS — Research Discovery & Hypothesis Mining Domain Models (Priority 19)

Defines domain dataclasses for:
  - Pattern Dimensions (GRAHA, BHAVA, DASHA_TIMING, GOCHARA_TRANSIT, ASHTAKAVARGA, DIVISIONAL_VARGA)
  - Astrological Pattern Primitives
  - Multi-Criteria Replication Records on Independent Holdout Cohorts
  - Epistemic Hypothesis Classification Lifecycle (CANDIDATE_DISCOVERY, REPLICATED_VALIDATED, PROVENANCE_MAPPED, REJECTED_FDR)
  - Discovered Hypotheses & Full Mining Run Reports
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Sequence


class PatternDimension(str, Enum):
    GRAHA = "GRAHA"
    BHAVA = "BHAVA"
    DASHA_TIMING = "DASHA_TIMING"
    GOCHARA_TRANSIT = "GOCHARA_TRANSIT"
    ASHTAKAVARGA = "ASHTAKAVARGA"
    DIVISIONAL_VARGA = "DIVISIONAL_VARGA"


class HypothesisStatus(str, Enum):
    CANDIDATE_DISCOVERY = "CANDIDATE_DISCOVERY"
    REPLICATED_VALIDATED = "REPLICATED_VALIDATED"
    PROVENANCE_MAPPED = "PROVENANCE_MAPPED"
    REJECTED_FDR = "REJECTED_FDR"


@dataclass(frozen=True)
class AstrologicalPatternPrimitive:
    """An atomic astrological / astronomical rule condition."""
    dimension: PatternDimension
    operator: str      # e.g. "EQUALS", "GREATER_EQUAL", "ASPECTS", "IN"
    value: str         # e.g. "7th_Lord", ">= 30", "Jupiter", "Kendra"
    description: str   # Human-readable explanation of this primitive


@dataclass(frozen=True)
class ReplicationRecord:
    """Record of independent holdout cohort validation."""
    holdout_dataset_id: str
    holdout_sample_size: int
    holdout_support_percent: float
    holdout_confidence_percent: float
    holdout_statistical_lift: float
    holdout_fdr_q_value: float
    is_replication_confirmed: bool
    replicated_at: datetime


@dataclass(frozen=True)
class DiscoveredHypothesis:
    """A mined astrological rule candidate with empirical metrics, FDR correction, and replication lineage."""
    hypothesis_id: str
    name: str
    target_objective: str
    pattern_primitives: tuple[AstrologicalPatternPrimitive, ...]
    discovery_dataset_id: str
    discovery_sample_size: int
    discovery_support_percent: float
    discovery_confidence_percent: float
    discovery_statistical_lift: float
    discovery_raw_p_value: float
    discovery_fdr_q_value: float
    status: HypothesisStatus
    replication_records: tuple[ReplicationRecord, ...]
    lineage_snapshot_id: str
    discovered_at: datetime
    classical_provenance_note: str = "NO_CLASSICAL_PREDECESSOR"


@dataclass(frozen=True)
class HypothesisMiningReport:
    """Complete summary of a research discovery & hypothesis mining run."""
    mining_run_id: str
    discovery_dataset_id: str
    holdout_dataset_id: str
    target_objective: str
    total_combinations_evaluated: int
    candidate_hypotheses_count: int
    replicated_validated_count: int
    rejected_fdr_count: int
    top_hypotheses: tuple[DiscoveredHypothesis, ...]
    execution_time_seconds: float
    mined_at: datetime
