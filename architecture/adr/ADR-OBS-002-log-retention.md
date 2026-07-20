# ADR-OBS-002: Log Retention Policy — Local Files, Bounded, No Centralization

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.2 — Observability & SRE (Local-First)

## Context

The API emits structured JSON logs to stdout (ADR-OBS-001). A retention policy is needed that respects the local-first, single-user architecture: no centralized log service may be required.

## Decision

1. **Emission:** stdout only. The application never manages log files itself (no in-process file handlers, no rotation logic in code) — retention is an operational concern, kept out of the codebase.
2. **Local retention default:** the process supervisor (e.g., `scripts/dev.sh`, a service wrapper, or shell redirection) writes stdout to `logs/astroos-api.jsonl`; recommended rotation **14 days or 500 MB, whichever comes first** (logrotate or equivalent).
3. **Sensitive data:** logs must not contain credentials, tokens, or full birth-data payloads. Correlation/trace IDs, method, path, status, and durations are the standard request record.
4. **Centralized retention:** explicitly **deferred**. If a future phase introduces multi-machine deployment (requires its own ADR), stdout-JSON is already ingestible by Loki/ELK/CloudWatch without application changes.

## Alternatives considered

- **In-process RotatingFileHandler** — rejected: couples retention policy to application code and duplicates what OS tooling does better.
- **Database-backed log store** — rejected: PostgreSQL is the primary data store, not a log sink; write amplification and cleanup burden for no single-user benefit.

## Consequences

- Zero code-level retention maintenance; policy is documented in `observability/SLO.md` and `observability/README.md`.
- Research-mode query logging (Phase I.4, `query_log_service`) is unaffected — it is an application feature, not operational logging.

---
*Author: Architecture Office, 2026-07-20*
