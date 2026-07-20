# CLAUDE_START_HERE.md

## Before Making Any Changes

**Read these files in order before proceeding:**

1. [README.md](README.md)
2. [architecture/INDEX.md](architecture/INDEX.md)
3. [architecture/STATUS.md](architecture/STATUS.md)
4. [architecture/ROADMAP.md](architecture/ROADMAP.md)
5. [ASTROOS_V2_ROADMAP.md](ASTROOS_V2_ROADMAP.md)
6. [CHANGELOG.md](CHANGELOG.md)
7. [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md) (if present)

---

## Important Project Update

**AstroOS v2.3.0 "Lakshmi" (Phase III) is the current stable release.** All phases are local-first, single-user personal research platform. The repository is the source of truth.

### Key Constraints:

- **AstroOS is a Local-First, single-user personal research platform.** Everything runs on a single machine. No cloud services required.
- **Native PostgreSQL is the official database** (localhost).
- **FastAPI + Next.js run locally.** Additionally, a React Native mobile app and a Python CLI tool extend access beyond the browser — both default to `localhost:8000`.
- **Redis is optional** (JWT denylist only, gracefully disabled if absent).
- **Docker, Kubernetes, Helm, cloud deployment, and enterprise infrastructure are NOT part of the development plan.**
- **Existing Docker/Kubernetes documents are historical or future references only.** See `CLAUDE_START_HERE.md`'s own "Key Changes" note on this.
- **Mobile apps** (iOS/Android) connect to the user's own local API — no cloud relay, no hosted sync service. Push notifications are optional (feature-flagged).
- **Plugin system** is local-first (file-based registry, CLI install from tarballs, subprocess sandbox). No hosted marketplace, no Stripe, no dev portal.
- **All analytics and i18n** are pure local computation and static files — zero external dependencies.

---

## Official Architecture

```
User ─┬→ Next.js (Web Browser)
      ├→ React Native (Mobile App — iOS + Android)
      └→ CLI (Plugin mgmt, data export, research tools)
              ↓
         FastAPI (Backend API)
          ↓             ↕
     PostgreSQL     Worker Pools (cpu/io/ai)
          ↓          in-process batch jobs
   Swiss Ephemeris
```

All components run locally on a single machine. Mobile and CLI connect to `localhost:8000` by default.

---

## What v2.3.0 Includes

| Area | What's Built | Local-First? |
|------|-------------|--------------|
| **Web frontend** | Next.js app with D3.js charts, dark mode, research dashboard | ✅ Pure local |
| **REST API** | FastAPI, 80+ endpoints covering horoscope, dasha, yoga, transit, AI, reports | ✅ Pure local |
| **Calculation engines** | Shadbala (6-fold), Ashtakavarga (7 grahas), 70+ yoga types (Phase 1 + 2), 6 Dasha systems, 15 vargas | ✅ Pure local |
| **Research tools** | Project CRUD, snapshot comparison, CSV/JSON export with citations, hypothesis validation, research mode logging | ✅ Pure local |
| **AI engine** | Template-based NLG (6 generators), Knowledge Graph-grounded hypotheses, deterministic fallback | ✅ Pure local (no LLM) |
| **Worker pools** | 3 in-process pools (cpu/io/ai), priority queue, queue-depth autoscaling, retry/backoff, dead-letter | ✅ Pure local |
| **Observability** | JSON logging, Prometheus metrics, W3C traceparent, Grafana dashboards (optional) | ✅ Pure local |
| **SDKs** | Python 2.2.0 + TypeScript 2.2.0 | ✅ Point to localhost by default |
| **Mobile app** | React Native (iOS + Android), birth chart, Dasha timeline, offline SQLite cache | ✅ Defaults to localhost |
| **Plugin CLI** | `astroos-plugin` — list, install, uninstall, scaffold, validate. Subprocess sandbox | ✅ File-based registry |
| **Analytics** | Query builder + statistical engine (correlation, chi², t-test, Bayes) | ✅ Pure local |
| **i18n** | 5 languages (ES, HI, FR, DE, AR), static JSON translations | ✅ Static files |

---

## Workflow Rules

1. **Always use the repository documents as the authoritative source** instead of previous chat context.
2. **Read the files listed above** before proposing or implementing any changes.
3. **Update this file** (`CLAUDE_START_HERE.md`) whenever you change any documentation or project configuration.
4. **Do NOT modify business logic, APIs, database schema, or implemented features** unless explicitly requested. Exceptions: approved AMP resolutions (architecture-governed bugfixes) may modify frozen code — see `architecture/AMP-RESOLUTION-REPORT.md`.
5. **Keep all documentation consistent** with the Local-First architecture.

---

## Quick Reference

| Item | Value |
|------|-------|
| Current Version | **v2.3.0** (released, tag `v2.3.0`) |
| Codename | Lakshmi (Phase III — Mobile, Plugins, Analytics, i18n) |
| Architecture | Local-First |
| Database | PostgreSQL 15+ (native) |
| Frontend | Next.js (web) + React Native (mobile) |
| CLI | Python CLI (`apps/cli/astroos-plugin`) |
| Cache | Redis (optional) |
| Containerization | **Not in scope** |

