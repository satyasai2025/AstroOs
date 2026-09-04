"""
AstroOS — Hypothesis-First Statistical Sweeps API Router (Module 17, Phase 2)

Endpoints:
  GET  /api/v1/research/sweeps/standard-hypotheses
  POST /api/v1/research/sweeps/evaluate-hypothesis
  POST /api/v1/research/sweeps/multi-sweep
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, status

from apps.api.domain.statistical_sweep import (
    AstrologicalExposureRule,
    ContingencyTable2x2,
    HypothesisCategory,
    HypothesisDefinition,
    HypothesisStatisticalResult,
)
from apps.api.schemas.statistical_sweep import (
    CohortPipelineRequest,
    CohortPipelineResponse,
    ContingencyTableSchema,
    ExposureRuleSchema,
    HypothesisDefinitionSchema,
    HypothesisEvaluationRequest,
    HypothesisResultSchema,
    MultiSweepRequest,
    MultiSweepResponse,
    StandardHypothesesResponse,
)
from apps.api.services.statistical_sweep_engine import StatisticalSweepEngine

router = APIRouter(prefix="/research/sweeps", tags=["Research Hypothesis Sweeps"])


def _to_schema_hypothesis(h: HypothesisDefinition) -> HypothesisDefinitionSchema:
    return HypothesisDefinitionSchema(
        id=h.id,
        title=h.title,
        category=h.category.value,
        exposure_rule=ExposureRuleSchema(
            rule_type=h.exposure_rule.rule_type,
            parameters=h.exposure_rule.parameters,
            description=h.exposure_rule.description,
        ),
        target_outcome=h.target_outcome,
        description=h.description,
        pre_registered=h.pre_registered,
        classical_reference=h.classical_reference,
    )


def _to_domain_hypothesis(s: HypothesisDefinitionSchema) -> HypothesisDefinition:
    cat_val = s.category.lower()
    cat_enum = next((c for c in HypothesisCategory if c.value == cat_val), HypothesisCategory.GENERAL)
    return HypothesisDefinition(
        id=s.id,
        title=s.title,
        category=cat_enum,
        exposure_rule=AstrologicalExposureRule(
            rule_type=s.exposure_rule.rule_type,
            parameters=s.exposure_rule.parameters,
            description=s.exposure_rule.description or "",
        ),
        target_outcome=s.target_outcome,
        description=s.description,
        pre_registered=s.pre_registered,
        classical_reference=s.classical_reference,
    )


def _to_schema_result(res: HypothesisStatisticalResult) -> HypothesisResultSchema:
    tbl = res.contingency_table
    return HypothesisResultSchema(
        hypothesis=_to_schema_hypothesis(res.hypothesis),
        contingency_table=ContingencyTableSchema(
            a_exposed_cases=tbl.a_exposed_cases,
            b_exposed_controls=tbl.b_exposed_controls,
            c_unexposed_cases=tbl.c_unexposed_cases,
            d_unexposed_controls=tbl.d_unexposed_controls,
            total_n=tbl.total_n,
            total_exposed=tbl.total_exposed,
            total_unexposed=tbl.total_unexposed,
            total_cases=tbl.total_cases,
            total_controls=tbl.total_controls,
            exposure_rate_cases=tbl.exposure_rate_cases,
            exposure_rate_controls=tbl.exposure_rate_controls,
        ),
        sample_size_n=res.sample_size_n,
        odds_ratio=res.odds_ratio,
        odds_ratio_ci_lower=res.odds_ratio_ci_lower,
        odds_ratio_ci_upper=res.odds_ratio_ci_upper,
        relative_risk=res.relative_risk,
        relative_risk_ci_lower=res.relative_risk_ci_lower,
        relative_risk_ci_upper=res.relative_risk_ci_upper,
        cohen_w_effect_size=res.cohen_w_effect_size,
        cramers_v=res.cramers_v,
        chi_square_stat=res.chi_square_stat,
        chi_square_p_value=res.chi_square_p_value,
        fisher_exact_p_value=res.fisher_exact_p_value,
        is_significant_nominal=res.is_significant_nominal,
        bonferroni_adjusted_alpha=res.bonferroni_adjusted_alpha,
        is_significant_bonferroni=res.is_significant_bonferroni,
        fdr_q_value=res.fdr_q_value,
        is_significant_fdr=res.is_significant_fdr,
        has_small_sample_warning=res.has_small_sample_warning,
        statistical_power_estimate=res.statistical_power_estimate,
        verdict=res.verdict.value,
        audit_trace=res.audit_trace,
    )


@router.get("/standard-hypotheses", response_model=StandardHypothesesResponse)
async def get_standard_hypotheses() -> StandardHypothesesResponse:
    """Returns curated library of classical pre-registered hypotheses."""
    engine = StatisticalSweepEngine()
    hypotheses = engine.get_standard_hypotheses()
    return StandardHypothesesResponse(
        total_count=len(hypotheses),
        hypotheses=[_to_schema_hypothesis(h) for h in hypotheses],
    )


@router.post("/evaluate-hypothesis", response_model=HypothesisResultSchema)
async def evaluate_single_hypothesis(body: HypothesisEvaluationRequest) -> HypothesisResultSchema:
    """
    Evaluates a single hypothesis using a provided 2x2 contingency table or cohort dataset.
    """
    engine = StatisticalSweepEngine()

    # Resolve hypothesis definition
    hypothesis: Optional[HypothesisDefinition] = None
    if body.hypothesis:
        hypothesis = _to_domain_hypothesis(body.hypothesis)
    elif body.hypothesis_id:
        standards = engine.get_standard_hypotheses()
        for std in standards:
            if std.id == body.hypothesis_id:
                hypothesis = std
                break

    if not hypothesis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either hypothesis or valid hypothesis_id must be provided.",
        )

    # Resolve contingency table
    if body.contingency_table:
        t = body.contingency_table
        table = ContingencyTable2x2(
            a_exposed_cases=t.a_exposed_cases,
            b_exposed_controls=t.b_exposed_controls,
            c_unexposed_cases=t.c_unexposed_cases,
            d_unexposed_controls=t.d_unexposed_controls,
        )
    elif body.cohort_records:
        table = engine.build_contingency_table(body.cohort_records, hypothesis)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either contingency_table or cohort_records must be provided.",
        )

    result = engine.evaluate_hypothesis(
        hypothesis=hypothesis,
        table=table,
        total_hypotheses_in_sweep=body.total_hypotheses_in_sweep,
        nominal_alpha=body.nominal_alpha,
    )

    return _to_schema_result(result)


@router.post("/multi-sweep", response_model=MultiSweepResponse)
async def run_multi_hypothesis_sweep(body: MultiSweepRequest) -> MultiSweepResponse:
    """
    Executes a battery of hypothesis sweeps over a cohort dataset with
    Bonferroni and Benjamini-Hochberg FDR adjustments.
    """
    engine = StatisticalSweepEngine()

    hypotheses_to_test: list[HypothesisDefinition] = []
    standards = engine.get_standard_hypotheses()

    if body.hypothesis_ids:
        id_set = set(body.hypothesis_ids)
        hypotheses_to_test.extend([h for h in standards if h.id in id_set])

    if body.custom_hypotheses:
        hypotheses_to_test.extend([_to_domain_hypothesis(h) for h in body.custom_hypotheses])

    if not hypotheses_to_test:
        # Default: test all standard hypotheses
        hypotheses_to_test = standards

    report = engine.run_multi_hypothesis_sweep(
        cohort_tag=body.cohort_tag,
        cohort_records=body.cohort_records,
        hypotheses=hypotheses_to_test,
        nominal_alpha=body.nominal_alpha,
    )

    return MultiSweepResponse(
        sweep_id=report.sweep_id,
        cohort_tag=report.cohort_tag,
        total_cohort_size=report.total_cohort_size,
        hypotheses_tested_count=report.hypotheses_tested_count,
        bonferroni_alpha=report.bonferroni_alpha,
        nominal_significant_count=report.nominal_significant_count,
        fdr_significant_count=report.fdr_significant_count,
        bonferroni_significant_count=report.bonferroni_significant_count,
        results=[_to_schema_result(r) for r in report.results],
        generated_at=report.generated_at,
    )


@router.post("/pipeline-run", response_model=CohortPipelineResponse)
async def run_cohort_research_pipeline(body: CohortPipelineRequest) -> CohortPipelineResponse:
    """
    Executes the full 6-stage end-to-end scientific cohort research pipeline:
      Stage 1: Cohort Ingestion
      Stage 2: Validation & Deduplication (Rodden rating filter AA/A/B, coordinate QC)
      Stage 3: Batch Chart Generation (Swiss Ephemeris Lahiri ayanamsa)
      Stage 4: Astrological Feature Extraction
      Stage 5: Statistical Hypotheses Testing (2x2 contingency, Odds Ratio, Yates Chi2, Fisher Exact, FDR)
      Stage 6: Comprehensive Results & Verification Report
    """
    from apps.api.services.statistical_sweep_engine import CohortPipelineOrchestrator
    from apps.api.schemas.statistical_sweep import (
        Stage1IngestionSchema,
        Stage2ValidationSchema,
        Stage3BatchChartSchema,
        Stage4FeatureExtractionSchema,
        Stage5HypothesisSweepSchema,
    )

    orchestrator = CohortPipelineOrchestrator()
    standards = StatisticalSweepEngine().get_standard_hypotheses()
    hypotheses_to_test: list[HypothesisDefinition] = []

    if body.hypothesis_ids:
        id_set = set(body.hypothesis_ids)
        hypotheses_to_test.extend([h for h in standards if h.id in id_set])

    if body.custom_hypotheses:
        hypotheses_to_test.extend([_to_domain_hypothesis(h) for h in body.custom_hypotheses])

    if not hypotheses_to_test:
        hypotheses_to_test = standards

    pipeline_result = orchestrator.run_pipeline(
        cohort_tag=body.cohort_tag,
        raw_records=body.raw_records,
        min_rodden_rating=body.min_rodden_rating,
        hypotheses=hypotheses_to_test,
        nominal_alpha=body.nominal_alpha,
    )

    sweep = pipeline_result.sweep_report
    sweep_schema = MultiSweepResponse(
        sweep_id=sweep.sweep_id,
        cohort_tag=sweep.cohort_tag,
        total_cohort_size=sweep.total_cohort_size,
        hypotheses_tested_count=sweep.hypotheses_tested_count,
        bonferroni_alpha=sweep.bonferroni_alpha,
        nominal_significant_count=sweep.nominal_significant_count,
        fdr_significant_count=sweep.fdr_significant_count,
        bonferroni_significant_count=sweep.bonferroni_significant_count,
        results=[_to_schema_result(r) for r in sweep.results],
        generated_at=sweep.generated_at,
    )

    return CohortPipelineResponse(
        pipeline_run_id=pipeline_result.pipeline_run_id,
        cohort_tag=pipeline_result.cohort_tag,
        stage_1_ingestion=Stage1IngestionSchema(
            total_received=pipeline_result.stage_1_ingestion.total_received,
            total_accepted=pipeline_result.stage_1_ingestion.total_accepted,
            total_rejected=pipeline_result.stage_1_ingestion.total_rejected,
            duplicates_count=pipeline_result.stage_1_ingestion.duplicates_count,
            provenance_hash_sha256=pipeline_result.stage_1_ingestion.provenance_hash_sha256,
        ),
        stage_2_validation=Stage2ValidationSchema(
            accepted_events_count=pipeline_result.stage_2_validation.accepted_events_count,
            rejected_events_count=pipeline_result.stage_2_validation.rejected_events_count,
            rejections_by_code=pipeline_result.stage_2_validation.rejections_by_code,
        ),
        stage_3_batch_charts=Stage3BatchChartSchema(
            generated_charts_count=pipeline_result.stage_3_batch_charts.generated_charts_count,
            calculation_time_ms=pipeline_result.stage_3_batch_charts.calculation_time_ms,
            ephemeris_ayanamsa=pipeline_result.stage_3_batch_charts.ephemeris_ayanamsa,
        ),
        stage_4_feature_extraction=Stage4FeatureExtractionSchema(
            subjects_profiled_count=pipeline_result.stage_4_feature_extraction.subjects_profiled_count,
            features_per_subject_count=pipeline_result.stage_4_feature_extraction.features_per_subject_count,
            sample_features=pipeline_result.stage_4_feature_extraction.sample_features,
        ),
        stage_5_hypothesis_sweep=Stage5HypothesisSweepSchema(
            hypotheses_tested_count=pipeline_result.stage_5_hypothesis_sweep.hypotheses_tested_count,
            bonferroni_adjusted_alpha=pipeline_result.stage_5_hypothesis_sweep.bonferroni_adjusted_alpha,
            nominal_significant_count=pipeline_result.stage_5_hypothesis_sweep.nominal_significant_count,
            fdr_significant_count=pipeline_result.stage_5_hypothesis_sweep.fdr_significant_count,
            bonferroni_significant_count=pipeline_result.stage_5_hypothesis_sweep.bonferroni_significant_count,
        ),
        sweep_report=sweep_schema,
        executed_at=pipeline_result.executed_at,
    )


@router.get("/benchmark-datasets")
async def get_benchmark_datasets() -> dict[str, Any]:
    """
    Returns pre-registered gold-standard benchmark datasets with authentic
    statistical properties for empirical hypothesis sweeps.
    """
    engine = StatisticalSweepEngine()
    cohorts = engine.get_benchmark_cohorts()
    return {
        "total_datasets": len(cohorts),
        "datasets": cohorts,
        "epistemological_notice": (
            "Statistical association measures observational correlation across cohort charts "
            "and does not establish causal efficacy or direct planetary causation."
        ),
    }


@router.post("/cohort-sweep")
async def run_cohort_dataset_sweep(
    body: dict[str, Any],
) -> dict[str, Any]:
    """
    Executes a complete statistical sweep across selected cohort dataset records
    and target classical hypotheses with Benjamini-Hochberg FDR adjustments.
    """
    engine = StatisticalSweepEngine()
    cohort_tag = str(body.get("cohort_tag", "Empirical_Cohort"))
    records = body.get("cohort_records", [])

    # If no records provided directly, try loading from benchmark cohort
    cohort_id = body.get("cohort_id")
    if not records and cohort_id:
        benchmarks = engine.get_benchmark_cohorts()
        matched = next((b for b in benchmarks if b["cohort_id"] == cohort_id), None)
        if matched:
            records = matched["records"]
            cohort_tag = matched["title"]

    if not records:
        # Fallback to first benchmark cohort
        benchmarks = engine.get_benchmark_cohorts()
        if benchmarks:
            records = benchmarks[0]["records"]
            cohort_tag = benchmarks[0]["title"]

    # Filter hypotheses
    standards = engine.get_standard_hypotheses()
    hyp_ids = body.get("hypothesis_ids")
    category_filter = body.get("category")

    if hyp_ids:
        id_set = set(hyp_ids)
        hypotheses_to_test = [h for h in standards if h.id in id_set]
    elif category_filter:
        hypotheses_to_test = [h for h in standards if h.category.value.lower() == str(category_filter).lower()]
    else:
        hypotheses_to_test = standards

    alpha = float(body.get("nominal_alpha", 0.05))
    report = engine.run_multi_hypothesis_sweep(
        cohort_tag=cohort_tag,
        cohort_records=records,
        hypotheses=hypotheses_to_test,
        nominal_alpha=alpha,
    )

    return {
        "sweep_id": report.sweep_id,
        "cohort_tag": report.cohort_tag,
        "total_cohort_size": report.total_cohort_size,
        "hypotheses_tested_count": report.hypotheses_tested_count,
        "bonferroni_alpha": report.bonferroni_alpha,
        "nominal_significant_count": report.nominal_significant_count,
        "fdr_significant_count": report.fdr_significant_count,
        "bonferroni_significant_count": report.bonferroni_significant_count,
        "results": [_to_schema_result(r).model_dump() for r in report.results],
        "generated_at": report.generated_at,
        "epistemological_disclaimer": (
            "Scientific Rigor Notice: All computed Odds Ratios, Relative Risks, Chi-Square, "
            "and Fisher Exact metrics quantify statistical association within the observational sample. "
            "Statistical association does NOT imply physical or astrological causation."
        ),
    }

