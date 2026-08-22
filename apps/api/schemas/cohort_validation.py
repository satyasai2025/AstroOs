"""
AstroOS — Longitudinal Resonance & Cohort Validation Schemas (Priority 15)
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class CohortDatasetItem(BaseModel):
    dataset_id: str
    name: str
    target_objective: str
    total_subjects: int
    positive_count: int
    negative_count: int
    description: str


class HypothesisTestResultItem(BaseModel):
    metric_name: str
    observed_value: float
    null_mean: float
    null_std: float
    z_score: float
    p_value: float
    is_statistically_significant: bool
    confidence_interval_95: list[float]
    methodology: str


class CohortValidationEvaluateRequest(BaseModel):
    dataset_id: str = Field(default="ds-marriage-28", description="Target benchmark dataset ID")
    monte_carlo_iterations: int = Field(default=100, ge=20, le=1000)
    random_seed: int = Field(default=42)


class CohortValidationReportResponse(BaseModel):
    report_id: str
    dataset_id: str
    dataset_name: str
    target_objective: str
    total_subjects_evaluated: int
    positive_prevalence: float
    brier_score: float
    log_loss: float
    roc_auc: float
    pr_auc: float
    monte_carlo_iterations: int
    permutation_p_value: float
    null_roc_distribution: list[float]
    hypothesis_tests: list[HypothesisTestResultItem]
    executive_summary: str
    publication_provenance: str
