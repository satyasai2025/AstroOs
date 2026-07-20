"""
AstroOS Worker Pools (Phase II.4 — Local-First)

In-process, dependency-free background job execution for batch workloads
(e.g. "compute 1000 charts and zip the reports"). No Celery, no Redis/RabbitMQ
broker, no Kubernetes HPA — everything here is a single Python process using
`concurrent.futures` and a priority queue, per `CLAUDE_START_HERE.md`.

Design
------
- Three named pools — ``cpu``, ``io``, ``ai`` — each a `ThreadPoolExecutor`
  whose size is grown/shrunk by a local autoscaler based on queue depth
  (bounded by ``WORKER_{POOL}_MIN``/``MAX`` in Settings). Chart computation
  releases the GIL during the C-extension (Swiss Ephemeris) calls, so thread
  pools are appropriate for all three pool types on a single machine; a
  process pool remains a drop-in future option (see ``pool_kind``).
- A single dispatcher thread per pool drains a `PriorityQueue` (interactive
  jobs before bulk jobs; FIFO within the same priority) and submits work to
  that pool's executor, respecting the executor's current size.
- Failed jobs retry with exponential backoff up to ``WORKER_MAX_RETRIES``,
  then move to a dead-letter list — never silently dropped.
- Job records live in memory (mirrors the existing `_import_jobs` pattern in
  ``routers/dataset_import.py``) and are periodically evicted after TTL.
- Prometheus gauges/counters expose queue depth and job outcomes for the
  Phase II.2 observability stack.

This module intentionally has zero new third-party dependencies.
"""

from __future__ import annotations

import heapq
import itertools
import logging
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from typing import Any, Callable, Optional

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)


# ── Metrics ───────────────────────────────────────────────────────────────────

jobs_submitted_total = Counter(
    "worker_jobs_submitted_total", "Jobs submitted", ["pool", "priority"]
)
jobs_completed_total = Counter(
    "worker_jobs_completed_total", "Jobs completed", ["pool", "outcome"]
)
queue_depth = Gauge("worker_queue_depth", "Pending jobs waiting for a worker", ["pool"])
pool_size = Gauge("worker_pool_size", "Current worker count", ["pool"])
job_duration_seconds = Gauge(
    "worker_job_duration_seconds", "Duration of the most recently completed job", ["pool"]
)


# ── Priority & status ───────────────────────────────────────────────────────────

class JobPriority(IntEnum):
    """Lower value = served first. Interactive work preempts bulk batches."""

    INTERACTIVE = 0
    BULK = 10


class JobStatus:
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


_TERMINAL_STATUSES = {
    JobStatus.COMPLETED,
    JobStatus.FAILED,
    JobStatus.DEAD_LETTER,
    JobStatus.CANCELLED,
}


@dataclass
class Job:
    """A unit of background work and its execution record."""

    id: str
    pool: str
    priority: JobPriority
    fn: Callable[..., Any]
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    max_retries: int = 3
    retry_base_delay: float = 1.0

    status: str = JobStatus.QUEUED
    attempt: int = 0
    progress_current: int = 0
    progress_total: int = 1
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancel_requested: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def set_progress(self, current: int, total: Optional[int] = None) -> None:
        with self._lock:
            self.progress_current = current
            if total is not None:
                self.progress_total = total

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "id": self.id,
                "pool": self.pool,
                "priority": self.priority.name,
                "status": self.status,
                "attempt": self.attempt,
                "progress": {"current": self.progress_current, "total": self.progress_total},
                "error": self.error,
                "created_at": self.created_at.isoformat(),
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            }


@dataclass(order=True)
class _QueueEntry:
    priority: int
    seq: int
    job_id: str = field(compare=False)
    not_before: float = field(compare=False, default=0.0)


class JobCancelled(Exception):
    """Raised inside a job function (via `check_cancelled`) to abort early."""


# ── Worker pool ───────────────────────────────────────────────────────────────

