"""
AstroOS — Priority 11: Pydantic Schemas for Experiment Management API
"""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ExperimentCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., max_length=500)
    author: str = Field(default="researcher")
    tags: List[str] = Field(default_factory=list)


class SnapshotFreezeRequest(BaseModel):
    dataset_id: str
    dataset_version: str = "1.0"
    record_count: int = 100
    dataset_hash: str
    dsl_rule_ids: List[str] = Field(default_factory=list)
    classical_techniques: List[str] = Field(default_factory=list)
    calibration_profile_id: str
    calibration_status: str = "ACTIVE"
    technique_weights: dict[str, float]
    primary_brier_score: float
    primary_log_loss: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: Optional[float] = None
    roc_auc_status: str = "VALID"
    sample_size_n: int = 30
    hit_rate: float = 0.85
    consensus_profile_id: str = "parashari_standard_v1"
    minimum_activation_threshold: int = 60
    conflict_penalty_multiplier: float = 1.25
    execution_params: dict[str, Any] = Field(default_factory=dict)
    parent_snapshot_id: Optional[str] = None


class CompareExperimentsRequest(BaseModel):
    exp1_id: str
    snapshot1_id: str
    exp2_id: str
    snapshot2_id: str


class ExperimentImportRequest(BaseModel):
    bundle_json: str
