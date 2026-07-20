# ADR-WKR-003: Retry Policy — Exponential Backoff with Dead-Letter Termination

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.4 — Worker Pools & Batch Scaling (Local-First)

## Context

Background jobs may fail transiently (network timeouts, database connection drops, ephemeris file not yet cached) or permanently (invalid input data, bug in job function). A retry policy must distinguish between these cases, avoid retry storms, and surface permanently failed jobs without silently dropping them.

## Decision

Adopt an **exponential backoff retry policy with configurable maximum attempts and a dead-letter list**:

1. **Retry trigger:** Any unhandled exception thrown by the job function triggers a retry. `JobCancelled` (explicit cancellation) is not retried — it is recorded as a cancellation outcome.
2. **Backoff formula:** `delay = retry_base_delay × 2^(attempt - 1)`, where `attempt` starts at 1 on the first run (first failure → attempt=1 in the retry). Default `retry_base_delay = 1.0 s` produces delays of ~1 s, ~2 s, ~4 s, ~8 s on successive retries.
3. **Max retries:** Configurable per job via `max_retries` parameter (default 3). After `max_retries` consecutive failures, the job transitions to `DEAD_LETTER` status — never silently dropped, never retried again.
4. **Dead-letter list:** Failed jobs are retained in the in-memory job store with status `DEAD_LETTER` and their final error message. The operator (or a monitoring endpoint) can inspect dead-lettered jobs via `WorkerPool.list_jobs(status="dead_letter")` or the batch job API. Explicit human action (e.g., an admin endpoint to re-queue a dead-lettered job) is deferred as a future enhancement.
5. **No retry on cancellation.** If a user explicitly cancels a running job (via `WorkerPool.cancel()`), the job function must periodically call `check_cancelled()` to raise `JobCancelled` — the pool treats this as a clean voluntary stop, not a failure.

## Alternatives considered

- **Fixed-interval retry** — rejected: risks retry-storming the database or ephemeris library on transient infrastructure glitches. Exponential backoff is the standard mitigation.
- **Infinite retry with backoff** — rejected: permanently failing jobs would occupy queue slots and consume memory indefinitely. A dead-letter cap is the standard bounded-failure pattern.
- **Circuit breaker per job type** — rejected: adds complexity beyond single-user needs. If a future multi-tenant deployment requires it, the pattern is already used in ADR-EAL-025's Integration Framework and can be adapted.

## Consequences

- Transient failures self-heal within predictable bounds (default max ~15 s total backoff window for 3 retries).
- Permanently failing jobs are never lost — they surface in the dead-letter list for inspection.
- The retry policy is fully observable via Prometheus metrics (`worker_jobs_completed_total{outcome="retry"}` and `{outcome="dead_letter"}`).
- Backoff parameters are per-job, allowing interactive jobs (low retries, short delay) vs. bulk jobs (higher retries, longer delay) to use different profiles — consistent with the priority routing model in ADR-WKR-004.

---
*Author: Architecture Office, 2026-07-20*
