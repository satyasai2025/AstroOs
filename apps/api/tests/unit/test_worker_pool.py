"""Unit tests for apps/api/services/worker_pool.py (Phase II.4 — local-first)."""

import time

import pytest

from apps.api.services.worker_pool import (
    Job,
    JobCancelled,
    JobPriority,
    JobStatus,
    WorkerPool,
    WorkerPoolManager,
)


def _wait_until(predicate, timeout=5.0, interval=0.02):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


@pytest.fixture()
def pool():
    p = WorkerPool("test", min_workers=1, max_workers=4, autoscale_interval=0.1)
    yield p
    p.shutdown()


def test_job_runs_to_completion(pool):
    job = pool.submit(lambda j: 21 * 2)
    assert _wait_until(lambda: job.status == JobStatus.COMPLETED)
    assert job.result == 42


def test_job_records_error_and_dead_letters_after_retries(pool):
    def boom(j):
        raise ValueError("nope")

    job = pool.submit(boom, max_retries=1, retry_base_delay=0.01)
    assert _wait_until(lambda: job.status == JobStatus.DEAD_LETTER, timeout=5.0)
    assert job.attempt == 2  # initial attempt + 1 retry
    assert "nope" in job.error


def test_job_retries_then_succeeds(pool):
    calls = {"n": 0}

    def flaky(j):
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")
        return "ok"

    job = pool.submit(flaky, max_retries=3, retry_base_delay=0.01)
    assert _wait_until(lambda: job.status == JobStatus.COMPLETED, timeout=5.0)
    assert job.result == "ok"
    assert calls["n"] == 2


def test_interactive_priority_served_before_bulk():
    # Single-worker pool so ordering is deterministic and observable.
    p = WorkerPool("prio", min_workers=1, max_workers=1, autoscale_interval=100)
    order = []
    gate = __import__("threading").Event()

    def blocker(j):
        gate.wait(timeout=2)

    def record(j, name):
        order.append(name)

    try:
        # Occupy the single worker so subsequent submissions queue up.
        first = p.submit(blocker, priority=JobPriority.BULK)
        assert _wait_until(lambda: first.status == JobStatus.RUNNING)

        bulk_job = p.submit(record, "bulk", priority=JobPriority.BULK)
        interactive_job = p.submit(record, "interactive", priority=JobPriority.INTERACTIVE)

        gate.set()  # release the blocker; queued jobs now run in priority order
        assert _wait_until(lambda: bulk_job.status == JobStatus.COMPLETED and interactive_job.status == JobStatus.COMPLETED)
        assert order == ["interactive", "bulk"]
    finally:
        gate.set()
        p.shutdown()


def test_cancel_queued_job_never_runs():
    p = WorkerPool("cancel", min_workers=1, max_workers=1, autoscale_interval=100)
    ran = []
    try:
        blocker_gate = __import__("threading").Event()
        blocker = p.submit(lambda j: blocker_gate.wait(timeout=2))
        assert _wait_until(lambda: blocker.status == JobStatus.RUNNING)

        job = p.submit(lambda j: ran.append(1))
        assert p.cancel(job.id) is True
        blocker_gate.set()
        time.sleep(0.2)
        assert job.status == JobStatus.CANCELLED
        assert ran == []
    finally:
        blocker_gate.set()
        p.shutdown()


def test_running_job_cooperative_cancel():
    p = WorkerPool("coop-cancel", min_workers=1, max_workers=1, autoscale_interval=100)

    def long_job(j):
        for _ in range(50):
            if j.cancel_requested:
                raise JobCancelled()
            time.sleep(0.02)
        return "finished"

    try:
        job = p.submit(long_job)
        assert _wait_until(lambda: job.status == JobStatus.RUNNING)
        assert p.cancel(job.id) is True
        assert _wait_until(lambda: job.status == JobStatus.CANCELLED, timeout=3.0)
    finally:
        p.shutdown()


def test_progress_tracking(pool):
    def with_progress(j):
        for i in range(1, 4):
            j.set_progress(i, 3)
        return "done"

    job = pool.submit(with_progress)
    assert _wait_until(lambda: job.status == JobStatus.COMPLETED)
    assert job.progress_current == 3
    assert job.progress_total == 3


def test_autoscaler_grows_pool_under_backlog():
    p = WorkerPool("scale", min_workers=1, max_workers=4, autoscale_interval=0.05)
    gate = __import__("threading").Event()
    try:
        # Submit more slow jobs than the starting worker count so a backlog forms.
        jobs = [p.submit(lambda j: gate.wait(timeout=3), priority=JobPriority.BULK) for _ in range(6)]
        assert _wait_until(lambda: p._current_size > 1, timeout=3.0)
        assert p._current_size <= p.max_workers
    finally:
        gate.set()
        p.shutdown()


def test_manager_routes_jobs_across_pools():
    manager = WorkerPoolManager(
        cpu_range=(1, 2), io_range=(1, 2), ai_range=(1, 2), autoscale_interval=0.5
    )
    try:
        cpu_job = manager.pool("cpu").submit(lambda j: "cpu-done")
        io_job = manager.pool("io").submit(lambda j: "io-done")
        assert _wait_until(lambda: cpu_job.status == JobStatus.COMPLETED)
        assert _wait_until(lambda: io_job.status == JobStatus.COMPLETED)
        assert manager.get_job(cpu_job.id) is cpu_job
        assert manager.get_job(io_job.id) is io_job
        assert manager.get_job("does-not-exist") is None
        with pytest.raises(KeyError):
            manager.pool("nonexistent")
    finally:
        manager.shutdown()


def test_evict_expired_removes_only_terminal_old_jobs(pool):
    job = pool.submit(lambda j: "ok")
    assert _wait_until(lambda: job.status == JobStatus.COMPLETED)
    # Not expired yet (ttl huge) -> nothing evicted.
    assert pool.evict_expired(ttl_seconds=3600) == 0
    # Force it to look old, then it should be evicted.
    from datetime import datetime, timedelta, timezone
    job.completed_at = datetime.now(timezone.utc) - timedelta(days=2)
    assert pool.evict_expired(ttl_seconds=3600) == 1
    assert pool.get(job.id) is None


def test_job_to_dict_shape():
    job = Job(id="abc", pool="io", priority=JobPriority.BULK, fn=lambda j: None)
    d = job.to_dict()
    assert d["id"] == "abc"
    assert d["pool"] == "io"
    assert d["priority"] == "BULK"
    assert d["status"] == JobStatus.QUEUED
    assert d["progress"] == {"current": 0, "total": 1}
