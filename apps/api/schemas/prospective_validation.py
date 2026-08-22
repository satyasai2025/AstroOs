"""
AstroOS — Prospective Research Validation & Rule Lifecycle Schemas (Priority 20)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PreRegisterHypothesisRequest(BaseModel):
    hypothesis_id: str = Field(..., description="ID of the discovered hypothesis from P19")
    rule_name: str = Field(..., description="Canonical human-readable rule name")
    target_objective: str = Field(default="marriage", description="Target astrological outcome")
    formula_expression: str = Field(..., description="Frozen boolean / mathematical formula expression")
    thresholds: Dict[str, float] = Field(default_factory=dict, description="Frozen parameter thresholds")
    author: str = Field(default="ResearchValidationEngine", description="Author of the pre-registration")


class PreRegistrationRecordResponse(BaseModel):
    registration_id: str
    hypothesis_id: str
    rule_name: str
    target_objective: str
    frozen_formula: str
    frozen_thresholds: Dict[str, float]
    sha256_registration_hash: str
    registered_at: datetime
    lineage_snapshot_id: str
    author: str


class EvaluateProspectiveCohortRequest(BaseModel):
    registration_id: str = Field(..., description="Pre-registration record ID")
    total_subjects: int = Field(default=150, description="Total unseen prospective subjects")
    positive_prevalence: float = Field(default=0.52, description="Observed event prevalence")


class DriftAnalysisResponse(BaseModel):
    psi_drift_score: float
    is_significant_drift: bool
    drift_diagnosis: str


class ProspectiveEvaluationReportResponse(BaseModel):
    evaluation_id: str
    registration_id: str
    target_objective: str
    total_prospective_subjects: int
    positive_outcomes_count: int
    brier_score: float
    log_loss: float
    roc_auc: float
    pr_auc: float
    precision: float
    recall: float
    statistical_lift: float
    confidence_interval_95_roc: List[float]
    drift_analysis: DriftAnalysisResponse
    final_lifecycle_status: str
    epistemic_classification: str
    evaluated_at: datetime
