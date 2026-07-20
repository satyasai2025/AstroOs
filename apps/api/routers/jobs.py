"""
AstroOS — Job Monitoring Router (Phase II.4 — Local-First)

JSON API plus a small self-refreshing HTML dashboard over the worker pools
(apps.api.services.worker_pool) — a local, dependency-free alternative to
Celery Flower. Read-only aside from cancel.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from apps.api.dependencies import get_worker_pool_manager
from apps.api.schemas.batch import JobStatusResponse
from apps.api.services.worker_pool import WorkerPoolManager

router = APIRouter(prefix="/api/v1/jobs", tags=["Job Monitoring"])


@router.get("", response_model=list[JobStatusResponse], summary="List jobs across all worker pools")
async def list_jobs(
    pool: str | None = None,
    status: str | None = None,
    manager: WorkerPoolManager = Depends(get_worker_pool_manager),
) -> list[JobStatusResponse]:
    jobs = manager.pool(pool).list_jobs(status) if pool else manager.list_all_jobs(status)
    return [JobStatusResponse(**j.to_dict()) for j in jobs]


@router.get("/pools", summary="Current size/queue-depth snapshot for each worker pool")
async def list_pools(manager: WorkerPoolManager = Depends(get_worker_pool_manager)) -> dict:
    return {
        name: {
            "current_size": p._current_size,
            "min_workers": p.min_workers,
            "max_workers": p.max_workers,
            "queue_depth": len(p._heap),
            "in_flight": p._in_flight,
            "job_count": len(p._jobs),
        }
        for name, p in manager.pools.items()
    }


@router.get("/{job_id}", response_model=JobStatusResponse, summary="Get a single job's status")
async def get_job(
    job_id: str, manager: WorkerPoolManager = Depends(get_worker_pool_manager)
) -> JobStatusResponse:
    job = manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusResponse(**job.to_dict())


@router.get("/monitor/html", response_class=HTMLResponse, summary="Local job monitoring dashboard")
async def monitor_html(manager: WorkerPoolManager = Depends(get_worker_pool_manager)) -> str:
    pools_html = "".join(
        f'<div class="pool"><b>{name}</b> — size {p._current_size} '
        f'(min {p.min_workers}/max {p.max_workers}) · queue {len(p._heap)} · in-flight {p._in_flight}</div>'
        for name, p in manager.pools.items()
    )
    jobs = manager.list_all_jobs()[:200]
    rows = "".join(
        f'<tr><td>{j.id[:8]}</td><td>{j.pool}</td><td>{j.priority.name}</td>'
        f'<td class="status-{j.status}">{j.status}</td><td>{j.progress_current}/{j.progress_total}</td>'
        f'<td>{j.attempt}</td><td>{(j.error or "")[:80]}</td></tr>'
        for j in jobs
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="5">
<title>AstroOS Job Monitor</title>
<style>
body {{ font-family: -apple-system, sans-serif; background: #f8fafc; color: #1e293b; padding: 24px; }}
h1 {{ font-size: 20px; }}
.pool {{ display: inline-block; margin: 4px 12px 4px 0; padding: 8px 12px; background: #fff;
  border: 1px solid #e2e8f0; border-radius: 8px; font-size: 13px; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 16px; font-size: 13px; }}
th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid #e2e8f0; }}
th {{ background: #f1f5f9; }}
.status-completed {{ color: #16a34a; font-weight: 600; }}
.status-failed, .status-dead_letter {{ color: #dc2626; font-weight: 600; }}
.status-running {{ color: #2563eb; font-weight: 600; }}
.status-queued {{ color: #64748b; }}
</style></head>
<body>
<h1>AstroOS Job Monitor (local, refreshes every 5s)</h1>
<div>{pools_html}</div>
<table><thead><tr><th>Job</th><th>Pool</th><th>Priority</th><th>Status</th>
<th>Progress</th><th>Attempt</th><th>Error</th></tr></thead>
<tbody>{rows}</tbody></table>
</body></html>"""
