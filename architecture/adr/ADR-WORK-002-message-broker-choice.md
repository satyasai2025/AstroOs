# ADR-WORK-002: Message Broker — None by Default (In-Process Priority Heap)

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.4 — Distributed Worker Pools & Auto-Scaling (Local-First)

## Context

The Phase II.4 roadmap asks for a broker decision (Redis vs RabbitMQ) as if a broker were required. Local-first single-user operation does not need cross-process/cross-machine message delivery.

## Decision

**No broker.** Each `WorkerPool` owns an in-process `heapq`-based priority queue (`_QueueEntry`, ordered by `JobPriority` then submission sequence) guarded by a single `threading.RLock`/`Condition`. Jobs and their state (`Job` dataclass) live in an in-memory dict per pool — the same pattern already used by `apps/api/routers/dataset_import.py`'s `_import_jobs` tracker, extended with priority, retries, and progress.

Redis is already an optional dependency in this codebase (`Settings.REDIS_URL`, used only for the JWT denylist — see `apps/api/dependencies.py`). This ADR does not change that; Redis remains optional and unrelated to job queuing.

## Alternatives considered

- **Redis as broker (lists/streams)** — rejected as a requirement: would make an optional component mandatory for a core feature (batch jobs), directly contradicting `CLAUDE_START_HERE.md`. Remains a natural fit *if* a future multi-process/multi-machine ADR is approved — Redis is already in the dependency graph.
- **RabbitMQ** — rejected: a new, heavier dependency with no offsetting benefit at single-machine scale; would also need to run as its own service, which local-first disallows as a default requirement.
- **SQLite/PostgreSQL-backed queue** — considered for durability (jobs would survive an API restart) but rejected for this phase: adds schema/migration surface for a feature whose current worst case (job list lost on restart) is acceptable for interactive/batch work a single user re-submits. Revisit if job durability across restarts becomes a real requirement.

## Consequences

- Job records do not survive an API process restart — acceptable given local-first, single-user scope; documented, not hidden.
- Zero new services to install, configure, or monitor.
- If a future phase requires durability or true multi-worker-process distribution, the queue implementation is isolated inside `WorkerPool` (`_enqueue`/`_heap`/`_dispatch_loop`); swapping in Redis-backed queuing would not require router or `Job`-shape changes.

---
*Author: Architecture Office, 2026-07-20*
