# AstroOS Phase I / v2.1.0 Roadmap

> **Version:** v2.1.0 — Phase I
> **Codename:** "Vistara" (Local-First Enhancement)
> **Date:** 2026-07-19
> **Status:** PLANNING

---

## Theme

**Local-First Enhancement.** v2.0.0 delivered a solid, local-first astrology platform. Phase I improves the **user experience, local tooling, documentation, and calculation accuracy** for the single-user personal research platform. All work stays on the local machine: native PostgreSQL, FastAPI + Next.js locally.

**No Kubernetes, no Helm, no cloud deployment, no multi-region.** Those are explicitly out of scope per `CLAUDE_START_HERE.md`.

---

## Operating Model

Unchanged from v2.0.0. Five offices continue with non-overlapping boundaries.

| Office | Owns | Does NOT own |
|--------|------|--------------|
| Engineering (CEO-ENG) | Backend, frontend, SDKs, API layer, DB, CI/CD, testing, performance, security | Architecture decisions, astrology knowledge, benchmarks, research datasets |
| Architecture (CAO) | System architecture, ADRs, RFCs, module boundaries, dependency rules | Implementation |
| Knowledge (CKO) | Ontology, classical texts, catalogues, glossary, cross-references, conflicts, Knowledge Graph | Calculations |
| Benchmark (CBO) | Benchmark specs, gold-standard datasets, accuracy metrics, validation methodology | Algorithm implementation |
| Research Data (CRDO) | Research datasets, metadata, data standards, import pipelines, dataset quality/versioning | Benchmark rules, software implementation |

---

## V2.0.0 Traceability

v2.0.0 completed Phases A–H with:
- 1103 unit tests passing
- Local-first architecture (PostgreSQL, FastAPI, Next.js, Redis optional)
- 15 divisional charts (D1–D60), 6 Dasha systems, 6 Ayanamsas
- Rule Engine with 47 rules
- Knowledge Graph, Research Engine, Report Engine
- Python + TypeScript SDKs (not yet published)

Phase I builds on this foundation with **local-first enhancements only**.

---

## Phases

### Phase I.1 — Documentation & Developer Experience (2 weeks)

**Objectives:**
1. Update all README files with accurate local-first setup instructions.
2. Add comprehensive API documentation (OpenAPI, examples).
3. Improve code docstrings (FastAPI services, Pydantic models).
4. Create troubleshooting guide for common local setup issues.
5. Add local development scripts (dev, test, lint, build).
6. Ensure `CLAUDE_START_HERE.md` is accurate and cross-referenced.

**Deliverable:** `docs/` directory expanded with setup guides, API reference, troubleshooting, contribution guide. `README.md` and `CLAUDE_START_HERE.md` updated inline.

**Acceptance Criteria:**
- New contributor can setup local dev environment in <30 minutes following docs.
- OpenAPI docs at `/api/docs` show all endpoints with example requests/responses.
- All public functions have type hints and docstrings.
- `dev.sh` script starts API + frontend with hot reload.

---

### Phase I.2 — Calculation Accuracy & Precision (2 weeks)

**Objectives:**
1. Verify Swiss Ephemeris integration with real ephemeris data files (`.se1`).
2. Cross-validate D1 chart calculations against known test cases (verified astrologer charts).
3. Implement ephemeris data fallback grace messages (when `.se1` absent).
4. Add Shadbala calculations (6-fold strength) — currently missing.
5. Add Ashtakavarga calculations (bindu, SAMITY) — currently missing.
6. Create precision test suite comparing against published ephemeris tables.

**Deliverable:** `apps/api/services/shadbala_engine.py`, `apps/api/services/ashtakavarga_engine.py`. Updated Swiss Ephemeris wrapper with `.se1` file support. Benchmarks in `tests/precision/`.

**Acceptance Criteria:**
- Planet positions match modified ephemeris data within <1 arc-second.
- Shadbala scores computed for all 9 planets.
- Ashtakavarga bindu count per house matches reference charts.
- Graceful Moshier fallback when `.se1` missing, with version warning.

