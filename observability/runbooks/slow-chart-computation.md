# Runbook: SlowChartComputation

**Severity:** warning
**SLO:** chart computation p95 < 2s (10m windows)

## Symptoms
Alert firing; analysis pipeline slow even though HTTP overhead is normal.

## Verify
Prometheus: `histogram_quantile(0.95, sum(rate(chart_computation_duration_seconds_bucket[10m])) by (le))`.

## Diagnose
1. Check ephemeris mode via `curl -s http://localhost:8000/api/healthz | jq .ephemeris` — `moshier` fallback (missing `.se1` files) is slower and less precise; expected warning at startup.
2. Break down by labels: `by (le, planet, house_system)` — one house system or body dominating suggests an algorithmic hotspot.
3. Concurrent batch/research jobs competing for CPU? Check request rate and any running batch work.

## Mitigate
- Restore `.se1` files at `EPHEMERIS_PATH` and restart if the mode regressed to fallback.
- Defer batch workloads to idle periods.

## Follow-up
Persistent hotspot ⇒ performance AMP with the offending labels and a captured `trace_id` example.
