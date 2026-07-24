# ADR-WORK-003: Retry Policy — Bounded Exponential Backoff, Explicit Dead-Letter

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.4 — Distributed Worker Pools & Auto-Scaling (Local-First)

## Context

Jobs can fail transiently (a flaky outbound call, a momentary resource contention) or permanently (bad input, a real bug). The system must not retry forever, and must never silently drop a failed job.

## Decision

1. **Per-job retry budget:** `max_retries` (default from `Settings.WORKER_MAX_RETRIES = 3`), settable per-submission (`WorkerPool.submit(..., max_retries=...)`).
2. **Exponential backoff:** `delay = retry_base_delay * 2^(attempt - 1)` (`Settings.WORKER_RETRY_BASE_DELAY_SECONDS`, default 1.0s) — a failed job is re-enqueued with a `not_before` timestamp; the dispatcher leaves it in the heap until that time passes rather than busy-polling.
3. **Dead-letter, not silent drop:** once `attempt > max_retries`, the job's terminal status becomes `dead_letter` (distinct from `failed`, which this implementation does not otherwise reach — a job is either retried, cancelled, completed, or dead-lettered). The error message is preserved on the `Job` record indefinitely until TTL eviction (ADR-OBS-002 pattern, `WORKER_JOB_TTL_SECONDS`). Dead-lettered jobs are visible via `GET /api/v1/jobs?status=dead_letter` and the HTML monitor.
4. **Batch jobs opt out of whole-job retry** (`max_retries=0` in `apps/api/routers/batch.py`): a batch is a container of many independent subject computations; retrying the *entire* batch on one subject's transient failure would redo already-succeeded work. Instead, `batch_report_service.run_batch_chart_reports` catches per-subject exceptions internally and records them in the output `MANIFEST.txt` — the batch job itself always reaches `completed` unless cancelled, with a success/failure count.
5. **Priority is not retry-boosted.** A retried job keeps its original `JobPriority`; retries do not jump the queue ahead of fresh interactive work.

## Alternatives considered

- **Unbounded retry** — rejected: masks real bugs as permanent background noise and can starve a pool with a poison-pill job.
- **Fixed (non-exponential) delay** — rejected: doesn't back off under sustained failure (e.g. a downstream dependency actually down for a while), causing needless retry storms.
- **Dead-letter queue as a separate pool/store** — rejected for this phase: dead-lettered jobs stay in the same pool's job dict with `status=dead_letter`; a dedicated store would add persistence machinery this phase's local-first, in-memory design deliberately avoids (see ADR-WORK-002).

## Consequences

- Every terminal failure is inspectable (`error` field) until TTL eviction; nothing vanishes.
- Callers needing "no retry, fail fast" (like batch subjects, handled at a finer grain internally) set `max_retries=0` explicitly.
- Retry storms are bounded in both count (max_retries) and rate (exponential backoff).

---
*Author: Architecture Office, 2026-07-20*
