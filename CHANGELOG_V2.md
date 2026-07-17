# AstroOS v2.0 Changelog

> Dated log of v2 work. Untagged in-progress work is logged by date; tagged releases (see `ASTROOS_V2_RELEASE_PLAN.md`) get their own entry when cut.

## 2026-07-17 (continued, 4)

**Phase A objective 2 (frontend integration) — substantially complete. AstroOS Platform Alpha deliverable reached.**

- Built the Unified Analysis Pipeline UI in `apps/web`: `/dashboard` page, `BirthDetailsForm`, a 10-tab `AnalysisResults` container (Chart/Vargas/Dasha/Yogas/Strength/Transits/Rules/Knowledge/Verification/Report panels), a `useAnalyzeWorkflow()` TanStack mutation hook calling `POST /api/v1/workflow/analyze` directly (no more per-engine calls from the client), and an `AppShell` auth guard redirecting unauthenticated users to `/login`.
- A structured bug report was raised mid-build claiming the Ascendant calculation was wrong and release-blocking. Investigated independently: the app's output matched a from-scratch raw Swiss Ephemeris call (bypassing all AstroOS code) to 4 decimal places on JD, ayanamsa, Moon, and Ascendant. **No defect found** — see `ASTROOS_V2_STATUS.md`'s "Ascendant-correctness investigation" section for the full writeup, including the quadrant-selection mistake in the ad hoc verification script that had made it look otherwise at first.
- Ran a stabilization pass on `BirthDetailsForm` per explicit request: split the single `datetime-local` field into separate Birth Date and Birth Time (with seconds) controls; added `BirthPlaceSearch` (debounced Nominatim-backed search-as-you-type with a results dropdown) that auto-populates latitude/longitude/IANA timezone/UTC offset/DST via two new endpoints, `GET /api/v1/geocode/search` and `GET /api/v1/geocode/timezone` (`apps/api/domain/geocoding.py`, `apps/api/services/geocoding_service.py`, `apps/api/routers/geocoding.py`); kept a manual-coordinate-entry override for advanced/research users; added a resolved-location validation summary (place or manual label, coordinates, timezone, UTC offset, DST flag) shown before a user can submit.
- Found and fixed two real bugs surfaced only by live end-to-end testing (not previously possible to catch — see below):
  - `column books.deleted_at does not exist` — migration `0004` had explicitly deferred adding `deleted_at`/`updated_at` to `books`/`verses`/`karakatvas`/`transits`/`research_snapshots` "to whichever migration accompanies that engine," and no later migration ever did. Fixed with new migration `database/versions/0007_knowledge_research_transit_audit_columns.py`, applied and verified against the live schema.
  - `[SSL: CERTIFICATE_VERIFY_FAILED]` on the geocoding provider call — root cause was Avast Antivirus's local HTTPS-inspection proxy injecting its own root CA, which `certifi`'s bundle doesn't include even though the OS store does. Fixed properly (not via `verify=False`) using the `truststore` package to make Python's `ssl` module use the OS-native trust store; added `httpx.AsyncClient(verify=truststore.SSLContext(...))` to `apps/api/main.py`'s app-state lifespan.
- **This is the first entry in this changelog verified against a genuinely live PostgreSQL database and a real running frontend+backend**, not just static compilation/import checks — a live Postgres instance was discovered running in this environment (correcting a standing false assumption in prior entries and in `ASTROOS_V2_STATUS.md`) and used for real user registration, login, and full pipeline execution through the actual UI.
- Known caveat carried forward: the public Nominatim instance used for geocoding has a ~1 req/sec usage policy — fine for development, needs a self-hosted instance or paid provider before production traffic.

## 2026-07-17 (continued, 2)

**Phase A objective 4 (auth/RBAC) — substantially complete.**