---

### Phase I.3 — UI/UX Enhancements (2 weeks)

**Objectives:**
1. Build full chart visualization using D3.js (D1, D9, and other vargas).
2. Add interactive Nakshatra/Pada selector with lookup.
3. Implement Dasha timeline visualization (Mahadasha → Pratyantar).
4. Add عدة chart comparison view (side-by-side D1, D9).
5. Improve accessibility (keyboard navigation, ARIA labels).
6. Add dark mode toggle.

**Deliverable:** `/charts` page with D3.js SVG renders. `/charts/compare` page for side-by-side. Enhanced dashboard UI with full timeline visualization.

**Acceptance Criteria:**
- Charts render responsively (mobile + desktop).
- All interactive elements accessible via keyboard.
- Day/night theme persists across sessions (localStorage).
- Timeline shows current Dasha period with countdown.

---

### Phase I.4 — Research Tools (2 weeks)

**Objectives:**
1. Build detailed Research Project UI (create, list, filter, export).
2. Add experiment snapshot comparison tools.
3. Implement export to CSV/JSON with knowledge citations included.
4. Add "research mode" toggle that logs all queries for reproducibility.
5. Create hypothesis validation workflow (flag AI-generated hypotheses for confirmation).

**Deliverable:** `/research/projects` with full CRUD. `/research/snapshots/{id}/compare`. Enhanced `POST /api/v1/workflow/analyze` with `research_mode` flag.

**Acceptance Criteria:**
- Researchers can create projects, capture snapshots, and compare across versions.
- Snapshots export to CSV/JSON with all citations preserved.
- Audit log shows who created which snapshot and when.

---

### Phase I.5 — Enhanced Yoga Detection (2 weeks)

**Objectives:**
1. Add Phase 2 Yogas: Chandra/Navamsa yogas, Nabhasa yogas, Arishta yogas (per `yogas/` roadmap).
2. Implement Yoga strength scoring (0–100 scale based on contributing factors).
3. Add composite yoga detection (yogas formed by multiple planets/houses).
4. Create yoga timeline (when each yoga activates during Dasha periods).
5. Add yoga counter-examples (weakness conditions).

**Deliverable:** `apps/api/services/yogas/phase2/` directory with `chandra_yogas.py`, `nabhasa_yogas.py`, `arista_yogas.py`. Yoga strength calculation in `YogaEngine.evaluate_with_strength()`.

**Acceptance Criteria:**
- All Chandra/Nabhasa/Arishta yogas implemented (30+ new yoga types).
- Yoga strength score computed using planet dignity × house placement × aspected strength.
- Yoga activation times shown in Dasha timeline.
- 100% test coverage on new yoga modules.

---

## Milestones

| Milestone | Criteria | Target |
|-----------|----------|--------|
| M4 | Phase I.1 + I.2 complete | +4 weeks |
| M5 | Phase I.3 complete | +6 weeks |
| M6 | Phase I.4 + I.5 complete | +10 weeks |

---

## Out of Scope (Local-First Mandate)

Per `CLAUDE_START_HERE.md`:
- Docker (optional only; local-first uses native PostgreSQL)
- Kubernetes
- Helm charts
- Cloud deployment (AWS/GCP/Azure)
- Multi-region replication
- Celery background jobs (async can be done via FastAPI background tasks, no separate Redis broker needed)
- Webhook push notifications (optional later, not in Phase I)
- Plugin marketplace
- Mobile SDKs

---

## Governance Rules

1. All changes must respect local-first architecture.
2. No K8s/Helm/Cloud manifests without explicit Architecture Office approval via ADR.
3. New phases require explicit decision recorded in `ASTROOS_V2_STATUS.md`.
4. If `CLAUDE_START_HERE.md` says something is out of scope, it is out of scope.

---

*Last updated: 2026-07-19*