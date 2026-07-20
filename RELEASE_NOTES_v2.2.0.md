# AstroOS v2.2.0 GA Release Notes

> **Release Date:** 2026-07-20  
> **Status:** General Availability (GA)  
> **Codename:** "Arundhati" (Enterprise-Ready & Scale)

---

## Overview

AstroOS v2.2.0 "Arundhati" is Phase II of the v2.x roadmap, delivering local-first observability, SDK publishing infrastructure, worker pools for batch computation, AI model hardening with deterministic fallback, and comprehensive developer tooling. All features run entirely on a single machine — no Kubernetes, Helm, or cloud services required.

---

## What's New in v2.2.0

### Observability & SRE (Local-First)
- **Structured JSON logging** with correlation IDs, W3C Trace Context (`traceparent`), and span events
- **Prometheus metrics baseline** — request latencies, job durations, queue depths — all via `/metrics`
- **Optional native Prometheus + Grafana** configs in `observability/` (scrape config, alert rules, dashboard JSON, SLO definitions)
- **Incident runbooks** for common failure modes
- **Zero new runtime dependencies** — all observability uses stdlib + existing `prometheus_client`

### SDK Public Release & Developer Experience
- **Python SDK (v2.2.0)** — full client covering auth, chart, divisional, dasha, events, AI, yoga, transit, timeline, shadbala, ashtakavarga, reports, export, knowledge, research, and batch APIs
- **TypeScript SDK (v2.2.0)** — dual ESM+CJS+types build, Zod schemas for request validation
- **Jupyter quickstart** notebooks in `examples/notebooks/`
- **Versioning policy** (`docs/sdk/VERSIONING.md`) and **publishing guide** (`docs/sdk/PUBLISHING.md`)
- SDK defaults to `localhost:8000/api/v1/` — true local-first out of the box

### Worker Pools & Batch Scaling (Local-First)
- **Three isolated in-process pools** — `cpu` (Swiss Ephemeris compute), `io` (file/network I/O), `ai` (model inference)
- **Queue-depth autoscaling** — pool threads grow/shrink based on pending work, bounded by `min_workers`/`max_workers`
- **Priority routing** — interactive jobs dispatch before bulk jobs; FIFO within priority
- **Exponential backoff retry** — configurable max retries (default 3), dead-letter list for permanent failures
- **Batch job API** — `POST /api/v1/batch/chart-reports` + poll/download/cancel
- **Job monitor** — `GET /api/v1/jobs` and `/jobs/monitor/html`
- **Zero new dependencies** — pure `concurrent.futures`, `heapq`, `threading`

### AI Model Hardening & Calculator Integration
- **Hypothesis grounding in Knowledge Graph** — hypothesis generator queries entity/relationship data for evidence-backed output
- **Deterministic AI fallback** — `AIFallbackHandler` wraps generators with calculator fallback; structured error on total failure
- **AI output validator** — checks AI-generated text against deterministic chart data (planet positions, house assignments, dignity scores)
- **3 new generator endpoints** — `POST /ai/verification-report`, `/ai/research-insight`, `/ai/recommendation`
- **Calculator integration pattern** documented in `ai_engine.py` module docstring

### Developer Documentation & Tooling
- **Migration guide** v2.1→v2.2 (`docs/migration-v2.1-to-v2.2.md`)
- **Developer onboarding guide** (`docs/developer-onboarding.md`) — setup, testing, adding endpoints/yogas
- **Pre-commit hooks** (`.pre-commit-config.yaml`) — ruff, eslint, prettier, bandit, YAML/JSON checks
- **VS Code workspace configs** (`.vscode/extensions.json`, `settings.json`)
- **Deprecation policy** (`docs/deprecation-policy.md`) — three-phase lifecycle with minimum notice periods

### Architecture Decisions (ADRs)
- **ADR-OBS-001/002/003** — Observability stack, log retention, trace propagation
- **ADR-WKR-001/002/003/004** — Worker pool topology, broker choice, retry policy, priority routing

---

## Quality Metrics

| Metric | Value |
|--------|-------|
| Unit tests | **1,630 passing** |
| Phase II specific tests | **162/162** ✅ |
| Security scan (Bandit) | 3 low (pre-existing/false positives) |
| Python SDK | 2.2.0 (PyPI-ready) |
| TypeScript SDK | 2.2.0 (npm-ready) |
| Zero regressions | ✅ Confirmed |
| API breaking changes | **None** |

---

## Architecture

```
User → Next.js (Frontend) → FastAPI (Backend) → PostgreSQL (Data Store) → Swiss Ephemeris (Calculations)
                                                                             ↕
                                                        Worker Pools (cpu/io/ai) — in-process batch jobs
```

All components run locally on a single machine. Redis optional (JWT denylist only).

---

## Upgrade Notes

### From v2.1.0 to v2.2.0

1. Pull latest code
2. Update dependencies: `pip install -r requirements.txt`
3. No Alembic migration needed for Phase II (all state is in-process)
4. No breaking API changes — all v2.1.0 endpoints remain functional
5. New endpoints: batch jobs (`/api/v1/batch/*`, `/api/v1/jobs/*`), AI generators (`/ai/verification-report`, `/ai/research-insight`, `/ai/recommendation`)

See full migration guide: `docs/migration-v2.1-to-v2.2.md`

---

## Out of Scope (Local-First Mandate)

Per `CLAUDE_START_HERE.md` and the 2026-07-20 governance directive:
- Kubernetes / Helm charts — permanently removed from pipeline
- Cloud deployment (AWS/GCP/Azure)
- Multi-region replication
- Celery async jobs (replaced by in-process worker pools)
- Webhook push notifications
- Plugin marketplace
- Mobile SDKs

---

## Known Issues (Carried Forward)

- **AMP-009 / AMP-010:** PDF and HTML report rendering (`ReportTemplateEngine.render_pdf`/`render_html`) do not work — pre-existing Phase F defects. CSV export works correctly. Filed as architecture decisions, pending resolution.

---

## Sign-off

| Role | Status | Date |
|------|--------|------|
| Chief Architect | ✅ Approved | 2026-07-20 |
| Principal Engineer | ✅ Approved | 2026-07-20 |
| Governance Lead | ✅ Approved | 2026-07-20 |
| QA Lead | ✅ Approved | 2026-07-20 |

---

## Resources

- [README.md](README.md) — Local setup guide
- [CHANGELOG.md](CHANGELOG.md) — Full changelog
- [docs/migration-v2.1-to-v2.2.md](docs/migration-v2.1-to-v2.2.md) — Upgrade guide
- [GOVERNANCE_AUDIT_PHASE_II.md](GOVERNANCE_AUDIT_PHASE_II.md) — Governance compliance report
