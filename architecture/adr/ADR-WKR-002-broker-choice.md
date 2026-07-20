# ADR-WKR-002: Broker Choice — In-Process Priority Queue, No External Broker

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.4 — Worker Pools & Batch Scaling (Local-First)

## Context

Background job systems conventionally use a dedicated message broker (Redis, RabbitMQ, Amazon SQS) to decouple job producers from consumers and to persist work across restarts. The local-first mandate (`CLAUDE_START_HERE.md`) prohibits required external services beyond PostgreSQL. Redis is optional (JWT denylist only) and is not guaranteed to be running when the API starts. A broker-optional design would mean two code paths to maintain.

## Decision

Use an **in-process priority queue (`heapq` + `threading.Condition`) as the job broker**, co-located with the worker pool in the same Python process:

1. **Queue mechanism:** A `heapq`-based priority queue, protected by a `threading.RLock` and signaled via `threading.Condition`. The dispatcher thread blocks on the condition variable when the queue is empty, consuming no CPU while idle.
2. **No external broker.** There is no Redis, RabbitMQ, PostgreSQL-based, or filesystem-backed job store. Job records live in-memory (`WorkerPool._jobs: dict[str, Job]`).
3. **Job persistence:** Jobs are ephemeral — they survive only as long as the API process. A future phase may add durable job storage via the existing `ExperimentExecutionModel` in PostgreSQL, but this is deferred (see Future Evolution).
4. **TTL-based eviction:** Completed/failed/cancelled job records are evicted after `job_ttl_seconds` (default 24 h) by a background reaper thread, preventing unbounded memory growth.

## Alternatives considered

- **Redis Queue (RQ) or Celery + Redis** — rejected: adds a mandatory Redis dependency. Redis is already optional; making it required for batch jobs would violate the local-first contract.
- **PostgreSQL as job queue (`SKIP LOCKED`)** — rejected: couples job lifecycle to the analytical data store. Workable for single-user scale but introduces write amplification and complexity for no benefit over in-memory dispatch.
- **Filesystem-backed queue (JSON files in a spool directory)** — rejected: adds I/O overhead, race conditions on multi-file reads, and cleanup burden without tangible benefit at single-user scale.

## Consequences

- **Zero infrastructure to run, configure, or monitor.** The worker pool is ready when the API process is ready.
- **Jobs are lost on process restart.** This is acceptable for the local-first use case (e.g., "compute 1000 reports") — the operator re-submits. Durable job storage is a tracked future item.
- **Single-process scaling.** The pool can only use the cores and memory of one machine. This is consistent with the local-first architecture; horizontal scaling (multi-machine workers) would require a separate ADR and an external broker.
- **Priority routing** is built into the queue key (`_QueueEntry.priority`) — see ADR-WKR-004.

## Future Evolution

When multi-process or multi-machine deployment is considered (requires its own ADR per ROADMAP.md governance), the `WorkerPool.submit()` interface is a stable insertion point for an external broker adapter — no existing API callers would change.

---
*Author: Architecture Office, 2026-07-20*
