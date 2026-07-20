# Migration Guide: v2.1 "Vistara" → v2.2 "Arundhati"

> **Audience:** Developers upgrading an existing v2.1 AstroOS installation.
> **Est. time:** 15 minutes (pull + migrate + verify).

## Overview

v2.2.0 ("Arundhati") is the Phase II release of AstroOS. It adds local-first
observability, publishable SDKs, worker pools for batch computation, AI model
hardening, and architecture decision records for the new subsystems.

**No breaking changes to the API contract, database schema, or public SDK
surface.** All v2.1 features and endpoints continue to work without
modification.

---

## What Changed Between v2.1 and v2.2

### New Features

| Feature | Description | Delivered In |
|---------|-------------|--------------|
| **AMP Governance** | All 8 Actionable Maturity Process items resolved and closed. Governance audit completed. | Task 1 |
| **Observability & SRE (Local-First)** | Structured JSON logging with correlation IDs (`trace_id`, `span_id`), W3C `traceparent` propagation, request/response timing spans, Prometheus metrics middleware. Native configs for Prometheus, alert rules, and Grafana in `observability/`. | Task 8 |
| **Architecture ADRs (Observability)** | ADR-OBS-001 (stack), ADR-OBS-002 (log retention), ADR-OBS-003 (trace propagation). | Task 9 |
| **SDK Public Release & DX** | Python SDK (`astroos` 2.2.0, PyPI-ready) and TypeScript SDK (`@astroos/sdk` 2.2.0, npm-ready). Quickstart guides, versioning policy, publishing guide. Jupyter example notebook. | Task 10 |
| **Worker Pools & Batch Scaling** | CPU/I/O/AI worker pools with priority queue, retry/backoff, dead-letter queue, local autoscaling. Batch chart-reports API (`POST /api/v1/batch/chart-reports`). Job monitoring endpoints. | Task 11 |
| **Architecture ADRs (Worker Pools)** | ADR-WKR-001 (topology), ADR-WKR-002 (broker choice), ADR-WKR-003 (retry policy), ADR-WKR-004 (priority routing). | Task 11 |
| **AI Model Hardening & Calculator Integration** | Calculator integration into AI tools, schema hardening, improved error handling. | Task 13 |
| **Hypothesis Validation & Query Logging** | Hypothesis validation service, query log service for research reproducibility, research middleware. | Task 13 |

### New Files & Modules

- `apps/api/observability.py` — middleware for logging, tracing, metrics
- `apps/api/services/worker_pool.py` — CPU/I/O/AI pool implementation
- `apps/api/services/hypothesis_validation_service.py` — AI hypothesis validation
- `apps/api/services/query_log_service.py` — research query audit trail
- `apps/api/services/research_middleware.py` — research-mode middleware
- `apps/api/services/research_csv_exporter.py` — CSV export for research
- `apps/api/routers/research_tools.py` — research tools API endpoints
- `apps/api/models/research.py` — research ORM models
- `apps/api/schemas/research_tools.py` — research tools schemas
- `observability/` — Prometheus config, alert rules, Grafana dashboard, SLO.md, runbooks
- `architecture/adr/ADR-OBS-001/002/003.md` — observability ADRs
- `architecture/adr/ADR-WKR-001/002/003/004.md` — worker pool ADRs
- `sdks/python/` — publishable Python SDK
- `sdks/typescript/` — publishable TypeScript SDK
- `docs/sdk/VERSIONING.md` — SDK versioning policy
- `docs/sdk/PUBLISHING.md` — SDK publishing guide
- `examples/notebooks/astroos_sdk_quickstart.ipynb` — Jupyter quickstart

### New Dependencies (Python)

Added to `apps/api/requirements.txt` / `pyproject.toml`:

| Package | Purpose |
|---------|---------|
| `prometheus-client` | Worker pool metrics (already present for monitoring) |
| `opentelemetry-api` | Trace context propagation (optional, graceful fallback) |

### New Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FORMAT` | `json` | Log format (`json` or `text`; `text` for dev) |
| `OTEL_SERVICE_NAME` | `astroos-api` | OpenTelemetry service name for trace propagation |
| `WORKER_POOL_CPU_SIZE` | `2` | CPU worker pool size |
| `WORKER_POOL_IO_SIZE` | `4` | I/O worker pool size |
| `WORKER_POOL_AI_SIZE` | `1` | AI worker pool size |
| `WORKER_MAX_RETRIES` | `3` | Maximum retries for failed jobs |

