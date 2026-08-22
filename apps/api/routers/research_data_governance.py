"""
AstroOS — Research Data Governance & Benchmark Validation Router (Priority 21)

Endpoints:
  - GET  /api/v1/research/datasets
  - GET  /api/v1/research/datasets/{dataset_id}
  - POST /api/v1/research/datasets/{dataset_id}/audit
  - GET  /api/v1/research/benchmarks
  - POST /api/v1/research/benchmarks/run
"""

from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from apps.api.domain.research_data_governance import BenchmarkSuiteType
from apps.api.schemas.research_data_governance import (
    BenchmarkRunResultResponse,
    DatasetQualityAuditReportResponse,
    GovernedDatasetMetadataResponse,
    RunBenchmarkSuiteRequest,
)
from apps.api.services.research_data_governance_engine import ResearchDataGovernanceEngine

router = APIRouter(prefix="/research/data-governance", tags=["Research: Data Governance & Benchmark Layer"])


def _map_audit(a) -> DatasetQualityAuditReportResponse:
    return DatasetQualityAuditReportResponse(
        total_records=a.total_records,
        missing_fields_count=a.missing_fields_count,
        duplicates_count=a.duplicates_count,
        temporal_leakage_detected=a.temporal_leakage_detected,
        label_leakage_detected=a.label_leakage_detected,
        coordinate_integrity_verified=a.coordinate_integrity_verified,
        audit_summary=a.audit_summary,
        status=a.status.value if hasattr(a.status, "value") else str(a.status),
    )


def _map_dataset(d) -> GovernedDatasetMetadataResponse:
    return GovernedDatasetMetadataResponse(
        dataset_id=d.dataset_id,
        name=d.name,
        version=d.version,
        split_type=d.split_type.value if hasattr(d.split_type, "value") else str(d.split_type),
        target_objective=d.target_objective,
        total_records=d.total_records,
        positive_count=d.positive_count,
        negative_count=d.negative_count,
        source_attribution=d.source_attribution,
        license_type=d.license_type,
        sha256_checksum=d.sha256_checksum,
        quality_audit=_map_audit(d.quality_audit),
        created_at=d.created_at,
        is_external_available=d.is_external_available,
        lineage_snapshot_id=d.lineage_snapshot_id,
    )


def _map_benchmark(b) -> BenchmarkRunResultResponse:
    return BenchmarkRunResultResponse(
        run_id=b.run_id,
        suite_type=b.suite_type.value if hasattr(b.suite_type, "value") else str(b.suite_type),
        total_cases_evaluated=b.total_cases_evaluated,
        passed_cases_count=b.passed_cases_count,
        accuracy_score_percent=b.accuracy_score_percent,
        reference_engine_source=b.reference_engine_source,
        is_reference_verified=b.is_reference_verified,
        mean_latency_microseconds=b.mean_latency_microseconds,
        sha256_snapshot_hash=b.sha256_snapshot_hash,
        audit_notes=b.audit_notes,
        executed_at=b.executed_at,
    )


@router.get("/datasets", response_model=List[GovernedDatasetMetadataResponse], status_code=status.HTTP_200_OK)
def list_datasets() -> List[GovernedDatasetMetadataResponse]:
    """Lists all version-controlled, governed research cohort datasets."""
    engine = ResearchDataGovernanceEngine.get_instance()
    return [_map_dataset(d) for d in engine.list_datasets()]


@router.get("/datasets/{dataset_id}", response_model=GovernedDatasetMetadataResponse, status_code=status.HTTP_200_OK)
def get_dataset(dataset_id: str) -> GovernedDatasetMetadataResponse:
    """Retrieves full provenance, license, and quality audit for a governed dataset."""
    engine = ResearchDataGovernanceEngine.get_instance()
    d = engine.get_dataset(dataset_id)
    if not d:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return _map_dataset(d)


@router.post("/datasets/{dataset_id}/audit", response_model=DatasetQualityAuditReportResponse, status_code=status.HTTP_200_OK)
def audit_dataset_quality(dataset_id: str) -> DatasetQualityAuditReportResponse:
    """Executes a deep quality audit on a research dataset for missing data, duplicates, and leakage."""
    engine = ResearchDataGovernanceEngine.get_instance()
    audit = engine.run_dataset_quality_audit(dataset_id)
    return _map_audit(audit)


@router.get("/benchmarks", response_model=List[BenchmarkRunResultResponse], status_code=status.HTTP_200_OK)
def list_benchmark_runs() -> List[BenchmarkRunResultResponse]:
    """Lists all calculation and performance benchmark suite runs."""
    engine = ResearchDataGovernanceEngine.get_instance()
    return [_map_benchmark(b) for b in engine.list_benchmark_runs()]


@router.post("/benchmarks/run", response_model=BenchmarkRunResultResponse, status_code=status.HTTP_200_OK)
def run_benchmark_suite(req: RunBenchmarkSuiteRequest) -> BenchmarkRunResultResponse:
    """Executes a standardized benchmark suite (BM_BALA, BM_ASTAK, BM_DIV, BM_PERF) against canonical references."""
    engine = ResearchDataGovernanceEngine.get_instance()
    try:
        suite = BenchmarkSuiteType(req.suite_type.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid benchmark suite type '{req.suite_type}'.")

    result = engine.run_benchmark_suite(suite)
    return _map_benchmark(result)
