# Runbook: HighErrorRate

**Severity:** critical
**SLO:** 5xx < 1% of requests (alert at 2%)

## Symptoms
Alert firing; users see "An internal error occurred."; 5xx share climbing in Grafana.

## Verify
Prometheus: `sum(rate(api_request_duration_seconds_count{status_code=~"5.."}[5m])) / sum(rate(api_request_duration_seconds_count[5m]))`.

## Diagnose
1. Which endpoints: `sum(rate(api_request_duration_seconds_count{status_code=~"5.."}[5m])) by (endpoint)`.
2. Exceptions with stack traces: `jq 'select(.level=="ERROR")' logs/astroos-api.jsonl | tail -20`.
3. Correlate: each 5xx `http_request` line's `trace_id`/`correlation_id` links the request to its exception record.
4. Common causes: PostgreSQL connectivity lost mid-session, ephemeris files moved/corrupted, malformed knowledge/dataset imports, recent code change.

## Mitigate
- Restore the failing dependency (DB up, ephemeris path valid), errors clear immediately — no restart usually needed.
- If a deploy/change introduced it, revert and restart.

## Follow-up
Every distinct exception signature reaching users warrants a regression test before the fix is considered done.
