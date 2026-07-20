# Runbook: <AlertName>

**Severity:** warning | critical
**SLO:** <which SLO this protects, see ../SLO.md>

## Symptoms
What the user/operator observes.

## Verify
Commands or URLs to confirm the problem is real (not a scrape artifact).

## Diagnose
Ordered checks, most likely cause first. Reference log queries
(`jq` over `logs/astroos-api.jsonl`) and Prometheus queries.

## Mitigate
Fastest safe path back to healthy.

## Follow-up
What to record; when to open an AMP/ADR.