---

## Developer Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Local setup (<30 min target) |
| [docs/api-reference.md](docs/api-reference.md) | Curated API reference with curl examples |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Fixes for common local setup failures |
| [docs/contributing.md](docs/contributing.md) | Contribution guide, conventions, testing |
| [docs/architecture.md](docs/architecture.md) | Full architecture reference |
| [docs/developer-onboarding.md](docs/developer-onboarding.md) | Developer onboarding guide (Phase II) |
| [docs/migration-v2.1-to-v2.2.md](docs/migration-v2.1-to-v2.2.md) | Migration guide v2.1 → v2.2 |
| [docs/deprecation-policy.md](docs/deprecation-policy.md) | API deprecation policy |
| [docs/pre-commit-setup.md](docs/pre-commit-setup.md) | Pre-commit hooks setup guide |
| [docs/api-key-management.md](docs/api-key-management.md) | API key auth and OAuth guide (Phase III) |
| [docs/mobile-store-submission.md](docs/mobile-store-submission.md) | iOS + Android store submission (Phase III) |
| [docs/qa-mobile-device-lab.md](docs/qa-mobile-device-lab.md) | Mobile device testing guide (Phase III) |
| [docs/plugin-sandbox-security.md](docs/plugin-sandbox-security.md) | Plugin sandbox threat model (Phase III) |
| [docs/research-data-privacy.md](docs/research-data-privacy.md) | Data export/delete/anonymize (Phase III) |
| [docs/sdk/VERSIONING.md](docs/sdk/VERSIONING.md) | SDK versioning policy |
| [docs/sdk/PUBLISHING.md](docs/sdk/PUBLISHING.md) | SDK publishing guide |
| [apps/mobile/README.md](apps/mobile/README.md) | Mobile app setup guide |
| `.pre-commit-config.yaml` | Pre-commit hooks configuration |
| `.vscode/extensions.json` | Recommended VS Code extensions |
| `.vscode/settings.json` | Workspace VS Code settings |
| `scripts/dev.sh` | One-command dev start (API + frontend, hot reload) |

---

## Phases Completed

| Phase | Version | Codename | Key Deliverables |
|-------|---------|----------|------------------|
| A–H (Foundation) | v2.0.0 | Siddhanta | Platform foundation, all 7 engines, SDKs, CI/CD |
| I (Phase I) | v2.1.0 | Vistara | Docs, Shadbala/Ashtakavarga, D3.js charts, research tools, 70 yoga types |
| II (Phase II) | v2.2.0 | Arundhati | Observability, SDK publish, worker pools, AI hardening, developer tooling |
| III (Phase III) | **v2.3.0** | **Lakshmi** | **Mobile apps, plugin CLI, analytics engine, i18n (5 langs), API key auth** |

---

## Out of Scope (Permanently)

Per governance directives and the local-first mandate:
- **Kubernetes / Helm** (removed from pipeline 2026-07-20)
- **Cloud deployment** (AWS/GCP/Azure)
- **Multi-region replication**
- **Hosted plugin marketplace / Stripe payments**
- **SaaS / multi-tenancy**
- **Real-time collaboration** (OT/CRDT, chat, @mentions — deferred from Phase III)
- **Plugin marketplace** (replaced by local plugin directory)
- **Celery async jobs** (replaced by in-process worker pools)
- **Webhook push notifications** (optional add-on, not in scope)
- **Blockchain / crypto integrations**
- **VR/AR visualization**

---

## Recent Documentation Changes

- **2026-07-20 (Phase III complete):** v2.3.0 "Lakshmi" released. React Native mobile app (iOS + Android), plugin CLI with local registry (`apps/cli/astroos-plugin`, `plugins/registry.json`), analytics engine (`apps/api/services/analytics_engine.py` with QueryBuilder + StatisticalEngine), i18n with 5 language translations (`apps/api/i18n/`), API key management docs. AMP-009/010 resolved (PDF/CSV report endpoints fixed, report templates created). Phase IV/V roadmaps removed — they were drafted on old enterprise assumptions. CLAUDE_START_HERE.md rewritten to reflect current architecture.
- **2026-07-20 (Phase II.4 complete):** Local-first worker pools + batch job API — `apps/api/services/worker_pool.py` (cpu/io/ai pools, priority queue, retry/backoff, dead-letter, local queue-depth autoscaling), `POST /api/v1/batch/chart-reports` + monitoring endpoints under `/api/v1/jobs`. 20 new tests. Filed AMP-009 and AMP-010.
- **2026-07-20 (Phase II scope amendment):** Task 6/7/18 (containers, Helm, K8s) permanently removed. Local-first mandate reaffirmed.
- **2026-07-19 (Phase I.1):** Documentation & DX pass. README, `docs/api-reference.md`, `docs/troubleshooting.md`, `docs/contributing.md`, `scripts/dev.sh`.
- **2026-07-19:** All 8 AMPs (AMP-001–AMP-008) resolved. See `architecture/AMP-RESOLUTION-REPORT.md`.

---

*This file is the entry point for all AI-assisted development. Update it when project context changes.*
