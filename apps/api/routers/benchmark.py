"""
AstroOS — Benchmark & Dataset Research API Router

Endpoints for managing benchmark definitions, quality control audits,
cryptographic locking, and profile comparison evaluations.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from apps.api.domain.benchmark_dataset import (
    InclusionCriteria,
    LockedBenchmarkCorpus,
)
from apps.api.domain.benchmark_experiment import (
    BaselineComparison,
    BenchmarkExperiment,
    ExperimentProvenance,
)
from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
    ConsensusProfile,
)
from apps.api.domain.research_calibration import (
    BirthDataConfidence,
    EventDateConfidence,
    EventVerification,
)
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.services.benchmark_corpus_loader import BenchmarkCorpusLoader
from apps.api.services.benchmark_registry import BenchmarkRegistry, ImmutableBenchmarkError
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.calibration_engine import CalibrationEngine
from apps.api.services.dataset_validator import DatasetValidator
from apps.api.services.research_engine import ResearchEngine

router = APIRouter(prefix="/benchmarks", tags=["Benchmark & Research Dataset"])

_registry = BenchmarkRegistry()
_loader = BenchmarkCorpusLoader(registry=_registry)
_repo = BenchmarkExperimentRepository()

# Auto-load canonical corpora on module import
try:
    _loader.load_and_lock_all_canonical_corpora()
except Exception as e:
    print(f"[WARN] Error auto-loading canonical corpora: {e}")


class InclusionCriteriaSchema(BaseModel):
    min_birth_confidence: str = "B"
    allowed_date_confidences: list[str] = ["exact_date", "approx_week", "approx_month"]
    min_event_verification: str = "secondary_report"


class ValidateDatasetRequest(BaseModel):
    benchmark_id: str
    events: list[dict[str, Any]]
    inclusion_criteria: Optional[InclusionCriteriaSchema] = None


class RejectedRecordSchema(BaseModel):
    event_id: str
    subject_id: str
    rejection_code: str
    reason: str


class PossibleDuplicateSchema(BaseModel):
    primary_event_id: str
    flagged_event_id: str
    subject_id: str
    reason: str


class ValidateDatasetResponse(BaseModel):
    is_valid: bool
    total_submitted: int
    accepted_count: int
    rejected_count: int
    rejected_records: list[RejectedRecordSchema]
    flagged_warnings: list[PossibleDuplicateSchema]
    content_hash_sha256: str


class LockCorpusRequest(BaseModel):
    benchmark_id: str
    version: str  # e.g. "1.0.0"
    events: list[dict[str, Any]]
    inclusion_criteria: Optional[InclusionCriteriaSchema] = None


class LockCorpusResponse(BaseModel):
    benchmark_id: str
    version: str
    content_hash_sha256: str
    total_events: int
    event_type: str
    status: str


class BenchmarkDefinitionSchema(BaseModel):
    benchmark_id: str
    name: str
    event_type: str
    description: str
    standard_tolerance_days: int
    is_locked: bool = False
    locked_version: Optional[str] = None
    locked_event_count: Optional[int] = None
    content_hash_sha256: Optional[str] = None


class CompareProfilesRequest(BaseModel):
    version: str = "1.0.0"
    profile_ids: list[str] = ["parashari_standard_v1", "empirical_research_v1"]
    baseline_profile_id: str = "parashari_standard_v1"
    tolerance_days: int = 30
    split_seed: int = 42
    split_train_ratio: float = 0.70


class ProfileComparisonRowSchema(BaseModel):
    profile_id: str
    profile_name: str
    calibration_sample_size_n: int
    holdout_sample_size_n: int
    holdout_precision: float
    holdout_recall: float
    holdout_f1_score: float
    holdout_hit_rate_pct: float
    holdout_brier_score: float
    holdout_mae_peak_days: float
    holdout_median_peak_offset_days: float
    holdout_p90_peak_offset_days: float
    calibration_method: str


class BaselineDeltaSchema(BaseModel):
    profile_id: str
    baseline_profile_id: str
    delta_hit_rate_pct: float
    delta_brier_score: float
    delta_f1_score: float
    delta_mae_peak_days: float
    is_statistically_superior: bool
    p_value: float = 1.0
    odds_ratio: float = 1.0
    verdict: str = "EQUIVALENT_OR_INSUFFICIENT_EVIDENCE"


class BenchmarkComparisonResponse(BaseModel):
    experiment_id: str
    benchmark_id: str
    benchmark_version: str
    content_hash_sha256: str
    split_seed: int
    split_train_ratio: float
    tolerance_days: int
    total_benchmark_events: int
    train_events_count: int
    holdout_events_count: int
    rows: list[ProfileComparisonRowSchema]
    baseline_comparisons: list[BaselineDeltaSchema]


class CalibrationCurveBinSchema(BaseModel):
    score_range: str
    min_score: int
    max_score: int
    sample_size_n: int
    observed_hits: int
    empirical_hit_rate_pct: float
    rate_ci_95: list[float]
    has_small_n_warning: bool


class CalibrationCurveReportResponse(BaseModel):
    benchmark_id: str
    version: str
    profile_id: str
    total_train_n: int
    brier_score: float
    bins: list[CalibrationCurveBinSchema]


@router.get("", response_model=list[BenchmarkDefinitionSchema])
async def list_benchmark_definitions() -> list[BenchmarkDefinitionSchema]:
    """Lists canonical benchmark specifications and locked corpora."""
    defs = _registry.list_definitions()
    results = []
    for d in defs:
        corpus = _registry.get_locked_corpus(d.benchmark_id, "1.0.0")
        results.append(
            BenchmarkDefinitionSchema(
                benchmark_id=d.benchmark_id,
                name=d.name,
                event_type=d.event_type,
                description=d.description,
                standard_tolerance_days=d.standard_tolerance_days,
                is_locked=(corpus is not None),
                locked_version="1.0.0" if corpus else None,
                locked_event_count=len(corpus.events) if corpus else None,
                content_hash_sha256=corpus.content_hash_sha256 if corpus else None,
            )
        )
    return results


@router.get("/{benchmark_id}", response_model=BenchmarkDefinitionSchema)
async def get_benchmark_detail(benchmark_id: str) -> BenchmarkDefinitionSchema:
    """Gets details for a specific benchmark definition and locked corpus."""
    d = _registry.get_definition(benchmark_id)
    if not d:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Benchmark '{benchmark_id}' not found.")

    corpus = _registry.get_locked_corpus(benchmark_id, "1.0.0")
    return BenchmarkDefinitionSchema(
        benchmark_id=d.benchmark_id,
        name=d.name,
        event_type=d.event_type,
        description=d.description,
        standard_tolerance_days=d.standard_tolerance_days,
        is_locked=(corpus is not None),
        locked_version="1.0.0" if corpus else None,
        locked_event_count=len(corpus.events) if corpus else None,
        content_hash_sha256=corpus.content_hash_sha256 if corpus else None,
    )


@router.post("/validate", response_model=ValidateDatasetResponse)
async def validate_raw_dataset(body: ValidateDatasetRequest) -> ValidateDatasetResponse:
    """Audits raw records against QC rules and returns accepted events + rejection log."""
    definition = _registry.get_definition(body.benchmark_id)
    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Benchmark '{body.benchmark_id}' not found.")

    criteria = definition.inclusion_criteria
    validator = DatasetValidator()
    result = validator.validate_and_audit(body.events, criteria)

    return ValidateDatasetResponse(
        is_valid=result.is_valid,
        total_submitted=result.total_submitted,
        accepted_count=len(result.accepted_events),
        rejected_count=len(result.rejected_records),
        rejected_records=[
            RejectedRecordSchema(
                event_id=r.event_id,
                subject_id=r.subject_id,
                rejection_code=r.rejection_code.value,
                reason=r.reason,
            )
            for r in result.rejected_records
        ],
        flagged_warnings=[
            PossibleDuplicateSchema(
                primary_event_id=w.primary_event_id,
                flagged_event_id=w.flagged_event_id,
                subject_id=w.subject_id,
                reason=w.reason,
            )
            for w in result.flagged_warnings
        ],
        content_hash_sha256=result.content_hash_sha256,
    )


@router.post("/{benchmark_id}/lock", response_model=LockCorpusResponse)
async def lock_benchmark_corpus_endpoint(benchmark_id: str, body: LockCorpusRequest) -> LockCorpusResponse:
    """Ingests, validates, and locks an immutable benchmark corpus."""
    definition = _registry.get_definition(benchmark_id)
    if not definition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Benchmark '{benchmark_id}' not found.")

    validator = DatasetValidator()
    result = validator.validate_and_audit(body.events, definition.inclusion_criteria)

    if len(result.accepted_events) == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot lock corpus: zero accepted events passed quality audit.")

    corpus = LockedBenchmarkCorpus(
        benchmark_id=benchmark_id,
        version=body.version,
        content_hash_sha256=result.content_hash_sha256,
        event_type=definition.event_type,
        events=result.accepted_events,
        definition=definition,
    )

    try:
        _registry.lock_corpus(corpus)
    except ImmutableBenchmarkError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return LockCorpusResponse(
        benchmark_id=corpus.benchmark_id,
        version=corpus.version,
        content_hash_sha256=corpus.content_hash_sha256,
        total_events=len(corpus.events),
        event_type=corpus.event_type,
        status="LOCKED_IMMUTABLE",
    )


@router.post("/{benchmark_id}/compare", response_model=BenchmarkComparisonResponse)
async def compare_profiles_endpoint(
    benchmark_id: str,
    body: CompareProfilesRequest,
) -> BenchmarkComparisonResponse:
    """Executes multi-profile evaluation and baseline comparison against locked corpus."""
    corpus = _registry.get_locked_corpus(benchmark_id, body.version)
    if not corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Locked benchmark corpus '{benchmark_id}' v{body.version} not found. Please lock the corpus first.",
        )

    profile_map = {
        "parashari_standard_v1": PARASHARI_STANDARD_PROFILE,
        "empirical_research_v1": EMPIRICAL_RESEARCH_PROFILE,
    }

    profiles: list[ConsensusProfile] = []
    for pid in body.profile_ids:
        if pid in profile_map:
            profiles.append(profile_map[pid])

    if not profiles:
        profiles = [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE]

    import time
    t0 = time.perf_counter()

    runner = BenchmarkRunner()
    experiment = runner.run_experiment(
        corpus=corpus,
        profiles=profiles,
        baseline_profile_id=body.baseline_profile_id,
        tolerance_days=body.tolerance_days,
        seed=body.split_seed,
        train_ratio=body.split_train_ratio,
    )
    duration_ms = round((time.perf_counter() - t0) * 1000, 2)

    await _repo.save_experiment(experiment, duration_ms=duration_ms)

    return BenchmarkComparisonResponse(
        experiment_id=experiment.provenance.experiment_id,
        benchmark_id=experiment.report.benchmark_id,
        benchmark_version=experiment.report.benchmark_version,
        content_hash_sha256=experiment.report.content_hash_sha256,
        split_seed=experiment.report.split_seed,
        split_train_ratio=experiment.report.split_train_ratio,
        tolerance_days=experiment.report.tolerance_days,
        total_benchmark_events=experiment.report.total_benchmark_events,
        train_events_count=experiment.report.train_events_count,
        holdout_events_count=experiment.report.holdout_events_count,
        rows=[
            ProfileComparisonRowSchema(
                profile_id=r.profile_id,
                profile_name=r.profile_name,
                calibration_sample_size_n=r.calibration_sample_size_n,
                holdout_sample_size_n=r.holdout_sample_size_n,
                holdout_precision=r.holdout_precision,
                holdout_recall=r.holdout_recall,
                holdout_f1_score=r.holdout_f1_score,
                holdout_hit_rate_pct=r.holdout_hit_rate_pct,
                holdout_brier_score=r.holdout_brier_score,
                holdout_mae_peak_days=r.holdout_mae_peak_days,
                holdout_median_peak_offset_days=r.holdout_median_peak_offset_days,
                holdout_p90_peak_offset_days=r.holdout_p90_peak_offset_days,
                calibration_method=r.calibration_method,
            )
            for r in experiment.report.rows
        ],
        baseline_comparisons=[
            BaselineDeltaSchema(
                profile_id=b.profile_id,
                baseline_profile_id=b.baseline_profile_id,
                delta_hit_rate_pct=b.delta_hit_rate_pct,
                delta_brier_score=b.delta_brier_score,
                delta_f1_score=b.delta_f1_score,
                delta_mae_peak_days=b.delta_mae_peak_days,
                is_statistically_superior=b.is_statistically_superior,
            )
            for b in experiment.baseline_comparisons
        ],
    )


class ExperimentSummarySchema(BaseModel):
    experiment_id: str
    benchmark_id: str
    benchmark_version: str
    status: str
    split_seed: int
    split_train_ratio: float
    tolerance_days: int
    profile_ids: list[str]
    results_hash_sha256: str
    duration_ms: float
    created_at: Optional[str] = None


@router.get("/{benchmark_id}/experiments", response_model=list[ExperimentSummarySchema])
async def list_experiments(benchmark_id: str) -> list[ExperimentSummarySchema]:
    """Lists all archived benchmark experiments for a specific benchmark."""
    models = await _repo.list_by_benchmark_id(benchmark_id)
    return [
        ExperimentSummarySchema(
            experiment_id=m.experiment_id,
            benchmark_id=m.benchmark_id,
            benchmark_version=m.benchmark_version,
            status=m.status,
            split_seed=m.split_seed,
            split_train_ratio=m.split_train_ratio,
            tolerance_days=m.tolerance_days,
            profile_ids=m.profile_ids,
            results_hash_sha256=m.results_hash_sha256,
            duration_ms=m.duration_ms,
            created_at=m.created_at.isoformat() if m.created_at else None,
        )
        for m in models
    ]


@router.get("/{benchmark_id}/experiments/{experiment_id}", response_model=BenchmarkComparisonResponse)
async def get_experiment(benchmark_id: str, experiment_id: str) -> BenchmarkComparisonResponse:
    """Retrieves an archived benchmark experiment by ID."""
    m = await _repo.get_by_experiment_id(experiment_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{experiment_id}' not found.")

    rows = m.results_summary.get("rows", [])
    base_cmps = m.baseline_comparisons or []

    return BenchmarkComparisonResponse(
        experiment_id=m.experiment_id,
        benchmark_id=m.benchmark_id,
        benchmark_version=m.benchmark_version,
        content_hash_sha256=m.content_hash_sha256,
        split_seed=m.split_seed,
        split_train_ratio=m.split_train_ratio,
        tolerance_days=m.tolerance_days,
        total_benchmark_events=len(m.train_event_ids) + len(m.holdout_event_ids),
        train_events_count=len(m.train_event_ids),
        holdout_events_count=len(m.holdout_event_ids),
        rows=[
            ProfileComparisonRowSchema(
                profile_id=r["profile_id"],
                profile_name=r["profile_name"],
                calibration_sample_size_n=r["calibration_sample_size_n"],
                holdout_sample_size_n=r["holdout_sample_size_n"],
                holdout_precision=r["holdout_precision"],
                holdout_recall=r["holdout_recall"],
                holdout_f1_score=r["holdout_f1_score"],
                holdout_hit_rate_pct=r["holdout_hit_rate_pct"],
                holdout_brier_score=r["holdout_brier_score"],
                holdout_mae_peak_days=r["holdout_mae_peak_days"],
                holdout_median_peak_offset_days=r["holdout_median_peak_offset_days"],
                holdout_p90_peak_offset_days=r["holdout_p90_peak_offset_days"],
                calibration_method=r.get("calibration_method", "isotonic_regression"),
            )
            for r in rows
        ],
        baseline_comparisons=[
            BaselineDeltaSchema(
                profile_id=b["profile_id"],
                baseline_profile_id=b["baseline_profile_id"],
                delta_hit_rate_pct=b["delta_hit_rate_pct"],
                delta_brier_score=b["delta_brier_score"],
                delta_f1_score=b["delta_f1_score"],
                delta_mae_peak_days=b["delta_mae_peak_days"],
                is_statistically_superior=b["is_statistically_superior"],
                p_value=b.get("p_value", 1.0),
                odds_ratio=b.get("odds_ratio", 1.0),
                verdict=b.get("verdict", "EQUIVALENT_OR_INSUFFICIENT_EVIDENCE"),
            )
            for b in base_cmps
        ],
    )


class McNemarTestSchema(BaseModel):
    contingency_table: list[int]
    b_discordant_baseline_only: int
    c_discordant_candidate_only: int
    statistic: float
    p_value: float
    odds_ratio: float
    is_significant: bool


class BootstrapCISchema(BaseModel):
    metric_name: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    confidence_level: float = 0.95
    standard_error: float = 0.0


class ProfileSignificanceSchema(BaseModel):
    profile_id: str
    baseline_profile_id: str
    mcnemar_test: McNemarTestSchema
    brier_permutation_p_value: float
    delta_hit_rate_pct: float
    delta_brier_score: float
    delta_mae_peak_days: float
    bootstrap_cis: dict[str, BootstrapCISchema]
    verdict: str


class ExperimentSignificanceReportResponse(BaseModel):
    experiment_id: str
    benchmark_id: str
    benchmark_version: str
    reports: list[ProfileSignificanceSchema]


@router.get("/{benchmark_id}/experiments/{experiment_id}/significance", response_model=ExperimentSignificanceReportResponse)
async def get_experiment_significance(benchmark_id: str, experiment_id: str) -> ExperimentSignificanceReportResponse:
    """Returns detailed inferential statistical significance analysis for an experiment."""
    m = await _repo.get_by_experiment_id(experiment_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{experiment_id}' not found.")

    sig_reports = m.results_summary.get("significance_reports", [])

    return ExperimentSignificanceReportResponse(
        experiment_id=m.experiment_id,
        benchmark_id=m.benchmark_id,
        benchmark_version=m.benchmark_version,
        reports=[
            ProfileSignificanceSchema(
                profile_id=s["profile_id"],
                baseline_profile_id=s["baseline_profile_id"],
                mcnemar_test=McNemarTestSchema(
                    contingency_table=s["mcnemar_test"]["contingency_table"],
                    b_discordant_baseline_only=s["mcnemar_test"]["b_discordant_baseline_only"],
                    c_discordant_candidate_only=s["mcnemar_test"]["c_discordant_candidate_only"],
                    statistic=s["mcnemar_test"]["statistic"],
                    p_value=s["mcnemar_test"]["p_value"],
                    odds_ratio=s["mcnemar_test"]["odds_ratio"],
                    is_significant=s["mcnemar_test"]["is_significant"],
                ),
                brier_permutation_p_value=s["brier_permutation_p_value"],
                delta_hit_rate_pct=s["delta_hit_rate_pct"],
                delta_brier_score=s["delta_brier_score"],
                delta_mae_peak_days=s["delta_mae_peak_days"],
                bootstrap_cis={
                    k: BootstrapCISchema(
                        metric_name=v["metric_name"],
                        point_estimate=v["point_estimate"],
                        ci_lower=v["ci_lower"],
                        ci_upper=v["ci_upper"],
                        confidence_level=v.get("confidence_level", 0.95),
                        standard_error=v.get("standard_error", 0.0),
                    )
                    for k, v in s.get("bootstrap_cis", {}).items()
                },
                verdict=s["verdict"],
            )
            for s in sig_reports
        ],
    )


@router.get("/{benchmark_id}/calibration-curve", response_model=CalibrationCurveReportResponse)
async def get_calibration_curve(
    benchmark_id: str,
    profile_id: str = Query("parashari_standard_v1"),
    version: str = Query("1.0.0"),
    tolerance_days: int = Query(30),
    seed: int = Query(42),
    train_ratio: float = Query(0.70),
) -> CalibrationCurveReportResponse:
    """Returns fitted calibration curve and Wilson CIs for reliability diagrams."""
    corpus = _registry.get_locked_corpus(benchmark_id, version)
    if not corpus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Corpus '{benchmark_id}' v{version} not found.")

    profile = PARASHARI_STANDARD_PROFILE if profile_id == "parashari_standard_v1" else EMPIRICAL_RESEARCH_PROFILE

    research = ResearchEngine()
    calib = CalibrationEngine()

    from apps.api.domain.research_calibration import BenchmarkDataset
    dataset = BenchmarkDataset(
        dataset_id=corpus.benchmark_id,
        name=corpus.definition.name,
        event_type=corpus.event_type,
        version=corpus.version,
        description="",
        events=corpus.events,
    )
    split = research.split_dataset(dataset, train_ratio=train_ratio, seed=seed)
    train_outcomes = research.run_backtest(split.train_events, profile=profile, tolerance_days=tolerance_days)

    model = calib.fit_isotonic_calibration(
        train_outcomes=train_outcomes,
        dataset_id=corpus.benchmark_id,
        dataset_version=version,
        event_type=corpus.event_type,
        profile_id=profile.profile_id,
        split_seed=seed,
        split_train_ratio=train_ratio,
        tolerance_days=tolerance_days,
    )

    validation = calib.evaluate_holdout_validation(research.run_backtest(split.holdout_events, profile=profile, tolerance_days=tolerance_days), model)

    return CalibrationCurveReportResponse(
        benchmark_id=benchmark_id,
        version=version,
        profile_id=profile_id,
        total_train_n=len(split.train_events),
        brier_score=validation.holdout_brier_score,
        bins=[
            CalibrationCurveBinSchema(
                score_range=f"{p.min_score}-{p.max_score}",
                min_score=p.min_score,
                max_score=p.max_score,
                sample_size_n=p.bin_sample_size_n,
                observed_hits=p.observed_hits,
                empirical_hit_rate_pct=round(p.empirical_hit_rate * 100, 1),
                rate_ci_95=list(p.rate_ci_95),
                has_small_n_warning=p.has_small_n_warning,
            )
            for p in model.isotonic_pools
        ],
    )


class DecisionRecommendationSchema(BaseModel):
    status: str
    recommended_profile_id: str
    baseline_profile_id: str
    confidence_score: float
    key_evidence_drivers: list[str]
    risk_factors: list[str]
    sample_size_adequate: bool
    requires_human_signoff: bool


class ExperimentReportResponse(BaseModel):
    experiment_id: str
    benchmark_id: str
    benchmark_version: str
    decision: DecisionRecommendationSchema
    executive_summary: str
    markdown_content: str
    json_content: dict[str, Any]


@router.get("/{benchmark_id}/experiments/{experiment_id}/decision", response_model=DecisionRecommendationSchema)
async def get_experiment_decision(benchmark_id: str, experiment_id: str) -> DecisionRecommendationSchema:
    """Returns automated scientific decision recommendation for an experiment."""
    m = await _repo.get_by_experiment_id(experiment_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{experiment_id}' not found.")

    corpus = _registry.get_locked_corpus(m.benchmark_id, m.benchmark_version)
    if not corpus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corpus not found.")

    from apps.api.domain.prediction_orchestration import ConsensusProfile
    from apps.api.services.benchmark_runner import BenchmarkRunner
    from apps.api.services.decision_engine import DecisionEngine

    profiles = [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE]
    runner = BenchmarkRunner()
    exp = runner.run_experiment(
        corpus=corpus,
        profiles=profiles,
        baseline_profile_id=m.baseline_profile_id,
        tolerance_days=m.tolerance_days,
        seed=m.split_seed,
        train_ratio=m.split_train_ratio,
    )

    decision_engine = DecisionEngine()
    decision = decision_engine.evaluate_experiment_decision(exp, baseline_profile_id=m.baseline_profile_id)

    return DecisionRecommendationSchema(
        status=decision.status.value,
        recommended_profile_id=decision.recommended_profile_id,
        baseline_profile_id=decision.baseline_profile_id,
        confidence_score=decision.confidence_score,
        key_evidence_drivers=list(decision.key_evidence_drivers),
        risk_factors=list(decision.risk_factors),
        sample_size_adequate=decision.sample_size_adequate,
        requires_human_signoff=decision.requires_human_signoff,
    )


@router.get("/{benchmark_id}/experiments/{experiment_id}/report", response_model=ExperimentReportResponse)
async def get_experiment_report(
    benchmark_id: str,
    experiment_id: str,
    format: str = Query("markdown", description="Report format: markdown or json"),
) -> ExperimentReportResponse:
    """Returns complete scientific research report for an experiment."""
    m = await _repo.get_by_experiment_id(experiment_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{experiment_id}' not found.")

    corpus = _registry.get_locked_corpus(m.benchmark_id, m.benchmark_version)
    if not corpus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corpus not found.")

    from apps.api.services.benchmark_runner import BenchmarkRunner
    from apps.api.services.statistical_report_generator import StatisticalReportGenerator

    profiles = [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE]
    runner = BenchmarkRunner()
    exp = runner.run_experiment(
        corpus=corpus,
        profiles=profiles,
        baseline_profile_id=m.baseline_profile_id,
        tolerance_days=m.tolerance_days,
        seed=m.split_seed,
        train_ratio=m.split_train_ratio,
    )

    gen = StatisticalReportGenerator()
    rep = gen.build_full_report(exp, baseline_profile_id=m.baseline_profile_id)

    return ExperimentReportResponse(
        experiment_id=rep.experiment_id,
        benchmark_id=rep.benchmark_id,
        benchmark_version=rep.benchmark_version,
        decision=DecisionRecommendationSchema(
            status=rep.decision.status.value,
            recommended_profile_id=rep.decision.recommended_profile_id,
            baseline_profile_id=rep.decision.baseline_profile_id,
            confidence_score=rep.decision.confidence_score,
            key_evidence_drivers=list(rep.decision.key_evidence_drivers),
            risk_factors=list(rep.decision.risk_factors),
            sample_size_adequate=rep.decision.sample_size_adequate,
            requires_human_signoff=rep.decision.requires_human_signoff,
        ),
        executive_summary=rep.executive_summary,
        markdown_content=rep.markdown_content,
        json_content=rep.json_content,
    )