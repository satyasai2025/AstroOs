# CLAUDE_START_HERE.md

## Before Making Any Changes

**Read these files in order before proceeding:**

1. [README.md](README.md)
2. [architecture/INDEX.md](architecture/INDEX.md)
3. [architecture/STATUS.md](architecture/STATUS.md)
4. [architecture/ROADMAP.md](architecture/ROADMAP.md)
5. [ASTROOS_V2_ROADMAP.md](ASTROOS_V2_ROADMAP.md)
6. [ASTROOS_PHASE_I_V2_1_ROADMAP.md](ASTROOS_PHASE_I_V2_1_ROADMAP.md)
7. [CHANGELOG.md](CHANGELOG.md)
8. [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md) (if present)

---

## Important Project Update

The project has changed since previous discussion. **Do NOT rely on earlier assumptions about AstroOS.** The current repository is the source of truth.

### Key Changes:

- **AstroOS v2.0.0 is GA and frozen.**
- **Active development is v2.1.0 "Vistara".**
- **AstroOS is now a Local-First, single-user personal research platform.**
- **Native PostgreSQL is the official database** (running on localhost).
- **FastAPI + Next.js run locally** on the user's machine.
- **Redis is optional** (JWT denylist only, gracefully disabled if absent).
- **Docker, Kubernetes, Helm, cloud deployment, and enterprise infrastructure are NOT part of the current development plan.**
- **Existing Docker/Kubernetes documents are historical or future references only.**

---

## Official Architecture

```
User
 ↓
Next.js (Frontend)
 ↓
FastAPI (Backend API)
 ↓
PostgreSQL (Primary Data Store)
 ↓
Swiss Ephemeris (Astronomical Calculations)
```

All components run locally on a single machine. No external services required for core functionality.

---

## Workflow Rules

1. **Always use the repository documents as the authoritative source** instead of previous chat context.
2. **Read the files listed above** before proposing or implementing any changes.
3. **Update this file** (`CLAUDE_START_HERE.md`) whenever you change any documentation or project configuration.
4. **Do NOT modify business logic, APIs, database schema, or implemented features** unless explicitly requested.
5. **Keep all documentation consistent** with the Local-First architecture.

---

## Quick Reference

| Item | Value |
|------|-------|
| Current Version | v2.1.0 (released, tag `v2.1.0`) |
| Active Development | v2.2.0 "Arundhati" (Phase II, local-first scope — see `ASTROOS_V2_STATUS.md`) |
| Architecture | Local-First |
| Database | PostgreSQL 15+ (native) |
| Cache | Redis (optional) |
| Containerization | Not in current scope |

---

## Developer Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Local setup (<30 min target) |
| [docs/api-reference.md](docs/api-reference.md) | Curated API reference with curl examples |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Fixes for common local setup failures |
| [docs/contributing.md](docs/contributing.md) | Contribution guide, conventions, testing |
| [docs/architecture.md](docs/architecture.md) | Full architecture reference |
| [docs/developer-onboarding.md](docs/developer-onboarding.md) | Developer onboarding guide |
| [docs/migration-v2.1-to-v2.2.md](docs/migration-v2.1-to-v2.2.md) | Migration guide v2.1 → v2.2 |
| [docs/deprecation-policy.md](docs/deprecation-policy.md) | API deprecation policy |
| [docs/pre-commit-setup.md](docs/pre-commit-setup.md) | Pre-commit hooks setup guide |
| [docs/sdk/VERSIONING.md](docs/sdk/VERSIONING.md) | SDK versioning policy |
| [docs/sdk/PUBLISHING.md](docs/sdk/PUBLISHING.md) | SDK publishing guide |
| `.pre-commit-config.yaml` | Pre-commit hooks configuration |
| `.vscode/extensions.json` | Recommended VS Code extensions |
| `.vscode/settings.json` | Workspace VS Code settings |
| `scripts/dev.sh` | One-command dev start (API + frontend, hot reload) |

---

## Recent Documentation Changes

- **2026-07-20 (Phase II.4 complete):** Local-first worker pools + batch job API — `apps/api/services/worker_pool.py` (cpu/io/ai pools, priority queue, retry/backoff, dead-letter, local queue-depth autoscaling), `POST /api/v1/batch/chart-reports` + monitoring endpoints under `/api/v1/jobs`. 20 new tests. **Filed AMP-009 and AMP-010**: pre-existing Phase F defects making PDF/HTML report export non-functional (CSV export works) — see `architecture/decisions/`; not fixed here per the "don't modify completed modules" rule.
- **2026-07-20 (Phase II.3 complete):** SDKs made publish-ready — PyPI package `astroos` 2.2.0 (build + twine check verified, py.typed) and npm `@astroos/sdk` 2.2.0 (dual ESM/CJS/types build verified). New `docs/sdk/VERSIONING.md`, `docs/sdk/PUBLISHING.md`, `examples/notebooks/astroos_sdk_quickstart.ipynb`. Publishing itself is manual (credentials required).
- **2026-07-20 (Phase II.2 complete):** Local-first observability delivered — `apps/api/observability.py` (JSON logs w/ correlation IDs, W3C traceparent, spans, request metrics), optional native configs in `observability/` (Prometheus, alerts, Grafana dashboard, SLO.md, runbooks), ADR-OBS-001/002/003 in `architecture/adr/`. 17 new unit tests.
- **2026-07-20 (Phase II scope amendment):** Per user directive, Phase II tasks 6/7/18 (containers, Helm, K8s validation) permanently removed from `tasks_phase2_data.json`; pipeline rewired (task 8 now follows task 1). Local-first mandate reaffirmed — Docker/K8s/Helm/cloud remain out of scope. Decision recorded in `ASTROOS_V2_STATUS.md`; log in `PHASE_II_ORCHESTRATOR_LOG.md`.
- **2026-07-20 (Phase II.5 / Task 14):** Documentation & Developer Tools complete. New: `docs/migration-v2.1-to-v2.2.md`, `docs/developer-onboarding.md`, `docs/deprecation-policy.md`, `docs/pre-commit-setup.md`, `.pre-commit-config.yaml`, `.vscode/extensions.json`, `.vscode/settings.json`. CHANGELOG updated for v2.2.0. VERSION bumped to 2.2.0.
- **2026-07-19 (Phase I.1):** Documentation & DX pass. README updated (accurate local-first setup, stale Module Build Status table fixed — Modules 7–10 are implemented, not "Planned"). New: `docs/api-reference.md`, `docs/troubleshooting.md`, `docs/contributing.md`, `scripts/dev.sh`. Docstrings added to Pydantic schema classes and small registry/predicate helpers (documentation-only, no logic changes).
- **2026-07-19:** All 8 open AMPs (AMP-001 – AMP-008) resolved and closed by the Architecture Office. See `architecture/AMP-RESOLUTION-REPORT.md`. STATUS.md updated (stale note removed, Phase column added); `apps/api/domain/ontology.py` docstring corrected per AMP-008 (documentation-only). No frozen ADR document modified.

---

*This file is the entry point for all AI-assisted development. Update it when project context changes.*