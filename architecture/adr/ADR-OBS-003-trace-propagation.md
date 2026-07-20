# ADR-OBS-003: Trace Context Propagation — W3C Trace Context, OTel-Upgradeable

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.2 — Observability & SRE (Local-First)

## Context

Requests flow Next.js → FastAPI → engines (workflow orchestrator, Rule Engine, AI services). Debugging needs a way to correlate all work done for one request without adopting a distributed-tracing backend, which local-first forbids as a requirement.

## Decision

1. **Wire format:** W3C Trace Context. The API accepts an incoming `traceparent` header (validated; malformed values ignored), continues its `trace-id`, and emits a `traceparent` response header with the request's own span id. `X-Correlation-ID` is accepted/generated and echoed for human-friendly log lookup.
2. **In-process propagation:** `contextvars` (`trace_id_var`, `span_id_var`, `correlation_id_var` in `apps/api/observability.py`) — async-safe, no thread-locals, no globals.
3. **Spans:** `start_span(name, **attrs)` context manager; nested spans inherit trace id and parent span id. Spans are **logged as structured events** (`span` records with `duration_ms`, status, attributes), not exported to a tracing backend.
4. **Upgrade path:** because IDs and propagation are W3C-conformant, adopting OpenTelemetry later means swapping the span logger for an OTel exporter; no header, ID-format, or call-site changes. That adoption requires a follow-up ADR.

## Alternatives considered

- **OpenTelemetry SDK now** — rejected (see ADR-OBS-001): dependency weight and collector requirement conflict with local-first defaults.
- **Custom header scheme (e.g., X-Request-ID only)** — rejected: keeping W3C compatibility costs nothing and preserves interop with any future frontend/browser instrumentation.

## Consequences

- One `trace_id` links the request log line and every span logged beneath it; `jq 'select(.trace_id=="…")' logs/astroos-api.jsonl` reconstructs a request timeline offline.
- Frontend (Next.js) may optionally send `traceparent`/`X-Correlation-ID`; nothing breaks if it does not.
- Engine-level spans should be added incrementally where latency questions arise (orchestrator first), never as a blanket refactor.

---
*Author: Architecture Office, 2026-07-20*