### New API Endpoints

All endpoints are prefixed with `/api/v1`.

#### Observability & Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (unauthenticated) |
| `GET` | `/health/live` | Liveness probe |
| `GET` | `/health/ready` | Readiness probe |

#### Batch / Worker Pools

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/batch/chart-reports` | Submit batch chart-report generation job |
| `GET` | `/batch/jobs/{job_id}` | Poll job status |
| `GET` | `/batch/jobs/{job_id}/download` | Download completed job results |
| `DELETE` | `/batch/jobs/{job_id}` | Cancel a pending/running job |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/jobs/monitor/html` | Job monitor dashboard (HTML) |

#### Research Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/research/projects` | Create a research project |
| `GET` | `/research/projects` | List research projects |
| `GET` | `/research/projects/{id}` | Get research project details |
| `POST` | `/research/snapshots` | Capture a research snapshot |
| `POST` | `/research/hypothesis/validate` | Validate a research hypothesis |
| `GET` | `/research/queries` | Query audit log |
| `POST` | `/research/export/csv` | Export research data as CSV |

---

## Deprecation Notices

- **No endpoints or features were deprecated in v2.2.**
- The `apps/api/monitoring.py` module (v2.0) is superseded by
  `apps/api/observability.py` but remains functional and is **not** deprecated.
  Both modules coexist; observability.py adds structured logging and tracing on
  top of the same Prometheus metrics path.

---

## Upgrade Steps

### Step 1: Pull the latest code

```bash
git checkout main
git pull origin main
```

Verify you are on the v2.2 release:

```bash
cat VERSION
# Expected: 2.2.0
```

### Step 2: Install new dependencies

```bash
pip install --upgrade -r apps/api/requirements.txt
```

### Step 3: Run database migrations

```bash
PYTHONPATH=. alembic -c database/alembic.ini upgrade head
PYTHONPATH=. alembic -c database/alembic.ini current
# Expected output: <revision_id> (head)
```

> **Note:** v2.2 does not introduce any new migrations. If alembic reports
> "already at head," you are up to date.

### Step 4: Update environment variables (optional)

Review your `.env` file against the new variables listed above. The defaults
are suitable for local development; only `LOG_LEVEL` may be worth adjusting:

```bash
# .env additions (all optional, defaults shown)
LOG_LEVEL=INFO
LOG_FORMAT=json          # Use "text" for human-readable dev logs
OTEL_SERVICE_NAME=astroos-api
WORKER_POOL_CPU_SIZE=2
WORKER_POOL_IO_SIZE=4
WORKER_POOL_AI_SIZE=1
WORKER_MAX_RETRIES=3
```

### Step 5: Verify

```bash
# Start the API
PYTHONPATH=. uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# Health check (unauthenticated)
curl http://localhost:8000/api/healthz

# Liveness probe
curl http://localhost:8000/api/health/live

# Run the test suite
PYTHONPATH=. pytest tests/ -v --cov=apps --cov=packages
```

---

## Post-Upgrade Checklist

- [ ] Logs are outputting in JSON format with `trace_id` and `span_id` fields
- [ ] `/api/health/live` and `/api/health/ready` return 200
- [ ] All existing v2.1 API endpoints return expected results
- [ ] Worker pool metrics appear at `/api/metrics` (Prometheus)
- [ ] `python -c "from astroos import AstroOSClient"` succeeds (Python SDK)
- [ ] Test suite passes: `PYTHONPATH=. pytest tests/ -v`

---

## Rolling Back

If issues arise, revert to the v2.1 tag:

```bash
git checkout v2.1.0
pip install --force-reinstall -r apps/api/requirements.txt
PYTHONPATH=. alembic -c database/alembic.ini downgrade -1
```

> The v2.2 schema is backward-compatible with v2.1 data — no destructive
> migrations were run. Downgrading is safe.

---

## Compatibility Matrix

| Component | v2.1 Compatible | v2.2 Notes |
|-----------|----------------|------------|
| Python SDK (sdks/python) | Yes | Upgrade recommended for new features |
| TypeScript SDK (sdks/typescript) | Yes | Upgrade recommended for new features |
| Frontend (apps/web) | Yes | No changes required |
| Redis (JWT denylist) | Yes | Unchanged |
| Swiss Ephemeris (.se1 files) | Yes | Unchanged |
| Custom integrations | Yes | No breaking changes |
