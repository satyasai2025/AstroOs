# AstroOS v2.0 Changelog

> Dated log of v2 work. Untagged in-progress work is logged by date; tagged releases (see `ASTROOS_V2_RELEASE_PLAN.md`) get their own entry when cut.

## 2026-07-17 (continued, 7) — correction to the entry below

The "(continued, 6)" entry immediately below states GD-RDO-001's fabricated data was "confirmed never part of any commit, including the tagged v1.0.0-alpha." **That was true only for the originally-scoped file.** Verifying release impact afterward surfaced three more fabricated datasets — `research-data/research/{health,wealth,spiritual}/ASTRO-RS-{HEALTH,WEALTH,SPIRITUAL}-v0.1.0/` (183 records each, filtered exports of the same fabricated source, one with 44 rows still carrying unfilled `{source}`-style template placeholders naming Lincoln, Newton, and Hawking) — that **were** already committed and **are** present in `d98fd01`, the commit tagged `v1.0.0-alpha`. Deleted these three under the same disposition decision already given for the original file. The already-published `v1.0.0-alpha` tag contains fabricated data as of this writing; a working-tree deletion cannot retroactively clean an existing commit/tag without a history rewrite, which was not performed. Full detail: `research-data/governance/GD-RDO-001_RS_EVENT_DATA_INTEGRITY.md` §7, and the corrected `ALPHA_RELEASE_READINESS_REPORT.md`.

## 2026-07-17 (continued, 6)

**GD-RDO-001 investigated and closed. Alpha Release Readiness Report produced. Major discovery: `v1.0.0-alpha` is already tagged.**

- Investigated `GD-RDO-001` from source (repository, code, tests, governance docs) rather than trusting the roadmap's prior framing, per explicit instruction. Confirmed: zero code or test in `apps/`/`tests/` references the fabricated RS-EVENT `v1.0.0` tree; it was untracked in git from the moment it was discovered and never part of any commit.
- Found the likely reason the fabrication exists: `research-data/STATUS.md`'s own Milestone M4 gate reads "RS-EVENT v1.0.0 with ≥1,000 verified events" — the fabricated file's 1,098-record, self-claimed-verified shape matches that gate almost exactly. Recorded as a process-integrity note on the gate itself (a bare count + self-reported status is satisfiable by exactly this shortcut), not just a one-off data problem.
- Presented three disposition options (delete / relabel-as-synthetic / quarantine) to the repository owner, since the finding's own prior write-up explicitly deferred this as a data-governance call, not an engineering one. **Decision: delete.** Executed: `research-data/research/event/ASTRO-RS-EVENT-v1.0.0/` removed in full (CSV, metadata.json, 2 generator scripts). Verified zero code/git impact.
- **While verifying release readiness, discovered `v1.0.0-alpha` already exists as a git tag** (`d98fd01`, tagged directly by the repository owner via `git tag`, 2026-07-17, entirely outside this Claude Code session — no `git tag`/`commit`/`push` has ever been run here, per standing instruction). Confirmed via `git ls-tree` that this tag predates and does not include: the Workflow Orchestrator, the frontend dashboard/analysis UI, the geocoding feature, RBAC, or this session's M1 gap closures — all of that still sits uncommitted. Also confirmed the tagged commit includes `FOUNDATION_RELEASE_REVIEW.md` with its own unmodified "NOT READY FOR FOUNDATION RELEASE" verdict, never updated before tagging even though 2 of its 4 blocking items (RSA key, RS-COHORT dedup) were fixed by that same commit.
- Added a dated addendum to `FOUNDATION_RELEASE_REVIEW.md` (preserving its original 2026-07-16 text rather than rewriting it) reconciling each of its 4 blocking items against current reality.
- Produced `ALPHA_RELEASE_READINESS_REPORT.md` — the authoritative current readiness assessment, recommending against moving/re-tagging the existing `v1.0.0-alpha` (tags are immutable pointers) and instead committing the current working tree and cutting a new tag (`v1.0.0-alpha.1` or `v2.0.0-alpha.1`) once the repository owner is ready — a decision this session does not make unilaterally. Confirms no code/data/security blocker prevents Phase B (Research Engine) from starting now.
- Updated every governance document that referenced `GD-RDO-001` or assumed no `v1.0.0`-series tag existed: `research-data/governance/GD-RDO-001_RS_EVENT_DATA_INTEGRITY.md`, `research-data/STATUS.md`, `research-data/INDEX.md`, `ASTROOS_V2_ROADMAP.md`, `ASTROOS_V2_STATUS.md`, `ASTROOS_V2_RELEASE_PLAN.md`, `ASTROOS_V2_INDEX.md`.

## 2026-07-17 (continued, 5)

**M1 milestone completed to 9/10 criteria — Research Data correlation and report citation-merging closed.**

- Closed M1 criterion 8 (Correlate Research Data): added an optional `research_project_id` field to `WorkflowAnalysisRequest` (`apps/api/schemas/workflow.py`). When supplied, `WorkflowOrchestrator.analyze()` (`apps/api/services/workflow_orchestrator.py`) captures the full computed result — chart, yogas, shadbala, ashtakavarga, dasha tree, vargas, timeline, verification — as an `AstrologicalSnapshot` into that Research project via `ResearchEngine.capture_snapshot`, returning the new `research_snapshot_id` field in the response. Off by default: most analyses aren't research and shouldn't silently accumulate snapshots in a project. Raises a clean 422 if the project id doesn't exist (reusing the router's existing `ValueError` → 422 mapping) rather than surfacing a raw DB foreign-key error.
- Closed M1 criterion 9 (produce a cited report): `ReportEngine.build_chart_report` (`apps/api/services/report_engine.py`) now accepts an optional `citations` tuple and appends a "Knowledge Citations" section directly into `ChartReport.sections` when non-empty, following the exact same conditional-section pattern already used for `timeline`/`verification`/`stats`. `WorkflowOrchestrator` passes its already-computed `knowledge_citations` straight into this call — citations are now part of the report document itself, not just a sibling field on the API response.
- **Found and fixed a real, previously-dormant bug** surfaced only by live end-to-end testing of this change: `ResearchRepository.save_snapshot` (`apps/api/repositories/research_repository.py`) called `.value` on `YogaResult.strength`, but `YogaStrength` is a plain `Literal["full", "partial", "cancelled"]` type alias, not an enum — `.value` doesn't exist on a `str`. This code path had never run live before; the Research router's own snapshot-capture endpoint only ever passed `chart_id`+`label` (see that router's docstring), never real yoga data, so the bug was latent since whenever this repository method was written.
- Verified live end-to-end against the database: registered a user, created a Research project, ran `POST /workflow/analyze` with `research_project_id` set, confirmed `research_snapshot_id` came back non-null and matched a real row visible via `GET /research/projects/{id}/snapshots`.
- Deliberately did not add a project-picker UI to `apps/web`'s `BirthDetailsForm` for this — a full Research project management UI is Phase B's "Research Dashboard" deliverable, not a Phase A polish item; the frontend TypeScript types (`apps/web/src/lib/types.ts`) were kept in sync with the new API fields regardless, so the contract is accurate even before that UI exists.

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
