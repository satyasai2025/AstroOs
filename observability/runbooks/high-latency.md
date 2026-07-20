# Runbook: HighP95Latency

**Severity:** warning
**SLO:** p95 request latency < 5s (5m windows)

## Symptoms
Alert firing; UI feels slow; Grafana "Request Latency" panel p95 above 5s.

## Verify
Prometheus: `histogram_quantile(0.95, sum(rate(api_request_duration_seconds_bucket[5m])) by (le))`.

## Diagnose
1. Which endpoints: `topk(5, histogram_quantile(0.95, sum(rate(api_request_duration_seconds_bucket[5m])) by (le, endpoint)))`.
2. Slowest requests in logs: `jq 'select(.message=="http_request" and .duration_ms>5000)' logs/astroos-api.jsonl | tail`.
3. Follow a slow request's `trace_id` to its `span` records — is time in chart computation, Rule Engine, DB, or an outbound call (geocoding)?
4. Chart computation specifically: see `slow-chart-computation.md`.
5. DB: check `db_pool_usage`; long queries ⇒ `pg_stat_activity`.

## Mitigate
- Outbound geocoding slow/offline ⇒ use manual coordinate entry; consider disabling lookups for the session.
- DB contention ⇒ terminate runaway queries; restart API to reset pool.
- Load-induced (batch jobs) ⇒ pause batch work until interactive traffic recovers.

## Follow-up
If a specific endpoint is consistently over SLO, file a performance AMP with the trace evidence.
