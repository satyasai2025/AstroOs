# AstroOS Observability (Local-First)

Everything here is **optional** and runs natively on the local machine — no
Docker, Kubernetes, or Helm, per `CLAUDE_START_HERE.md`.

## What the API provides out of the box

- `/metrics` — Prometheus exposition (Phase H, extended in Phase II.2)
- `/health/live`, `/health/ready` — probes
- Structured JSON logs on stdout with `correlation_id` and `trace_id`
  (opt out: `ASTROOS_JSON_LOGS=0`)
- `X-Correlation-ID` and W3C `traceparent` accepted and echoed per request
- In-process spans: `from apps.api.observability import start_span`

## Optional local stack

1. **Prometheus** (native binary):
   `prometheus --config.file=observability/prometheus/prometheus.yml`
2. **Alertmanager** (optional): point Prometheus at it; rules already in
   `prometheus/alert_rules.yml`.
3. **Grafana** (native binary): add Prometheus (`http://localhost:9090`) as a
   data source, then import `grafana/astroos_overview_dashboard.json`.

## SLIs / SLOs

See `SLO.md`. Alert thresholds mirror the SLOs.

## Log retention

stdout JSON → redirect to a file and rotate locally (14 days / 500 MB
recommended). Retention policy ADR: Phase II task 9.
