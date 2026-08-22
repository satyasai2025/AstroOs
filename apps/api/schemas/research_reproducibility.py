"""
AstroOS — Research Reproducibility & Independent Validation Schemas (Priority 22)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateRunManifestRequest(BaseModel):
    target_engine_priority: str = Field(..., description="Target Priority Engine (e.g. P15_COHORT, P20_PROSPECTIVE)")
    target_objective: str = Field(default="marriage", description="Target astrological outcome")
    dataset_id: str = Field(..., description="Dataset ID used in the run")
    astrological_formula: str = Field(..., description="Astrological rule/formula string")
    frozen_thresholds: Dict[str, float] = Field(default_factory=dict, description="Frozen parameters")
    random_seed: int = Field(default=42, description="Random seed")
    monte_carlo_iterations: int = Field(default=50, description="Iterations count")
    baseline_metrics: Dict[str, float] = Field(..., description="Baseline metrics to verify against")
    author: str = Field(default="ResearchReproducibilityEngine", description="Author")


class ImmutableRunManifestResponse(BaseModel):
    manifest_id: str
    target_engine_priority: str
    target_objective: str
    dataset_id: str
    dataset_sha256_hash: str
    engine_version: str
    astrological_formula: str
    frozen_thresholds: Dict[str, float]
    random_seed: int
    monte_carlo_iterations: int
    baseline_metrics: Dict[str, float]
    manifest_sha256_hash: str
    created_at: datetime
    parent_lineage_snapshot_id: str
    author: str


class ReExecuteManifestRequest(BaseModel):
    manifest_id: str = Field(..., description="Immutable manifest ID to independently re-execute")


class MetricDiffItemResponse(BaseModel):
    metric_name: str
    baseline_value: float
    reproduced_value: float
    absolute_delta: float
    is_exact_match: bool


class IndependentValidationAuditReportResponse(BaseModel):
    audit_id: str
    manifest_id: str
    target_engine_priority: str
    reproduced_at: datetime
    execution_duration_ms: float
    metric_diffs: List[MetricDiffItemResponse]
    status: str
    reproducibility_score_percent: float
    independent_repro_snapshot_id: str
    audit_summary: str
