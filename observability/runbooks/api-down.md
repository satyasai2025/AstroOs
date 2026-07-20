# Runbook: ApiDown

**Severity:** critical
**SLO:** API availability (99% of scrape intervals up)

## Symptoms
Prometheus `up{job="astroos-api"} == 0`; frontend requests fail; `curl http://localhost:8000/health/live` refuses or times out.

## Verify
1. `curl -s http://localhost:8000/health/live` — connection refused ⇒ process down; 200 ⇒ scrape config problem, not an outage.
2. Check the API process (uvicorn) is running.

## Diagnose
1. Tail the last log lines: `tail -50 logs/astroos-api.jsonl | jq -r '.level+" "+.message'` — look for startup failure (`AstroOS API starting` without `Swiss Ephemeris ready`).
2. Common causes: PostgreSQL not running (check `pg_ctl status` / service), port 8000 already bound, missing `.se1` ephemeris path misconfiguration, bad `.env` change.
3. Crash on request: find the last `http_request` line and its `trace_id`, then `jq 'select(.trace_id=="<id>")'` for the failing span/exception.

## Mitigate
1. Start PostgreSQL if down, then restart the API (`scripts/dev.sh` or your service wrapper).
2. If a recent config/code change caused it, revert the change and restart.

## Follow-up
Record cause and duration in `PHASE_II_ORCHESTRATOR_LOG.md` (or ops notes). Recurring cause ⇒ open an AMP.
