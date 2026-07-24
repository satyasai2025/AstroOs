# ADR-WORK-001: Worker Pool Topology — Three Named Thread Pools (cpu/io/ai)

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.4 — Distributed Worker Pools & Auto-Scaling (Local-First)

## Context

Phase II.4 requires background execution for batch workloads (e.g. 1000+ chart reports) without blocking request/response cycles, with separation between CPU-bound, I/O-bound, and AI workloads so a slow AI call cannot starve chart computation. `CLAUDE_START_HERE.md` rules out Celery's usual broker-based topology (Redis/RabbitMQ as a hard requirement) as a default.

## Decision

Three named pools — **cpu**, **io**, **ai** — implemented in `apps/api/services/worker_pool.py`, each a `ThreadPoolExecutor` fed by its own dispatcher thread draining a shared-shape priority queue:

1. **Thread pools, not process pools, for all three.** Swiss Ephemeris calls (pyswisseph, a C extension) release the GIL during computation, so `cpu`-pool work still parallelizes across threads on a single process. This avoids the pickling/IPC overhead and complexity of `ProcessPoolExecutor` for what is, on a single-user local machine, a modest workload. The `pool_kind` is isolated behind the `WorkerPool` class so a process-pool variant remains a future drop-in without touching call sites.
2. **Pool assignment by workload shape, not by literal resource type:**
   - `cpu` — chart/divisional/Shadbala computation-heavy jobs.
   - `io` — batch report generation (dominated by per-subject compute + zip I/O) and anything touching the DB/filesystem in a loop. Batch chart-reports (Phase II.4's flagship endpoint) run here today.
   - `ai` — LLM-backed jobs (Phase II.5 yoga scoring, hypothesis generation), isolated so a slow/rate-limited external call never blocks report batches.
3. **Sizing is local and bounded**, not autoscaled against cluster resources: `WORKER_{CPU,IO,AI}_{MIN,MAX}` in `Settings` (defaults: cpu 1–4, io 2–16, ai 1–4), on the assumption of one machine with a handful of cores. See ADR-WORK-004 (autoscaling).

## Alternatives considered

- **Celery + Redis/RabbitMQ broker** — rejected as the default: introduces a required external process, conflicts with local-first zero-additional-infra goal. Remains a documented upgrade path (ADR-WORK-002) for anyone who deploys AstroOS beyond a single machine — out of this phase's scope per the 2026-07-20 governance decision removing containers/K8s from Phase II.
- **A single shared pool for everything** — rejected: an AI call blocking on a rate limit would starve chart computation and batch jobs; separate pools with independent sizing avoid head-of-line blocking across workload types.
- **`asyncio` tasks instead of threads** — rejected as the sole mechanism: existing engines (`HoroscopeEngine`, `ReportEngine`, Swiss Ephemeris wrapper) are synchronous; wrapping every call site in `asyncio.to_thread` per request already happens for interactive endpoints (see `apps/api/routers/report.py`), but batch jobs need their own lifecycle (retry, priority, cancellation, progress) that a bare `asyncio.Task` doesn't provide out of the box without rebuilding much of what `WorkerPool` already does.

## Consequences

- No new required infrastructure; `pip install`-only, matches the SDK/observability precedent set earlier in Phase II.
- Ceiling is single-machine throughput — acceptable for the local-first single-user target; documented as a scaling boundary, not silently hidden.
- Future multi-machine deployment (if ever approved) can swap the dispatcher's `_enqueue`/`_run_job` internals for a Celery-backed implementation behind the same `WorkerPool.submit()`/`Job` interface without changing router code.

---
*Author: Architecture Office, 2026-07-20*
