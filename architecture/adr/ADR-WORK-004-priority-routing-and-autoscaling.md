# ADR-WORK-004: Priority Routing & Local Autoscaling — Queue-Depth-Driven, Bounded

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.4 — Distributed Worker Pools & Auto-Scaling (Local-First)

## Context

Interactive work (a user waiting on a result) and bulk work (a 1000-subject batch) share the same pools. Interactive requests must not queue behind a large batch. Separately, pool size should track load without requiring manual tuning or a Kubernetes HPA (explicitly out of scope — see the 2026-07-20 scope amendment removing containers/K8s from Phase II).

## Decision

### Priority routing
Two levels: `JobPriority.INTERACTIVE` (0) and `JobPriority.BULK` (10) — lower value served first. The dispatcher's priority heap orders strictly by `(priority, submission_sequence)`, so interactive jobs always preempt queued bulk jobs, and ties within a priority resolve FIFO. This is enforced at the pool level, not the job-type level — any submission can request either priority; today, batch report jobs are submitted as `BULK` and nothing yet submits `INTERACTIVE` (reserved for future request-scoped async work, e.g. an interactive "compute while I wait" job offloaded from the request thread).

### Local autoscaling
Each pool runs a dedicated autoscaler thread (`WorkerPool._autoscale_loop`), polling every `WORKER_AUTOSCALE_INTERVAL_SECONDS` (default 5s):
- **Scale up** when `queue_depth > 0` and `in_flight >= current_size` and `current_size < max_workers` — grow by `max(1, queue_depth // 2)`, capped at `max_workers`.
- **Scale down** when `queue_depth == 0` and `in_flight < current_size` and `current_size > min_workers` — shrink by 1 toward `min_workers`.
- Otherwise hold size steady (avoids oscillation on borderline load).

This directly satisfies the Phase II.4 roadmap's "HPA scales workers on queue depth" success criterion, reimplemented locally: the *signal* (queue depth vs in-flight capacity) is the same one a Kubernetes HPA would use against a custom metric; only the *actuator* differs (an in-process `ThreadPoolExecutor` resize instead of a Pod count).

## Alternatives considered

- **More than two priority levels** — rejected for now: no current caller needs finer-grained priority; two levels (interactive/bulk) map directly to the roadmap's stated requirement. Extending `JobPriority` is a non-breaking future addition (it's an `IntEnum`).
- **CPU/memory-based autoscaling** — rejected: queue depth is the leading indicator the roadmap specifies, is cheap to sample, and doesn't require OS-level resource polling.
- **Fixed pool sizes (no autoscaling)** — rejected: would require manual retuning as batch workloads vary in size; defeats the stated Phase II.4 goal.

## Consequences

- Interactive-vs-bulk starvation is prevented by construction (priority heap ordering), verified by `tests/unit/test_worker_pool.py::test_interactive_priority_served_before_bulk`.
- Autoscaling is bounded by `[MIN, MAX]` per pool — never grows unbounded, never shrinks below a floor that would stall a single incoming job.
- Growth uses CPython's `ThreadPoolExecutor` internal lazy-thread-creation behavior (raising `_max_workers` and letting subsequent `submit()` calls spawn threads up to the new cap) rather than replacing the executor — avoids losing in-flight work on a resize. This is noted as an implementation detail tied to `ThreadPoolExecutor`'s internals in `worker_pool.py`'s comments, should be re-verified if the executor implementation ever changes.

---
*Author: Architecture Office, 2026-07-20*
