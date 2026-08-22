"""
AstroOS — Research Data Governance & Benchmark Validation Schemas (Priority 21)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetQualityAuditReportResponse(BaseModel):
    total_records: int
    missing_fields_count: int
    duplicates_count: int
    temporal_leakage_detected: bool
    label_leakage_detected: bool
    coordinate_integrity_verified: bool
    audit_summary: str
    status: str


class GovernedDatasetMetadataResponse(BaseModel):
    dataset_id: str
    name: str
    version: str
    split_type: str
    target_objective: str
    total_records: int
    positive_count: int
    negative_count: int
    source_attribution: str
    license_type: str
    sha256_checksum: str
    quality_audit: DatasetQualityAuditReportResponse
    created_at: datetime
    is_external_available: bool
    lineage_snapshot_id: str


class RunBenchmarkSuiteRequest(BaseModel):
    suite_type: str = Field(default="BM_BALA", description="Benchmark suite (BM_BALA, BM_ASTAK, BM_DIV, BM_PERF)")


class BenchmarkRunResultResponse(BaseModel):
    run_id: str
    suite_type: str
    total_cases_evaluated: int
    passed_cases_count: int
    accuracy_score_percent: float
    reference_engine_source: str
    is_reference_verified: bool
    mean_latency_microseconds: float
    sha256_snapshot_hash: str
    audit_notes: str
    executed_at: datetime
