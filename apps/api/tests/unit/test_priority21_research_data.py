"""
Unit & Integration Tests for Priority 21 — Research Data Governance, Real-World Cohorts & Benchmark Validation Layer
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.domain.research_data_governance import (
    BenchmarkSuiteType,
    DatasetQualityStatus,
    DatasetSplitType,
)
from apps.api.main import app
from apps.api.services.research_data_governance_engine import ResearchDataGovernanceEngine


def test_research_data_governance_engine_datasets_and_benchmarks():
    """Verify ResearchDataGovernanceEngine lists datasets, performs audits, and runs benchmark suites."""
    engine = ResearchDataGovernanceEngine.get_instance()

    # 1. Verify Dataset Governance
    datasets = engine.list_datasets()
    assert len(datasets) >= 4
    m250 = engine.get_dataset("RS-MARRIAGE-250")
    assert m250 is not None
    assert m250.split_type == DatasetSplitType.TRAIN
    assert m250.quality_audit.status == DatasetQualityStatus.VERIFIED_CLEAN
    assert len(m250.sha256_checksum) == 64

    # Verify External Not Available Explicit Mark
    pb_wiki = engine.get_dataset("PB-WIKI-GOLDEN")
    assert pb_wiki is not None
    assert pb_wiki.is_external_available is False

    # 2. Run Quality Audit
    audit = engine.run_dataset_quality_audit("RS-MARRIAGE-250")
    assert audit.status == DatasetQualityStatus.VERIFIED_CLEAN
    assert audit.temporal_leakage_detected is False

    # 3. Run Benchmark Suites
    bm_bala = engine.run_benchmark_suite(BenchmarkSuiteType.BM_BALA)
    assert bm_bala.accuracy_score_percent == 100.0
    assert bm_bala.is_reference_verified is True
    assert bm_bala.passed_cases_count == 100

    bm_astak = engine.run_benchmark_suite(BenchmarkSuiteType.BM_ASTAK)
    assert bm_astak.accuracy_score_percent == 100.0
    assert bm_astak.passed_cases_count == 50

    bm_div = engine.run_benchmark_suite(BenchmarkSuiteType.BM_DIV)
    assert bm_div.accuracy_score_percent == 100.0
    assert bm_div.passed_cases_count == 75


def test_research_data_governance_fastapi_endpoints():
    """Verify FastAPI router endpoints for dataset governance and benchmark suites."""
    client = TestClient(app)

    # 1. List Datasets
    res_ds = client.get("/api/v1/research/data-governance/datasets")
    assert res_ds.status_code == 200
    data_ds = res_ds.json()
    assert len(data_ds) >= 4

    # 2. Get Specific Dataset
    res_m250 = client.get("/api/v1/research/data-governance/datasets/RS-MARRIAGE-250")
    assert res_m250.status_code == 200
    data_m250 = res_m250.json()
    assert data_m250["dataset_id"] == "RS-MARRIAGE-250"
    assert data_m250["quality_audit"]["status"] == "VERIFIED_CLEAN"

    # 3. Run Benchmark Suite
    res_bm = client.post(
        "/api/v1/research/data-governance/benchmarks/run",
        json={"suite_type": "BM_ASTAK"},
    )
    assert res_bm.status_code == 200
    data_bm = res_bm.json()
    assert data_bm["suite_type"] == "BM_ASTAK"
    assert data_bm["accuracy_score_percent"] == 100.0
    assert data_bm["is_reference_verified"] is True
