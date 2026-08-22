"""
Unit & Integration Tests for Priority 18 — Large-Scale Distributed / Local Cohort Research Optimization Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.domain.batch_research_optimization import BatchJobStatus
from apps.api.main import app
from apps.api.services.batch_research_optimizer import BatchResearchOptimizer


def test_batch_research_optimizer_chunking_and_checkpointing():
    """Verify BatchResearchOptimizer executes chunked parallel batch run, creates checkpoints, and tracks worker telemetry."""
    optimizer = BatchResearchOptimizer.get_instance()

    report = optimizer.submit_and_execute_job(
        dataset_id="ds-marriage-28",
        target_objective="marriage",
        total_subjects_target=750,
        chunk_size=250,
        max_workers=3,
        enable_ephemeris_cache=True,
        checkpoint_interval_chunks=1,
        monte_carlo_permutations=20,
    )

    assert report is not None
    assert report.status == BatchJobStatus.COMPLETED
    assert report.total_subjects_evaluated == 750
    assert report.average_throughput_charts_per_sec > 0.0
    assert report.cache_hit_rate_percent == 94.2
    assert report.aggregate_brier_score > 0.0
    assert report.aggregate_roc_auc >= 0.80
    assert report.checkpoints_saved >= 3
    assert len(report.worker_metrics) == 3

    # Verify Checkpoints
    checkpoints = optimizer.list_checkpoints(report.job_id)
    assert len(checkpoints) >= 3
    assert all(len(c.checkpoint_sha256_hash) == 64 for c in checkpoints)


def test_batch_research_optimizer_fastapi_endpoints():
    """Verify FastAPI router endpoints for submitting and monitoring batch research jobs."""
    client = TestClient(app)

    # 1. Submit Batch Job
    res_submit = client.post(
        "/api/v1/research/batch/jobs",
        json={
            "dataset_id": "ds-marriage-28",
            "target_objective": "marriage",
            "total_subjects_target": 500,
            "chunk_size": 250,
            "max_workers": 2,
            "enable_ephemeris_cache": True,
            "checkpoint_interval_chunks": 1,
            "monte_carlo_permutations": 20,
        },
    )
    assert res_submit.status_code == 200
    data_submit = res_submit.json()
    job_id = data_submit["job_id"]
    assert data_submit["status"] == "COMPLETED"
    assert data_submit["total_subjects_evaluated"] == 500
    assert len(data_submit["worker_metrics"]) == 2

    # 2. Get Batch Job
    res_get = client.get(f"/api/v1/research/batch/jobs/{job_id}")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["job_id"] == job_id
    assert data_get["total_subjects_evaluated"] == 500

    # 3. List Checkpoints
    res_chk = client.get(f"/api/v1/research/batch/jobs/{job_id}/checkpoints")
    assert res_chk.status_code == 200
    data_chk = res_chk.json()
    assert len(data_chk) >= 2
    assert all(len(c["checkpoint_sha256_hash"]) == 64 for c in data_chk)
