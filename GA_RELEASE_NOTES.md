# AstroOS v2.1.0 GA Release Notes

> **Release Date:** 2026-07-20  
> **Status:** General Availability (GA)  
> **Codename:** "Vistara" (Expansive Enhancement)

---

## Overview

AstroOS v2.1.0 "Vistara" is the first enhancement release following the v2.0.0 GA foundational release. This release delivers **Phase I** of the v2.x roadmap — five workstreams focused on precision, usability, and research capabilities, all within the **local-first** architecture.

All features run entirely on a single machine (PostgreSQL + FastAPI + Next.js + Swiss Ephemeris). No Kubernetes, Helm, Docker, or cloud services required.

---

## What's New in v2.1.0

### Phase I.1 — Documentation & Developer Experience
- **Complete documentation rewrite** for local-first setup
- **`docs/api-reference.md`** — curated API reference with curl examples (65+ endpoints)
- **`docs/troubleshooting.md`** — fixes for common local setup failures
- **`docs/contributing.md`** — contribution guide with conventions and testing
- **`scripts/dev.sh`** — one-command dev start (API + frontend, hot reload)
- Pydantic schema docstrings, improved type hints across all public functions

### Phase I.2 — Calculation Accuracy & Precision
- **Shadbala Engine:** Full 6-fold planetary strength (Naisargika, Dig, Drik, Chesta, Sthana, Kala Bala). All 9 grahas supported.
- **Ashtakavarga Engine:** Bhinnashtakavarga for 7 classical grahas, Sarvashtakavarga (classical total = 337), Shodhana reduction passes (Trikona + Ekadhipatya).
- **Swiss Ephemeris Precision:** Golden-reference precision suite. Planet positions verified <1 arc-second. Graceful Moshier fallback when `.se1` absent.

### Phase I.3 — UI/UX Enhancements
- **D3.js Chart Visualizations:** North Indian diamond-style chart rendering for D1, D9, and other vargas
- **Interactive Nakshatra/Pada Selector** with search and lookup
- **Dasha Timeline Visualization:** Mahadasha → Pratyantar with current period countdown
- **Dark Mode:** Light/dark theme toggle persisted to `localStorage`, respects system `prefers-color-scheme`
- **Chart Comparison:** Side-by-side D1/D9 comparison view
- **Accessibility:** Keyboard navigation, ARIA labels across chart components

### Phase I.4 — Research Tools
- **Research Project UI:** Full CRUD at `/research/projects` (create, list, filter, archive, export)
- **Snapshot Comparison:** Field-level diffing between experiment snapshots
- **CSV/JSON Export:** Each row includes knowledge citations linking to source references
- **Research Mode Toggle:** Per-user setting that logs all queries for reproducibility
- **Hypothesis Validation Workflow:** Flag AI-generated hypotheses → human confirm/reject with reviewer notes

### Phase I.5 — Enhanced Yoga Detection
- **70 registered yogas** across 12 modules (32 new Phase 2 Vistara additions)
- **Phase 2 Yogas:** Chandra/Navamsa (8), Nabhasa (18), Arishta (11), Composite multi-planet (7)
- **Strength Scoring (0–100):** Based on planet dignity × house placement × aspect strength × combustion/retrograde factors
- **Activation Timeline:** Dasha-period correlation showing when each yoga activates
- **Counter-Examples:** Weakness conditions documented for Phase 2 yogas
- **New API Endpoints:** `POST /evaluate/with-strength`, `POST /evaluate/timeline`, `GET /catalog/by-category/{category}`, `POST /evaluate/present-only`

---

## Governing Decisions

- **8 AMPs resolved** (AMP-001 through AMP-008) — all governance issues closed
- **Local-first mandate enforced** — K8s/Helm tasks permanently removed from scope
- **5-office boundaries upheld** — Engineering, Architecture, Knowledge, QA, Governance each operated within their remit
- **All 34 ADR/EAL documents remain frozen** — no architecture decisions superseded

---

## Quality Metrics

| Metric | Value |
|--------|-------|
| Unit tests | 1,573 passing |
| Yoga detection tests | 205 (across 11 files) |
| Precision tests (ephemeris) | <1 arc-second |
| Test categories | Unit, integration, precision |
| Python version | 3.13 |
| Database | PostgreSQL 15+ (native) |

---

## Architecture

```
User → Next.js (Frontend) → FastAPI (Backend) → PostgreSQL (Data Store) → Swiss Ephemeris (Calculations)
```

All components run locally on a single machine. Redis optional (JWT denylist only, gracefully disabled when absent).

---

## Upgrade Notes

### From v2.0.0 (GA) to v2.1.0

1. Pull latest code
2. Apply Alembic migration: `alembic upgrade head` (creates `research_mode_settings`, `research_query_logs`, `hypothesis_validations` tables)
3. No breaking API changes — all v2.0.0 endpoints remain functional
4. New endpoints require no additional configuration

### From earlier alpha versions

Must first upgrade to v2.0.0 GA, then apply v2.1.0 migration.

---

## Out of Scope (Local-First Mandate)

The following remain out of scope per project governance:
- Kubernetes / Helm charts (optional reference only)
- Cloud deployment (AWS/GCP/Azure)
- Multi-region replication
- Celery async jobs
- Webhook push notifications
- Mobile SDKs
- Plugin marketplace

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
- [PHASE_I_COMPLETION_REPORT.md](PHASE_I_COMPLETION_REPORT.md) — Detailed Phase I deliverable report
- [GOVERNANCE_AUDIT_REPORT.md](GOVERNANCE_AUDIT_REPORT.md) — Governance compliance report
