"""
AstroOS — Large-Scale Batch Research Optimization Router (Priority 18)

Endpoints:
  - POST /api/v1/research/batch/jobs
  - GET  /api/v1/research/batch/jobs/{job_id}
  - GET  /api/v1/research/batch/jobs/{job_id}/checkpoints
"""

from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, status

from apps.api.schemas.batch_research_optimization import (
    BatchJobCheckpointItem,
    BatchJobReportResponse,
    BatchWorkerMetricsItem,
    SubmitBatchJobRequest,
)
from apps.api.services.batch_research_optimizer import BatchResearchOptimizer

router = APIRouter(prefix="/research/batch", tags=["Research: Large-Scale Distributed Cohort Optimization"])


def _map_report(r) -> BatchJobReportResponse:
    return BatchJobReportResponse(
        job_id=r.job_id,
        dataset_id=r.dataset_id,
        target_objective=r.target_objective,
        status=r.status.value if hasattr(r.status, "value") else str(r.status),
        total_subjects_evaluated=r.total_subjects_evaluated,
        total_runtime_seconds=r.total_runtime_seconds,
        average_throughput_charts_per_sec=r.average_throughput_charts_per_sec,
        cache_hit_rate_percent=r.cache_hit_rate_percent,
        aggregate_brier_score=r.aggregate_brier_score,
        aggregate_log_loss=r.aggregate_log_loss,
        aggregate_roc_auc=r.aggregate_roc_auc,
        aggregate_hit_rate=r.aggregate_hit_rate,
        checkpoints_saved=r.checkpoints_saved,
        worker_metrics=[
            BatchWorkerMetricsItem(
                worker_id=w.worker_id,
                processed_count=w.processed_count,
                active_chunk_index=w.active_chunk_index,
                throughput_charts_per_sec=w.throughput_charts_per_sec,
                memory_mb=w.memory_mb,
                cpu_utilization_percent=w.cpu_utilization_percent,
            )
            for w in r.worker_metrics
        ],
        started_at=r.started_at,
        completed_at=r.completed_at,
    )


@router.post("/jobs", response_model=BatchJobReportResponse, status_code=status.HTTP_200_OK)
def submit_batch_job(req: SubmitBatchJobRequest) -> BatchJobReportResponse:
    """Submits and executes a high-throughput parallel chunked batch research cohort job."""
    optimizer = BatchResearchOptimizer.get_instance()
    report = optimizer.submit_and_execute_job(
        dataset_id=req.dataset_id,
        target_objective=req.target_objective,
        total_subjects_target=req.total_subjects_target,
        chunk_size=req.chunk_size,
        max_workers=req.max_workers,
        enable_ephemeris_cache=req.enable_ephemeris_cache,
        checkpoint_interval_chunks=req.checkpoint_interval_chunks,
        monte_carlo_permutations=req.monte_carlo_permutations,
    )
    return _map_report(report)


@router.get("/jobs/{job_id}", response_model=BatchJobReportResponse, status_code=status.HTTP_200_OK)
def get_batch_job(job_id: str) -> BatchJobReportResponse:
    """Retrieves execution status and aggregated metrics for a batch research job."""
    optimizer = BatchResearchOptimizer.get_instance()
    report = optimizer.get_job_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Batch job '{job_id}' not found.")
    return _map_report(report)


@router.get("/jobs/{job_id}/checkpoints", response_model=List[BatchJobCheckpointItem], status_code=status.HTTP_200_OK)
def list_job_checkpoints(job_id: str) -> List[BatchJobCheckpointItem]:
    """Lists tamper-evident SHA-256 checkpoints saved during the batch job execution."""
    optimizer = BatchResearchOptimizer.get_instance()
    checkpoints = optimizer.list_checkpoints(job_id)
    return [
        BatchJobCheckpointItem(
            checkpoint_id=c.checkpoint_id,
            job_id=c.job_id,
            chunk_index=c.chunk_index,
            processed_subjects=c.processed_subjects,
            running_brier_sum=c.running_brier_sum,
            running_log_loss_sum=c.running_log_loss_sum,
            running_hits_count=c.running_hits_count,
            checkpoint_sha256_hash=c.checkpoint_sha256_hash,
            timestamp=c.timestamp,
        )
        for c in checkpoints
    ]
