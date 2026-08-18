"""
AstroOS — Production Governance & Continuous Benchmarking API Router

Endpoints for human reviewer sign-offs, production baseline promotions,
reproducibility audits, and continuous regression analysis.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from apps.api.domain.production_governance import (
    RegressionSeverity,
    SignoffStatus,
)
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.repositories.production_governance_repository import ProductionGovernanceRepository
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.governance_engine import GovernanceEngine

router = APIRouter(prefix="/api/v1/governance", tags=["Production Governance"])

_gov_repo = ProductionGovernanceRepository()
_exp_repo = BenchmarkExperimentRepository()
_registry = BenchmarkRegistry()
_runner = BenchmarkRunner()
_engine = GovernanceEngine(
    governance_repo=_gov_repo,
    experiment_repo=_exp_repo,
    registry=_registry,
    runner=_runner,
)


class SignoffRequestSchema(BaseModel):
    status: str = "APPROVED"  # APPROVED, REJECTED, PENDING
    reviewer_id: str
    notes: str = ""


class SignoffResponseSchema(BaseModel):
    signoff_id: str
    experiment_id: str
    status: str
    reviewer_id: str
    notes: str
    signed_at: str


class PromoteRequestSchema(BaseModel):
    version: str = "1.1.0"
    reviewer_id: str
    notes: str = ""


class ProductionProfileSchema(BaseModel):
    profile_id: str
    version: str
    benchmark_id: str
    is_active_baseline: bool
    promoted_from_experiment_id: Optional[str]
    approved_by: Optional[str]
    promoted_at: Optional[str]
    notes: Optional[str]


class ReproducibilityAuditResponse(BaseModel):
    experiment_id: str
    is_bit_for_bit_identical: bool
    expected_results_hash: str
    actual_results_hash: str
    verified_at: str
    audit_notes: str


class RegressionCheckResponse(BaseModel):
    baseline_experiment_id: str
    candidate_experiment_id: str
    has_regression: bool
    hit_rate_drop_pct: float
    brier_increase: float
    mae_increase_days: float
    reasons: list[str]
    severity: str


@router.post("/experiments/{experiment_id}/signoff", response_model=SignoffResponseSchema)
async def record_experiment_signoff(
    experiment_id: str,
    payload: SignoffRequestSchema,
) -> SignoffResponseSchema:
    """Submits a formal human review sign-off on an experiment."""
    status_enum = SignoffStatus(payload.status.upper())
    signoff = await _gov_repo.record_signoff(
        experiment_id=experiment_id,
        status=status_enum,
        reviewer_id=payload.reviewer_id,
        notes=payload.notes,
    )
    return SignoffResponseSchema(
        signoff_id=signoff.signoff_id,
        experiment_id=signoff.experiment_id,
        status=signoff.status.value,
        reviewer_id=signoff.reviewer_id,
        notes=signoff.notes,
        signed_at=signoff.signed_at.isoformat(),
    )


@router.get("/experiments/{experiment_id}/signoff", response_model=Optional[SignoffResponseSchema])
async def get_experiment_signoff(experiment_id: str) -> Optional[SignoffResponseSchema]:
    """Retrieves the latest human review sign-off for an experiment."""
    signoff = await _gov_repo.get_signoff(experiment_id)
    if not signoff:
        return None
    return SignoffResponseSchema(
        signoff_id=signoff.signoff_id,
        experiment_id=signoff.experiment_id,
        status=signoff.status.value,
        reviewer_id=signoff.reviewer_id,
        notes=signoff.notes,
        signed_at=signoff.signed_at.isoformat(),
    )


@router.post("/experiments/{experiment_id}/promote", response_model=ProductionProfileSchema)
async def promote_experiment_to_production(
    experiment_id: str,
    payload: PromoteRequestSchema,
) -> ProductionProfileSchema:
    """Promotes an approved experiment to become the active production baseline profile."""
    try:
        profile = await _engine.promote_experiment_to_baseline(
            experiment_id=experiment_id,
            version=payload.version,
            reviewer_id=payload.reviewer_id,
            notes=payload.notes,
        )
        return ProductionProfileSchema(
            profile_id=profile.profile_id,
            version=profile.version,
            benchmark_id=profile.benchmark_id,
            is_active_baseline=profile.is_active_baseline,
            promoted_from_experiment_id=profile.promoted_from_experiment_id,
            approved_by=profile.approved_by,
            promoted_at=profile.promoted_at.isoformat() if profile.promoted_at else None,
            notes=profile.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/experiments/{experiment_id}/verify-reproducibility", response_model=ReproducibilityAuditResponse)
async def verify_experiment_reproducibility(experiment_id: str) -> ReproducibilityAuditResponse:
    """Re-executes the experiment pipeline with locked seed to verify bit-for-bit SHA-256 hash equality."""
    try:
        audit = await _engine.verify_reproducibility(experiment_id)
        return ReproducibilityAuditResponse(
            experiment_id=audit.experiment_id,
            is_bit_for_bit_identical=audit.is_bit_for_bit_identical,
            expected_results_hash=audit.expected_results_hash,
            actual_results_hash=audit.actual_results_hash,
            verified_at=audit.verified_at.isoformat(),
            audit_notes=audit.audit_notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/benchmarks/{benchmark_id}/production-profiles", response_model=list[ProductionProfileSchema])
async def list_production_profiles(benchmark_id: str) -> list[ProductionProfileSchema]:
    """Lists all versioned production profiles and active baseline status for a benchmark."""
    profiles = await _gov_repo.list_production_profiles(benchmark_id)
    return [
        ProductionProfileSchema(
            profile_id=p.profile_id,
            version=p.version,
            benchmark_id=p.benchmark_id,
            is_active_baseline=p.is_active_baseline,
            promoted_from_experiment_id=p.promoted_from_experiment_id,
            approved_by=p.approved_by,
            promoted_at=p.promoted_at.isoformat() if p.promoted_at else None,
            notes=p.notes,
        )
        for p in profiles
    ]


@router.get("/benchmarks/{benchmark_id}/regression-check", response_model=RegressionCheckResponse)
async def check_experiment_regression(
    benchmark_id: str,
    base_experiment_id: str = Query(...),
    cand_experiment_id: str = Query(...),
) -> RegressionCheckResponse:
    """Runs automated continuous regression detection between two experiment runs."""
    m_base = await _exp_repo.get_by_experiment_id(base_experiment_id)
    m_cand = await _exp_repo.get_by_experiment_id(cand_experiment_id)

    if not m_base or not m_cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both experiments not found.")

    corpus = _registry.get_locked_corpus(benchmark_id)
    if not corpus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Corpus '{benchmark_id}' not found.")

    from apps.api.domain.prediction_orchestration import (
        EMPIRICAL_RESEARCH_PROFILE,
        PARASHARI_STANDARD_PROFILE,
    )
    profiles = [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE]

    exp_base = _runner.run_experiment(
        corpus=corpus,
        profiles=profiles,
        baseline_profile_id=m_base.baseline_profile_id,
        tolerance_days=m_base.tolerance_days,
        seed=m_base.split_seed,
        train_ratio=m_base.split_train_ratio,
    )

    exp_cand = _runner.run_experiment(
        corpus=corpus,
        profiles=profiles,
        baseline_profile_id=m_cand.baseline_profile_id,
        tolerance_days=m_cand.tolerance_days,
        seed=m_cand.split_seed,
        train_ratio=m_cand.split_train_ratio,
    )

    report = _engine.detect_regression(exp_base, exp_cand)

    return RegressionCheckResponse(
        baseline_experiment_id=report.baseline_experiment_id,
        candidate_experiment_id=report.candidate_experiment_id,
        has_regression=report.has_regression,
        hit_rate_drop_pct=report.hit_rate_drop_pct,
        brier_increase=report.brier_increase,
        mae_increase_days=report.mae_increase_days,
        reasons=list(report.reasons),
        severity=report.severity.value,
    )