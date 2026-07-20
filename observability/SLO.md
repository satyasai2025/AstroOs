# AstroOS SLI / SLO Definitions (Phase II.2 — Local-First)

> Applies to the local single-user deployment. Measured via `/metrics`
> (Prometheus) and structured JSON logs. Alert thresholds in
> `observability/prometheus/alert_rules.yml`.

## Service Level Indicators

| SLI | Definition | Source |
|---|---|---|
| Availability | Successful scrapes of `/health/live` and `up{job="astroos-api"}` | Prometheus `up` |
| Request latency | `api_request_duration_seconds` histogram (p50/p95/p99 by endpoint) | `/metrics` |
| Error rate | Share of requests with `status_code=~"5.."` | `/metrics` |
| Chart computation latency | `chart_computation_duration_seconds` histogram | `/metrics` |
| Traceability | Share of requests carrying `correlation_id` in logs | JSON logs |

## Service Level Objectives

| SLO | Target | Alert |
|---|---|---|
| API availability | 99% of scrape intervals up (local session) | ApiDown |
| Request latency | p95 < 5s over 5m windows | HighP95Latency |
| Error rate | 5xx < 1% (alert at 2%) | HighErrorRate |
| Chart computation | p95 < 2s over 10m windows | SlowChartComputation |
| Log correlation | 100% of API requests logged with correlation ID | (audit via logs) |

## Log retention (local-first default)

Logs go to stdout as single-line JSON. Retention is delegated to the local
supervisor (e.g., redirect to file with logrotate). Recommended local policy:
14 days or 500 MB, whichever first. Centralized retention is a Phase II.2
ADR topic (see task 9).

## Trace context

W3C `traceparent` accepted and emitted on every response;
`X-Correlation-ID` accepted/echoed. In-process spans (`start_span`) log
`span` events with `trace_id`/`span_id`/`duration_ms`. OpenTelemetry export
is a documented upgrade path, not a default dependency (local-first).
