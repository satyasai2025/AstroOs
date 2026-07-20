# ADR-WKR-004: Priority Routing — Interactive Before Bulk, Non-Preemptive

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.4 — Worker Pools & Batch Scaling (Local-First)

## Context

The worker pool serves two distinct classes of work: **interactive** requests (user waiting for an AI hypothesis or a chart computation) and **bulk/batch** requests (pre-compute 1000 reports for a research project). Without priority routing, a bulk submission can occupy all pool threads and cause interactive requests to queue behind it, degrading the user experience. The local-first mandate prohibits external priority queue infrastructure.

## Decision

Implement a **two-level priority routing scheme using a unified priority queue**, with interactive jobs dispatched before bulk jobs:

1. **Priority levels** (`JobPriority` enum, lower numeric value = higher priority):
   - `INTERACTIVE = 0` — User-facing requests (chart computation triggered from the dashboard, AI query awaiting a response).
   - `BULK = 10` — Background batch work (research project export, bulk report generation).

2. **Dispatch ordering:** The dispatcher always pops the lowest-priority entry from `heapq`. Among entries at the same priority level, FIFO ordering is preserved by a monotonically increasing sequence number (`itertools.count()`). A bulk entry can never be dispatched while an interactive entry is queued — regardless of submission order.

3. **Non-preemptive execution.** Once a thread picks up a job and starts running it, that job runs to completion (or failure). There is no preemption, time-slicing, or cancellation of a running job to make way for a higher-priority one. This avoids deadlock and complexity at single-user scale; the interactive job's priority advantage is in **dispatch ordering**, not runtime preemption.

4. **Pool isolation preserved.** Priority routing operates within each pool independently. A bulk job on the IO pool never blocks an interactive job on the CPU pool, because each pool has its own dispatcher, its own heap, and its own thread pool (per ADR-WKR-001).

5. **Priority is a submission-time attribute.** The caller chooses priority when calling `WorkerPool.submit(priority=JobPriority.INTERACTIVE)` or `WorkerPool.submit(priority=JobPriority.BULK)`. Priority is immutable after submission — escalation or de-escalation is deferred as a future enhancement.

## Alternatives considered

- **Separate queues per priority level (e.g., `high_priority_queue` + `low_priority_queue`)** — rejected: a single `heapq` with a composite sort key achieves the same ordering with less code (no weighted fair-queuing or starvation-prevention algorithm needed).
- **Weighted fair queuing (WFQ)** — rejected: over-engineered for two priority levels at single-user scale. WFQ would be revisited if the number of priority levels grows beyond 3.
- **Preemptive priority (cancel or pause a running job)** — rejected: introduces thread-safety complexity (killing a thread mid-execution leaves resources in an unknown state) for a scenario that is unlikely at single-user scale. The non-preemptive model is the standard choice for I/O-bound and compute-bound thread pools.

## Consequences

- Interactive jobs never wait behind a queue of bulk jobs — the user's dashboard and AI queries remain responsive during batch processing.
- Within the same priority level, jobs are served fairly in submission order.
- Running jobs are not interrupted — a bulk job already in-flight continues even if an interactive job is submitted afterward. At single-user scale this is acceptable: the interactive job dispatches immediately on the **next available** thread, which typically arrives within milliseconds.
- The two-level scheme is future-proof (the `IntEnum` naturally accepts additional levels between 0 and 10).

---
*Author: Architecture Office, 2026-07-20*
