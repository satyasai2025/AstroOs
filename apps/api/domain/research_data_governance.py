"""
AstroOS — Research Data Governance, Real-World Cohorts & Benchmark Validation Domain Models (Priority 21)

Defines domain dataclasses for:
  - Governed Research Datasets (RS-MARRIAGE, RS-CAREER, RS-HEALTH, PB-WIKI)
  - Dataset Split Typologies (TRAIN, VALIDATION, HOLDOUT, PROSPECTIVE_BLIND)
  - Rigorous Quality Audits (Leakage detection, temporal integrity, coordinates verification)
  - Benchmark Suites (BM-BALA, BM-ASTAK, BM-DIV, BM-PERF)
  - Benchmark Run Results & Cross-Engine Validation Provenance
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Sequence


class DatasetSplitType(str, Enum):
    TRAIN = "TRAIN"
    VALIDATION = "VALIDATION"
    HOLDOUT = "HOLDOUT"
    PROSPECTIVE_BLIND = "PROSPECTIVE_BLIND"


class DatasetQualityStatus(str, Enum):
    VERIFIED_CLEAN = "VERIFIED_CLEAN"
    LEAKAGE_DETECTED = "LEAKAGE_DETECTED"
    DUPLICATES_REMOVED = "DUPLICATES_REMOVED"
    DATA_INCONSISTENCY = "DATA_INCONSISTENCY"


class BenchmarkSuiteType(str, Enum):
    BM_BALA = "BM_BALA"       # Shadbala & Planetary strength accuracy
    BM_ASTAK = "BM_ASTAK"     # Ashtakavarga 337 bindu checksum & Kakshyas
    BM_DIV = "BM_DIV"         # Divisional Charts accuracy (D9/D10/D60)
    BM_PERF = "BM_PERF"       # High-throughput batch streaming performance


@dataclass(frozen=True)
class DatasetQualityAuditReport:
    """Audit report validating dataset integrity, temporal leakage, and labels."""
    total_records: int
    missing_fields_count: int
    duplicates_count: int
    temporal_leakage_detected: bool
    label_leakage_detected: bool
    coordinate_integrity_verified: bool
    audit_summary: str
    status: DatasetQualityStatus


@dataclass(frozen=True)
class GovernedDatasetMetadata:
    """A version-controlled, governed research cohort dataset."""
    dataset_id: str
    name: str
    version: str
    split_type: DatasetSplitType
    target_objective: str
    total_records: int
    positive_count: int
    negative_count: int
    source_attribution: str
    license_type: str
    sha256_checksum: str
    quality_audit: DatasetQualityAuditReport
    created_at: datetime
    is_external_available: bool = True
    lineage_snapshot_id: str = ""


@dataclass(frozen=True)
class BenchmarkRunResult:
    """Empirical output of an automated calculation or performance benchmark suite."""
    run_id: str
    suite_type: BenchmarkSuiteType
    total_cases_evaluated: int
    passed_cases_count: int
    accuracy_score_percent: float
    reference_engine_source: str
    is_reference_verified: bool
    mean_latency_microseconds: float
    sha256_snapshot_hash: str
    audit_notes: str
    executed_at: datetime
