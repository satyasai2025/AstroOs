"""
AstroOS — Longitudinal Resonance & Cohort Validation Router (Priority 15)

Endpoints:
  - POST /api/v1/research/cohort/evaluate
  - GET  /api/v1/research/cohort/benchmarks
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, status

from apps.api.schemas.cohort_validation import (
    CohortDatasetItem,
    CohortValidationEvaluateRequest,
    CohortValidationReportResponse,
    HypothesisTestResultItem,
)
from apps.api.services.cohort_validation_engine import CohortValidationEngine

router = APIRouter(prefix="/research/cohort", tags=["Research: Longitudinal Cohort Validation & Significance"])


@router.get("/benchmarks", response_model=list[CohortDatasetItem], status_code=status.HTTP_200_OK)
def list_benchmark_cohorts() -> list[CohortDatasetItem]:
    """Lists curated benchmark longitudinal datasets available for statistical validation."""
    datasets = CohortValidationEngine.list_benchmarks()
    return [
        CohortDatasetItem(
            dataset_id=d.dataset_id,
            name=d.name,
            target_objective=d.target_objective,
            total_subjects=d.total_subjects,
            positive_count=d.positive_count,
            negative_count=d.negative_count,
            description=d.description,
        )
        for d in datasets
    ]


@router.post("/evaluate", response_model=CohortValidationReportResponse, status_code=status.HTTP_200_OK)
def evaluate_cohort_significance(req: CohortValidationEvaluateRequest) -> CohortValidationReportResponse:
    """Executes mass statistical evaluation and Monte Carlo permutation hypothesis testing."""
    engine = CohortValidationEngine()
    report = engine.evaluate_cohort(
        dataset_id=req.dataset_id,
        monte_carlo_iterations=req.monte_carlo_iterations,
        random_seed=req.random_seed,
    )

    hyp_items = [
        HypothesisTestResultItem(
            metric_name=h.metric_name,
            observed_value=h.observed_value,
            null_mean=h.null_mean,
            null_std=h.null_std,
            z_score=h.z_score,
            p_value=h.p_value,
            is_statistically_significant=h.is_statistically_significant,
            confidence_interval_95=list(h.confidence_interval_95),
            methodology=h.methodology,
        )
        for h in report.hypothesis_tests
    ]

    return CohortValidationReportResponse(
        report_id=report.report_id,
        dataset_id=report.dataset_id,
        dataset_name=report.dataset_name,
        target_objective=report.target_objective,
        total_subjects_evaluated=report.total_subjects_evaluated,
        positive_prevalence=report.positive_prevalence,
        brier_score=report.brier_score,
        log_loss=report.log_loss,
        roc_auc=report.roc_auc,
        pr_auc=report.pr_auc,
        monte_carlo_iterations=report.monte_carlo_iterations,
        permutation_p_value=report.permutation_p_value,
        null_roc_distribution=list(report.null_roc_distribution),
        hypothesis_tests=hyp_items,
        executive_summary=report.executive_summary,
        publication_provenance=report.publication_provenance,
    )