class WorkerPool:
    """One named pool: an autoscaled ThreadPoolExecutor fed by a priority queue."""

    def __init__(
        self,
        name: str,
        min_workers: int,
        max_workers: int,
        autoscale_interval: float = 5.0,
    ) -> None:
        self.name = name
        self.min_workers = max(1, min_workers)
        self.max_workers = max(self.min_workers, max_workers)
        self.autoscale_interval = autoscale_interval

        self._executor = ThreadPoolExecutor(
            max_workers=self.min_workers, thread_name_prefix=f"astroos-{name}"
        )
        self._current_size = self.min_workers
        self._jobs: dict[str, Job] = {}
        self._heap: list[_QueueEntry] = []
        self._seq = itertools.count()
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._in_flight = 0
        self._stopped = False

        pool_size.labels(pool=name).set(self._current_size)
        queue_depth.labels(pool=name).set(0)

        self._dispatcher = threading.Thread(
            target=self._dispatch_loop, name=f"astroos-{name}-dispatcher", daemon=True
        )
        self._dispatcher.start()
        self._autoscaler = threading.Thread(
            target=self._autoscale_loop, name=f"astroos-{name}-autoscaler", daemon=True
        )
        self._autoscaler.start()

    # -- submission -----------------------------------------------------------

    def submit(
        self,
        fn: Callable[..., Any],
        *args: Any,
        priority: JobPriority = JobPriority.BULK,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        job_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Job:
        job = Job(
            id=job_id or uuid.uuid4().hex,
            pool=self.name,
            priority=priority,
            fn=fn,
            args=args,
            kwargs=kwargs,
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
        )
        with self._lock:
            self._jobs[job.id] = job
            self._enqueue(job.id, priority, not_before=0.0)
        jobs_submitted_total.labels(pool=self.name, priority=priority.name).inc()
        return job

    def _enqueue(self, job_id: str, priority: JobPriority, not_before: float) -> None:
        with self._lock:
            heapq.heappush(
                self._heap, _QueueEntry(int(priority), next(self._seq), job_id, not_before)
            )
            queue_depth.labels(pool=self.name).set(len(self._heap))
            self._not_empty.notify()

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def list_jobs(self, status: Optional[str] = None) -> list[Job]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        with job._lock:
            if job.status == JobStatus.QUEUED:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now(timezone.utc)
                jobs_completed_total.labels(pool=self.name, outcome="cancelled").inc()
                return True
            if job.status == JobStatus.RUNNING:
                job.cancel_requested = True
                return True
        return False

    # -- dispatch ---------------------------------------------------------------

    def _dispatch_loop(self) -> None:
        while not self._stopped:
            with self._lock:
                while not self._heap and not self._stopped:
                    self._not_empty.wait(timeout=1.0)
                if self._stopped:
                    return
                if self._in_flight >= self._current_size:
                    self._not_empty.wait(timeout=0.05)
                    continue
                entry = self._heap[0]
                now = time.monotonic()
                if entry.not_before > now:
                    self._not_empty.wait(timeout=min(0.5, entry.not_before - now))
                    continue
                heapq.heappop(self._heap)
                queue_depth.labels(pool=self.name).set(len(self._heap))
                job = self._jobs.get(entry.job_id)
                if job is None or job.status == JobStatus.CANCELLED:
                    continue
                self._in_flight += 1
            self._executor.submit(self._run_job, job)

    def _run_job(self, job: Job) -> None:
        with job._lock:
            job.status = JobStatus.RUNNING
            job.attempt += 1
            job.started_at = datetime.now(timezone.utc)
        started = time.perf_counter()
        try:
            result = job.fn(job, *job.args, **job.kwargs)
            with job._lock:
                job.result = result
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
            jobs_completed_total.labels(pool=self.name, outcome="success").inc()
        except JobCancelled:
            with job._lock:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now(timezone.utc)
            jobs_completed_total.labels(pool=self.name, outcome="cancelled").inc()
        except Exception as exc:  # noqa: BLE001 — job errors are data, not process errors
            logger.exception("Job %s failed on pool %s: %s", job.id, self.name, exc)
            retry = job.attempt <= job.max_retries
            with job._lock:
                job.error = f"{type(exc).__name__}: {exc}"
                if retry:
                    job.status = JobStatus.QUEUED
                else:
                    job.status = JobStatus.DEAD_LETTER
                    job.completed_at = datetime.now(timezone.utc)
            if retry:
                delay = job.retry_base_delay * (2 ** (job.attempt - 1))
                self._enqueue(job.id, job.priority, not_before=time.monotonic() + delay)
                jobs_completed_total.labels(pool=self.name, outcome="retry").inc()
            else:
                jobs_completed_total.labels(pool=self.name, outcome="dead_letter").inc()
        finally:
            job_duration_seconds.labels(pool=self.name).set(time.perf_counter() - started)
            with self._lock:
                self._in_flight -= 1
                self._not_empty.notify()

    # -- autoscaling (local, queue-depth-based) ----------------------------------

    def _autoscale_loop(self) -> None:
        while not self._stopped:
            time.sleep(self.autoscale_interval)
            if self._stopped:
                return
            with self._lock:
                depth = len(self._heap)
                busy = self._in_flight
                size = self._current_size
                # Scale up: more pending work than idle capacity can absorb.
                if depth > 0 and busy >= size and size < self.max_workers:
                    new_size = min(self.max_workers, size + max(1, depth // 2))
                # Scale down: idle capacity sitting unused.
                elif depth == 0 and busy < size and size > self.min_workers:
                    new_size = max(self.min_workers, size - 1)
                else:
                    new_size = size
                if new_size != size:
                    self._current_size = new_size
            if new_size != size:
                self._executor._max_workers = new_size  # ThreadPoolExecutor supports growth in place
                pool_size.labels(pool=self.name).set(new_size)
                logger.info(
                    "worker pool rescaled",
                    extra={"pool": self.name, "old_size": size, "new_size": new_size, "queue_depth": depth},
                )

    def evict_expired(self, ttl_seconds: int) -> int:
        """Drop terminal job records older than ``ttl_seconds``. Returns count evicted."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
        with self._lock:
            expired = [
                jid for jid, j in self._jobs.items()
                if j.status in _TERMINAL_STATUSES and j.completed_at and j.completed_at < cutoff
            ]
            for jid in expired:
                del self._jobs[jid]
        return len(expired)

    def shutdown(self) -> None:
        self._stopped = True
        with self._lock:
            self._not_empty.notify_all()
        self._executor.shutdown(wait=False)


# ── Manager (process-wide registry) ──────────────────────────────────────────

class WorkerPoolManager:
    """Owns the cpu/io/ai pools. One instance lives on `app.state`."""

    def __init__(
        self,
        cpu_range: tuple[int, int],
        io_range: tuple[int, int],
        ai_range: tuple[int, int],
        autoscale_interval: float = 5.0,
        job_ttl_seconds: int = 24 * 60 * 60,
    ) -> None:
        self.pools: dict[str, WorkerPool] = {
            "cpu": WorkerPool("cpu", *cpu_range, autoscale_interval),
            "io": WorkerPool("io", *io_range, autoscale_interval),
            "ai": WorkerPool("ai", *ai_range, autoscale_interval),
        }
        self.job_ttl_seconds = job_ttl_seconds
        self._reaper_stop = threading.Event()
        self._reaper = threading.Thread(target=self._reap_loop, daemon=True, name="astroos-job-reaper")
        self._reaper.start()

    def pool(self, name: str) -> WorkerPool:
        if name not in self.pools:
            raise KeyError(f"Unknown worker pool: {name!r}. Valid: {list(self.pools)}")
        return self.pools[name]

    def get_job(self, job_id: str) -> Optional[Job]:
        for p in self.pools.values():
            job = p.get(job_id)
            if job is not None:
                return job
        return None

    def list_all_jobs(self, status: Optional[str] = None) -> list[Job]:
        jobs: list[Job] = []
        for p in self.pools.values():
            jobs.extend(p.list_jobs(status))
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def _reap_loop(self) -> None:
        while not self._reaper_stop.is_set():
            self._reaper_stop.wait(timeout=300)
            if self._reaper_stop.is_set():
                return
            for p in self.pools.values():
                n = p.evict_expired(self.job_ttl_seconds)
                if n:
                    logger.info("evicted expired job records", extra={"pool": p.name, "count": n})

    def shutdown(self) -> None:
        self._reaper_stop.set()
        for p in self.pools.values():
            p.shutdown()