- Added `require_role(*roles)` / `require_authenticated` / `require_researcher` / `require_admin` to `apps/api/dependencies.py`, built on top of the existing `get_current_user_from_bearer` (bad/missing token → 401 there; wrong role → 403 in the new check).
- Applied gating at the router level in `apps/api/main.py`'s `app.include_router(..., dependencies=[...])` calls — a single policy declaration per router rather than touching every endpoint function: authenticated-only for the chart-computation/product routers, researcher-or-admin for Research and Statistics, admin-only for Admin.
- Knowledge is mixed (public reads, researcher-gated writes) — gated per-endpoint directly in `routers/knowledge.py` for its 10 write endpoints (create/update/delete across books/verses/rules/karakatvas) instead of at the router level.
- `dataset_import` (a pre-existing v1 router) was deliberately left ungated — outside this pass's scope, tracked as a known gap in `ASTROOS_V2_STATUS.md`.
- Verified: full `apps/api` tree compiles, `apps.api.main:app` imports and generates a valid OpenAPI schema (95 endpoints, unchanged count — gating doesn't add/remove routes). Runtime enforcement not exercised — no live DB in this environment, same standing caveat as the rest of this changelog.

## 2026-07-17 (continued)

**Phase A objective 3 (connect Knowledge/Rule/Report Engines) — substantially complete. M1 milestone substantially advanced.**

- Built the Workflow Orchestrator (`apps/api/services/workflow_orchestrator.py`) — the first genuine cross-engine service-layer orchestrator in the codebase, composing Chart → Vargas → Dasha → Yoga → Shadbala → Ashtakavarga → Transit → Facts → Rule Engine → Knowledge → Verification (if events exist) → Report into one pipeline.
- Added `POST /api/v1/workflow/analyze` (`apps/api/routers/workflow.py` + `apps/api/schemas/workflow.py`), reusing 7 existing routers' own serializer functions rather than re-deriving them.
- This closes 2 of M1's previously-unmet criteria outright (enter birth details once; apply Rule Engine) and upgrades a 3rd (produce a cited report, now built from real Timeline/Verification data instead of placeholders) — see `ASTROOS_V2_MILESTONES.md` for the full criterion-by-criterion update.
- Benchmark validation remains an explicit `not_implemented` placeholder in the response (Phase C hasn't started) — not silently omitted.
- Research Data correlation (M1 criterion 8) is not yet wired into this pipeline — tracked as the next gap, not silently dropped.
- Verified: full `apps/api` tree compiles, `apps.api.main:app` imports and generates a valid OpenAPI schema (95 endpoints, no duplicates). No live-database run possible in this environment — same standing caveat as the rest of this changelog.

## 2026-07-17

**Phase A objective 1 (API exposure) — substantially complete.**

- Added 13 new API routers + schemas: Ashtakavarga, Shadbala, Yoga, Transit, Timeline, Knowledge, Research, Statistics, Report, Export, Visualization, Admin, AI — wired into `apps/api/main.py`. HTTP surface grew from 17 to 87 endpoints.
- Ran an 8-angle API contract review (correctness, removed-behavior, cross-file tracing, reuse, simplification, efficiency, altitude, conventions) across the new routers; confirmed and fixed 10 findings, including two that made new endpoints fail on every call (`TransitEngine()` missing its wrapper arg in `/ai/read-transit`; `AdminEngine.list_users()` awaiting a non-awaitable).
- Fixed the Admin pagination `total` count (was reporting page size) and Ashtakavarga's 4x redundant bindu-table recomputation per request, both via backward-compatible, additive changes to existing engine methods.
- Rotated the compromised RSA JWT-signing key (gitignored, no git-history impact).
- Reconciled the RS-COHORT duplicate dataset (Engineering's Candidacy copy vs. Research Data's promoted Stable v1.0.0 copy) — declared the Research Data copy canonical, fixed cross-references, marked the Engineering copy superseded without deleting it.
- Discovered and documented a data-integrity finding on RS-EVENT's `v1.0.0` file (template-generated data falsely labeled as curated/verified) — recorded as open governance decision `GD-RDO-001`, not yet resolved.
- Created this v2 governance document set (`ASTROOS_V2_ROADMAP.md`, `STATUS.md`, `INDEX.md`, `RELEASE_PLAN.md`, `MILESTONES.md`, this changelog) per the v2 vision's "New Governance" section.

**Explicitly not done yet:** frontend integration (Phase A objective 2), cross-engine wiring for Knowledge/Rule/Report (objective 3), auth/role-gating completion (objective 4), any work on Phases B–H, and the `v1.0.0-foundation` tag (paused — see `ASTROOS_V2_RELEASE_PLAN.md`).

---

*Format: newest entry at top. Add a new dated section per work session; add a tagged-release section (e.g. `## v2.0.0-alpha.1 — YYYY-MM-DD`) when a release is actually cut.*
