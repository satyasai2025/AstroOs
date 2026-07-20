"""
AstroOS — Batch Job Router (Phase II.4 — Local-First)

Submit large birth-data batches (up to 5000 subjects) for asynchronous
chart-report generation; poll for progress; download the resulting zip.
Runs on the local ``io`` worker pool (apps.api.services.worker_pool) — no
external broker, no Kubernetes.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from apps.api.config import Settings, get_settings
from apps.api.dependencies import get_ephemeris_wrapper, get_worker_pool_manager
from apps.api.schemas.batch import BatchChartReportRequest, BatchSubmitResponse, JobStatusResponse
from apps.api.services.batch_report_service import run_batch_chart_reports
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.worker_pool import JobPriority, JobStatus, WorkerPoolManager

router = APIRouter(prefix="/api/v1/batch", tags=["Batch Jobs"])


@router.post(
    "/chart-reports",
    response_model=BatchSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a batch of births for async chart-report generation (zip, pollable)",
)
async def submit_batch_chart_reports(
    body: BatchChartReportRequest,
    manager: WorkerPoolManager = Depends(get_worker_pool_manager),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    settings: Settings = Depends(get_settings),
) -> BatchSubmitResponse:
    io_pool = manager.pool("io")
    output_dir = Path(settings.BATCH_OUTPUT_DIR)

    job = io_pool.submit(
        run_batch_chart_reports,
        body,
        wrapper,
        output_dir,
        priority=JobPriority.BULK,
        max_retries=0,  # batches are large and partially-idempotent; failures are per-subject, not retried whole
    )
    return BatchSubmitResponse(
        job_id=job.id, pool=io_pool.name, status=job.status, subject_count=len(body.subjects)
    )


@router.get("/{job_id}", response_model=JobStatusResponse, summary="Poll a batch job's status/progress")
async def get_batch_job(
    job_id: str, manager: WorkerPoolManager = Depends(get_worker_pool_manager)
) -> JobStatusResponse:
    job = manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusResponse(**job.to_dict())


@router.get("/{job_id}/download", summary="Download the completed batch's zip archive")
async def download_batch_result(
    job_id: str, manager: WorkerPoolManager = Depends(get_worker_pool_manager)
) -> FileResponse:
    job = manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409, detail=f"Job is not complete yet (status: {job.status})."
        )
    zip_path = Path(job.result["zip_path"])
    if not zip_path.exists():
        raise HTTPException(status_code=410, detail="Result archive is no longer available.")
    return FileResponse(
        path=zip_path, media_type="application/zip", filename=f"astroos-batch-{job_id}.zip"
    )


@router.delete("/{job_id}", summary="Cancel a queued or running batch job")
async def cancel_batch_job(
    job_id: str, manager: WorkerPoolManager = Depends(get_worker_pool_manager)
) -> dict[str, bool]:
    job = manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    pool = manager.pool(job.pool)
    return {"cancelled": pool.cancel(job_id)}
