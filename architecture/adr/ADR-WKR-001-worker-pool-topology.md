# ADR-WKR-001: Worker Pool Topology — Three Named Pools, ThreadPoolExecutor, Local Autoscaling

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.4 — Worker Pools & Batch Scaling (Local-First)

## Context

Phase II requires background job execution for batch workloads — computing bulk chart reports, running research analyses, and serving interactive AI queries — without introducing third-party dependencies (Celery, Redis, RabbitMQ) per the local-first mandate (`CLAUDE_START_HERE.md`). Jobs have heterogeneous resource profiles: compute-heavy (Swiss Ephemeris calculations), I/O-bound (export, file I/O), and long-running/guarded (AI model calls). A single shared thread pool risks head-of-line blocking and resource contention.

## Decision

Adopt **three named, isolated in-process pools** — `cpu`, `io`, `ai` — each backed by a `ThreadPoolExecutor` with a dispatcher thread draining a priority queue:

1. **CPU pool** (`concurrent.futures.ThreadPoolExecutor`): Dedicates threads to Swiss Ephemeris computation. Threads are appropriate because Swiss Ephemeris calls are C-extension native calls that release the GIL, so true parallelism is achieved without a process-pool overhead.
2. **I/O pool** (`ThreadPoolExecutor`): Handles file writes (CSV/PDF export), HTTP calls (geocoding), and database queries. These threads spend most of their wall-clock time waiting on I/O — a thread pool is the natural fit.
3. **AI pool** (`ThreadPoolExecutor`): Reserved for model inference calls (hypothesis generation, research Q&A). Keeps long and potentially variable-duration calls from starving compute and I/O work.

**Local autoscaling:** Each pool's dispatcher loop monitors queue depth and in-flight thread count every `autoscale_interval` (default 5 s). When pending work exceeds idle capacity and the pool is below `max_workers`, new threads are added (within bounds). When idle and above `min_workers`, threads are released. This prevents over-provisioning while handling burst loads.

**Process pool alternative considered:** `ProcessPoolExecutor` was considered for the CPU pool to avoid GIL contention entirely. Rejected because (a) Swiss Ephemeris C bindings already release the GIL, (b) process pools impose serialization overhead on every call, and (c) the single-user local-first deployment does not warrant the complexity. A `pool_kind` parameter is reserved for future ProcessPoolExecutor migration without changing the public API (see `WorkerPool.__init__`).

## Consequences

- Zero new third-party dependencies. The three pools, dispatcher, and autoscaler use only `concurrent.futures`, `heapq`, `threading`, and `uuid` from the standard library.
- Resource contention between workload types is bounded. A bulk chart-computation job cannot starve an interactive AI query (pool isolation + priority routing per ADR-WKR-004).
- Thread count caps (`min_workers` / `max_workers`) are configurable via Settings, giving the single operator explicit control over local resource usage.
- Process-pool migration is a drop-in future option (the `WorkerPool` class is agnostic to executor type in its public interface).

---
*Author: Architecture Office, 2026-07-20*
