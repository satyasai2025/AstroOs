"""
AstroOS — Hypothesis-First Statistical Sweeps Domain Objects (Module 17, Phase 2)

Pure Python dataclasses for pre-registered hypothesis testing, contingency matrices,
inferential statistics (Odds Ratio, Chi-Square, Fisher's Exact, Cohen's w), and
multiple-testing corrections (Bonferroni, Benjamini-Hochberg FDR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class HypothesisCategory(str, Enum):
    MARRIAGE = "marriage"
    CAREER = "career"
    HEALTH = "health"
    LONGEVITY = "longevity"
    WEALTH = "wealth"
    EDUCATION = "education"
    SPIRITUALITY = "spirituality"
    GENERAL = "general"


class ScientificVerdict(str, Enum):
    CONFIRMED_SIGNIFICANT = "CONFIRMED_SIGNIFICANT"
    TREND_SUGGESTIVE = "TREND_SUGGESTIVE"
    NULL_INSUFFICIENT_EVIDENCE = "NULL_INSUFFICIENT_EVIDENCE"
    INVERSE_CORRELATION = "INVERSE_CORRELATION"


@dataclass(frozen=True)
class AstrologicalExposureRule:
    """Defines a deterministic astrological feature condition tested in H1."""

    rule_type: str  # e.g., 'graha_in_bhava', 'graha_in_rashi', 'yoga_present', 'ashtakavarga_threshold', 'argala_present'
    parameters: dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass(frozen=True)
class HypothesisDefinition:
    """Formal pre-registered scientific hypothesis H1."""

    id: str
    title: str
    category: HypothesisCategory
    exposure_rule: AstrologicalExposureRule
    target_outcome: str  # Name or key of the target life event/outcome label
    description: str
    pre_registered: bool = True
    classical_reference: Optional[str] = None


@dataclass(frozen=True)
class ContingencyTable2x2:
    """
    2x2 Contingency Table for Binary Exposure vs Binary Outcome.

                   Case (Outcome +)    Control (Outcome -)    Total
    Exposed (+)           a                     b             a + b
    Unexposed (-)         c                     d             c + d
    Total               a + c                 b + d             N
    """

    a_exposed_cases: int
    b_exposed_controls: int
    c_unexposed_cases: int
    d_unexposed_controls: int

    @property
    def total_n(self) -> int:
        return self.a_exposed_cases + self.b_exposed_controls + self.c_unexposed_cases + self.d_unexposed_controls

    @property
    def total_exposed(self) -> int:
        return self.a_exposed_cases + self.b_exposed_controls

    @property
    def total_unexposed(self) -> int:
        return self.c_unexposed_cases + self.d_unexposed_controls

    @property
    def total_cases(self) -> int:
        return self.a_exposed_cases + self.c_unexposed_cases

    @property
    def total_controls(self) -> int:
        return self.b_exposed_controls + self.d_unexposed_controls

    @property
    def exposure_rate_cases(self) -> float:
        cases = self.total_cases
        return round(self.a_exposed_cases / cases, 4) if cases > 0 else 0.0

    @property
    def exposure_rate_controls(self) -> float:
        controls = self.total_controls
        return round(self.b_exposed_controls / controls, 4) if controls > 0 else 0.0


@dataclass(frozen=True)
class HypothesisStatisticalResult:
    """Comprehensive statistical inference output for a tested hypothesis."""

    hypothesis: HypothesisDefinition
    contingency_table: ContingencyTable2x2
    sample_size_n: int

    # Effect size metrics
    odds_ratio: float
    odds_ratio_ci_lower: float
    odds_ratio_ci_upper: float
    relative_risk: float
    relative_risk_ci_lower: float
    relative_risk_ci_upper: float
    cohen_w_effect_size: float
    cramers_v: float

    # Hypothesis test p-values
    chi_square_stat: float
    chi_square_p_value: float
    fisher_exact_p_value: float
    is_significant_nominal: bool  # p < 0.05

    # Multi-testing adjustments
    bonferroni_adjusted_alpha: float
    is_significant_bonferroni: bool
    fdr_q_value: float
    is_significant_fdr: bool

    # Quality & verdict
    has_small_sample_warning: bool
    statistical_power_estimate: float
    verdict: ScientificVerdict
    audit_trace: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MultiHypothesisSweepReport:
    """Report aggregating results across a battery of tested hypotheses."""

    sweep_id: str
    cohort_tag: str
    total_cohort_size: int
    hypotheses_tested_count: int
    bonferroni_alpha: float
    nominal_significant_count: int
    fdr_significant_count: int
    bonferroni_significant_count: int
    results: tuple[HypothesisStatisticalResult, ...]
    generated_at: str


@dataclass(frozen=True)
class Stage1IngestionSummary:
    total_received: int
    total_accepted: int
    total_rejected: int
    duplicates_count: int
    provenance_hash_sha256: str


@dataclass(frozen=True)
class Stage2ValidationSummary:
    accepted_events_count: int
    rejected_events_count: int
    rejections_by_code: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Stage3BatchChartSummary:
    generated_charts_count: int
    calculation_time_ms: float
    ephemeris_ayanamsa: str = "lahiri"


@dataclass(frozen=True)
class Stage4FeatureExtractionSummary:
    subjects_profiled_count: int
    features_per_subject_count: int
    sample_features: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Stage5HypothesisSweepSummary:
    hypotheses_tested_count: int
    bonferroni_adjusted_alpha: float
    nominal_significant_count: int
    fdr_significant_count: int
    bonferroni_significant_count: int


@dataclass(frozen=True)
class CohortPipelineRunResult:
    """Complete end-to-end execution result of the 6-stage cohort research pipeline."""

    pipeline_run_id: str
    cohort_tag: str
    stage_1_ingestion: Stage1IngestionSummary
    stage_2_validation: Stage2ValidationSummary
    stage_3_batch_charts: Stage3BatchChartSummary
    stage_4_feature_extraction: Stage4FeatureExtractionSummary
    stage_5_hypothesis_sweep: Stage5HypothesisSweepSummary
    sweep_report: MultiHypothesisSweepReport
    executed_at: str

