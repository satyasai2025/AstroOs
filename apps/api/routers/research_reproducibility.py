"""
AstroOS — Research Reproducibility & Independent Validation Router (Priority 22)

Endpoints:
  - GET  /api/v1/research/reproducibility/manifests
  - GET  /api/v1/research/reproducibility/manifests/{manifest_id}
  - POST /api/v1/research/reproducibility/manifests
  - POST /api/v1/research/reproducibility/reproduce
  - GET  /api/v1/research/reproducibility/audits/{audit_id}
"""

from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from apps.api.schemas.research_reproducibility import (
    CreateRunManifestRequest,
    ImmutableRunManifestResponse,
    IndependentValidationAuditReportResponse,
    MetricDiffItemResponse,
    ReExecuteManifestRequest,
)
from apps.api.services.research_reproducibility_engine import ResearchReproducibilityEngine

router = APIRouter(prefix="/research/reproducibility", tags=["Research: Reproducibility & Independent Validation"])


def _map_manifest(m) -> ImmutableRunManifestResponse:
    return ImmutableRunManifestResponse(
        manifest_id=m.manifest_id,
        target_engine_priority=m.target_engine_priority,
        target_objective=m.target_objective,
        dataset_id=m.dataset_id,
        dataset_sha256_hash=m.dataset_sha256_hash,
        engine_version=m.engine_version,
        astrological_formula=m.astrological_formula,
        frozen_thresholds=m.frozen_thresholds,
        random_seed=m.random_seed,
        monte_carlo_iterations=m.monte_carlo_iterations,
        baseline_metrics=m.baseline_metrics,
        manifest_sha256_hash=m.manifest_sha256_hash,
        created_at=m.created_at,
        parent_lineage_snapshot_id=m.parent_lineage_snapshot_id,
        author=m.author,
    )


def _map_audit(a) -> IndependentValidationAuditReportResponse:
    return IndependentValidationAuditReportResponse(
        audit_id=a.audit_id,
        manifest_id=a.manifest_id,
        target_engine_priority=a.target_engine_priority,
        reproduced_at=a.reproduced_at,
        execution_duration_ms=a.execution_duration_ms,
        metric_diffs=[
            MetricDiffItemResponse(
                metric_name=d.metric_name,
                baseline_value=d.baseline_value,
                reproduced_value=d.reproduced_value,
                absolute_delta=d.absolute_delta,
                is_exact_match=d.is_exact_match,
            )
            for d in a.metric_diffs
        ],
        status=a.status.value if hasattr(a.status, "value") else str(a.status),
        reproducibility_score_percent=a.reproducibility_score_percent,
        independent_repro_snapshot_id=a.independent_repro_snapshot_id,
        audit_summary=a.audit_summary,
    )


@router.get("/manifests", response_model=List[ImmutableRunManifestResponse], status_code=status.HTTP_200_OK)
def list_manifests() -> List[ImmutableRunManifestResponse]:
    """Lists all active immutable research-run execution manifests."""
    engine = ResearchReproducibilityEngine.get_instance()
    return [_map_manifest(m) for m in engine.list_manifests()]


@router.get("/manifests/{manifest_id}", response_model=ImmutableRunManifestResponse, status_code=status.HTTP_200_OK)
def get_manifest(manifest_id: str) -> ImmutableRunManifestResponse:
    """Retrieves full details for a specific frozen execution manifest."""
    engine = ResearchReproducibilityEngine.get_instance()
    m = engine.get_manifest(manifest_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Manifest '{manifest_id}' not found.")
    return _map_manifest(m)


@router.post("/manifests", response_model=ImmutableRunManifestResponse, status_code=status.HTTP_200_OK)
def create_run_manifest(req: CreateRunManifestRequest) -> ImmutableRunManifestResponse:
    """Creates and cryptographically freezes a new execution manifest."""
    engine = ResearchReproducibilityEngine.get_instance()
    m = engine.create_run_manifest(
        target_engine_priority=req.target_engine_priority,
        target_objective=req.target_objective,
        dataset_id=req.dataset_id,
        astrological_formula=req.astrological_formula,
        frozen_thresholds=req.frozen_thresholds,
        random_seed=req.random_seed,
        monte_carlo_iterations=req.monte_carlo_iterations,
        baseline_metrics=req.baseline_metrics,
        author=req.author,
    )
    return _map_manifest(m)


@router.post("/reproduce", response_model=IndependentValidationAuditReportResponse, status_code=status.HTTP_200_OK)
def re_execute_manifest(req: ReExecuteManifestRequest) -> IndependentValidationAuditReportResponse:
    """Independently re-executes computation from frozen manifest parameters and diffs results."""
    engine = ResearchReproducibilityEngine.get_instance()
    audit = engine.re_execute_manifest(req.manifest_id)
    return _map_audit(audit)


@router.get("/audits/{audit_id}", response_model=IndependentValidationAuditReportResponse, status_code=status.HTTP_200_OK)
def get_audit_report(audit_id: str) -> IndependentValidationAuditReportResponse:
    """Retrieves independent execution audit report."""
    engine = ResearchReproducibilityEngine.get_instance()
    audit = engine.get_audit_report(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit report '{audit_id}' not found.")
    return _map_audit(audit)
