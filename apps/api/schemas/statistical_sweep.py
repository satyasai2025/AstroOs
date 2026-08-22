"""
AstroOS — Hypothesis-First Statistical Sweeps Schemas (Module 17, Phase 2)
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ExposureRuleSchema(BaseModel):
    rule_type: str = Field(..., description="Type of astrological exposure (e.g. 'graha_in_bhava', 'yoga_present')")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Rule specific parameters")
    description: Optional[str] = ""


class HypothesisDefinitionSchema(BaseModel):
    id: str
    title: str
    category: str
    exposure_rule: ExposureRuleSchema
    target_outcome: str
    description: str
    pre_registered: bool = True
    classical_reference: Optional[str] = None


class ContingencyTableSchema(BaseModel):
    a_exposed_cases: int
    b_exposed_controls: int
    c_unexposed_cases: int
    d_unexposed_controls: int
    total_n: int
    total_exposed: int
    total_unexposed: int
    total_cases: int
    total_controls: int
    exposure_rate_cases: float
    exposure_rate_controls: float


class HypothesisEvaluationRequest(BaseModel):
    hypothesis: Optional[HypothesisDefinitionSchema] = None
    hypothesis_id: Optional[str] = None  # If referencing a standard hypothesis
    contingency_table: Optional[ContingencyTableSchema] = None
    cohort_records: Optional[list[dict[str, Any]]] = None
    total_hypotheses_in_sweep: int = 1
    nominal_alpha: float = 0.05


class HypothesisResultSchema(BaseModel):
    hypothesis: HypothesisDefinitionSchema
    contingency_table: ContingencyTableSchema
    sample_size_n: int
    odds_ratio: float
    odds_ratio_ci_lower: float
    odds_ratio_ci_upper: float
    relative_risk: float
    relative_risk_ci_lower: float
    relative_risk_ci_upper: float
    cohen_w_effect_size: float
    cramers_v: float
    chi_square_stat: float
    chi_square_p_value: float
    fisher_exact_p_value: float
    is_significant_nominal: bool
    bonferroni_adjusted_alpha: float
    is_significant_bonferroni: bool
    fdr_q_value: float
    is_significant_fdr: bool
    has_small_sample_warning: bool
    statistical_power_estimate: float
    verdict: str
    audit_trace: list[str]


class MultiSweepRequest(BaseModel):
    cohort_tag: str
    cohort_records: list[dict[str, Any]]
    hypothesis_ids: Optional[list[str]] = None
    custom_hypotheses: Optional[list[HypothesisDefinitionSchema]] = None
    nominal_alpha: float = 0.05


class MultiSweepResponse(BaseModel):
    sweep_id: str
    cohort_tag: str
    total_cohort_size: int
    hypotheses_tested_count: int
    bonferroni_alpha: float
    nominal_significant_count: int
    fdr_significant_count: int
    bonferroni_significant_count: int
    results: list[HypothesisResultSchema]
    generated_at: str


class StandardHypothesesResponse(BaseModel):
    total_count: int
    hypotheses: list[HypothesisDefinitionSchema]


class CohortPipelineRequest(BaseModel):
    cohort_tag: str
    raw_records: list[dict[str, Any]]
    min_rodden_rating: str = "B"
    hypothesis_ids: Optional[list[str]] = None
    custom_hypotheses: Optional[list[HypothesisDefinitionSchema]] = None
    nominal_alpha: float = 0.05


class Stage1IngestionSchema(BaseModel):
    total_received: int
    total_accepted: int
    total_rejected: int
    duplicates_count: int
    provenance_hash_sha256: str


class Stage2ValidationSchema(BaseModel):
    accepted_events_count: int
    rejected_events_count: int
    rejections_by_code: dict[str, int]


class Stage3BatchChartSchema(BaseModel):
    generated_charts_count: int
    calculation_time_ms: float
    ephemeris_ayanamsa: str = "lahiri"


class Stage4FeatureExtractionSchema(BaseModel):
    subjects_profiled_count: int
    features_per_subject_count: int
    sample_features: dict[str, Any]


class Stage5HypothesisSweepSchema(BaseModel):
    hypotheses_tested_count: int
    bonferroni_adjusted_alpha: float
    nominal_significant_count: int
    fdr_significant_count: int
    bonferroni_significant_count: int


class CohortPipelineResponse(BaseModel):
    pipeline_run_id: str
    cohort_tag: str
    stage_1_ingestion: Stage1IngestionSchema
    stage_2_validation: Stage2ValidationSchema
    stage_3_batch_charts: Stage3BatchChartSchema
    stage_4_feature_extraction: Stage4FeatureExtractionSchema
    stage_5_hypothesis_sweep: Stage5HypothesisSweepSchema
    sweep_report: MultiSweepResponse
    executed_at: str

