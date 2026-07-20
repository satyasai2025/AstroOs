# ADR-OBS-001: Observability Stack — Prometheus Baseline, Zero New Runtime Dependencies

**Status:** Accepted
**Date:** 2026-07-20
**Owner:** Architecture (CAO)
**Phase:** II.2 — Observability & SRE (Local-First)

## Context

Phase II.2 requires production-grade observability (metrics, structured logs, tracing, alerts) while `CLAUDE_START_HERE.md` mandates a local-first architecture: no Docker, Kubernetes, Helm, or required external services. Phase H already ships `prometheus_client` metrics at `/metrics`.

## Decision

Adopt a **Prometheus-baseline, pull-based stack with zero new runtime dependencies**:

1. **Metrics:** Reuse and extend the Phase H `prometheus_client` registry (`apps/api/monitoring.py`). The `/metrics` endpoint is always on; scraping is optional.
2. **Logs:** Structured single-line JSON to stdout via stdlib `logging` (`apps/api/observability.py`), carrying `correlation_id` and `trace_id`. Opt-out to plain logs with `ASTROOS_JSON_LOGS=0`.
3. **Tracing:** Minimal in-process tracer (`start_span`) emitting span events as structured logs. W3C Trace Context (`traceparent`) accepted and echoed. Full OpenTelemetry export is an explicit **upgrade path, not a dependency** (see ADR-OBS-003).
4. **Visualization/alerting:** Prometheus, Alertmanager, and Grafana run as **optional native binaries**; ready-made configs live in `observability/` (scrape config, alert rules, dashboard JSON). Nothing in the API depends on them.

## Alternatives considered

- **OpenTelemetry SDK end-to-end** — rejected for now: heavy dependency tree, requires a collector process, conflicts with offline/local-first default. Design is OTel-compatible so migration is additive.
- **ELK / Loki for logs** — rejected: requires standing services; stdout JSON + local rotation suffices for single-user operation and remains machine-parseable for later ingestion.
- **Push-based metrics (StatsD/Pushgateway)** — rejected: pull model matches Phase H precedent and needs no always-on sink.

## Consequences

- Observability works with the API alone; richer views require optionally starting Prometheus/Grafana natively.
- SLIs/SLOs (`observability/SLO.md`) are defined against Prometheus metric names, which become a stable contract.
- Any future container/cloud deployment can reuse the same endpoints and configs unchanged (no rework), but such deployment remains out of scope per the 2026-07-20 governance decision.

---
*Author: Architecture Office, 2026-07-20*
