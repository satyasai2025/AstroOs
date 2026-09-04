"""
AstroOS — Research Discovery & Hypothesis Mining Schemas (Priority 19)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class AstrologicalPatternPrimitiveItem(BaseModel):
    dimension: str
    operator: str
    value: str
    description: str


class ReplicationRecordItem(BaseModel):
    holdout_dataset_id: str
    holdout_sample_size: int
    holdout_support_percent: float
    holdout_confidence_percent: float
    holdout_statistical_lift: float
    holdout_fdr_q_value: float
    is_replication_confirmed: bool
    replicated_at: datetime


class DiscoveredHypothesisItem(BaseModel):
    hypothesis_id: str
    name: str
    target_objective: str
    pattern_primitives: List[AstrologicalPatternPrimitiveItem]
    discovery_dataset_id: str
    discovery_sample_size: int
    discovery_support_percent: float
    discovery_confidence_percent: float
    discovery_statistical_lift: float
    discovery_raw_p_value: float
    discovery_fdr_q_value: float
    status: str
    replication_records: List[ReplicationRecordItem]
    lineage_snapshot_id: str
    discovered_at: datetime
    classical_provenance_note: str


class RunHypothesisMiningRequest(BaseModel):
    discovery_dataset_id: str = Field(default="ds-marriage-28", description="Primary discovery cohort dataset")
    holdout_dataset_id: str = Field(default="ds-marriage-100", description="Independent holdout cohort dataset")
    target_objective: str = Field(default="marriage", description="Target astrological outcome")
    min_support_percent: float = Field(default=15.0, description="Minimum cohort support percentage")
    min_statistical_lift: float = Field(default=1.35, description="Minimum effect size / lift threshold")
    max_fdr_q_value: float = Field(default=0.05, description="Maximum Benjamini-Hochberg FDR q-value")


class HypothesisMiningReportResponse(BaseModel):
    mining_run_id: str
    discovery_dataset_id: str
    holdout_dataset_id: str
    target_objective: str
    total_combinations_evaluated: int
    candidate_hypotheses_count: int
    replicated_validated_count: int
    rejected_fdr_count: int
    top_hypotheses: List[DiscoveredHypothesisItem]
    execution_time_seconds: float
    mined_at: datetime
