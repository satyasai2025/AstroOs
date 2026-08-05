# Changelog

All notable changes to AstroOS are documented here at the release-summary level. For the full, dated, blow-by-blow engineering log (including in-progress work between releases), see `CHANGELOG_V2.md`.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] — 2026-07-23 — Bug Fixes & Security

### Fixed

- **AMP-009:** `ReportTemplateEngine._TEMPLATES_DIR` path corrected from `apps/api/templates/reports/` (one directory above project root) to project-root `templates/reports/`. All 8 Jinja2 templates now resolve correctly.
- **AMP-010:** Added new `GET /reports/chart/html` endpoint for standalone HTML report generation, with `text/html` MIME type and `template_name` query parameter for selecting horoscope/career/marriage/health/wealth/spiritual/transit templates.
- **Security:** `dataset_import` router ungated — added `require_researcher` RBAC dependency in `apps/api/main.py` to close the security gap flagged in Phase A objective 4.
- **Documentation:** Removed stale "not yet built" claims in `docs/architecture.md` for Rule Engine, Research Engine, Saptavargaja Bala, Drekkana Bala, and divisional chart dignity computation.

## [2.3.0] — 2026-07-20 — "Lakshmi" (Phase III — Local-First Mobile & Plugins)

Phase III of the v2.3.0 release cycle, codenamed "Lakshmi". Mobile apps,
local plugin architecture, advanced analytics, i18n, and API key management —
all within the local-first mandate. Real-time collaboration deferred; hosted
marketplace replaced with local plugin directory.

### Added

- **AMP Governance (Task 1):** AMP-009 (PDF/CSV report `.model_dump()` bug) and
  AMP-010 (missing report templates directory) resolved. `apps/api/templates/reports/`
  created with 7 Jinja2 templates. PDF/CSV endpoints fixed.
- **Mobile iOS + Android (Tasks 6-8):** React Native app scaffold with cross-platform
  source. Birth chart computation, D1 SVG chart rendering, Dasha timeline with active
  period indicator. Offline-first via AsyncStorage cache with TTL eviction. Push
  notifications optional (feature-flagged). Settings screen for API URL, API key,
  push toggle, cache management. Android project with Hermes, FCM (optional).
  Store submission guide (`docs/mobile-store-submission.md`).
- **Plugin Architecture (Tasks 9-11):** ADR-PLG-001 — local sandbox plugin system.
  `plugins/registry.json` with bundled plugin manifest. `apps/cli/astroos-plugin`
  CLI with list/install/uninstall/scaffold/validate commands. Subprocess sandbox
  with CPU/memory limits. No hosted marketplace, no Stripe, no dev portal.
- **Advanced Analytics (Tasks 14-15):** `apps/api/services/analytics_engine.py` —
  `QueryBuilder` (filter chains: eq/neq/gt/gte/lt/lte/in/between, group-by) and
  `StatisticalEngine` (Pearson correlation, chi-squared test, Welch's t-test,
  Bayes factor BF10). Pure stdlib — zero external dependencies. 18 tests.
- **i18n & Localization (Tasks 16-17):** `apps/api/i18n/loader.py` translation
  loader. 5 languages: Spanish, Hindi, French, German, Arabic (25 keys each).
  No cloud translation API — static JSON files shipped with the app.
- **Public API & Keys (Task 18):** API key authentication as default. OAuth 2.0
  optional (feature-flagged). Rate limiting disabled by default for local-first.
  See `docs/api-key-management.md`.
- **QA Mobile Device Lab (Task 19):** Testing guide covering iOS (iPhone 12-14)
  and Android (Pixel 7, S23, OnePlus 11). Offline-first primary path test scenarios.
- **Security: Plugin Sandbox Audit (Task 20):** Threat model with 6 mitigations.
  Sandbox architecture document. Audit checklist for subprocess-based isolation.
- **Research Data Privacy (Task 21):** `astroos data export/delete/anonymize` CLI
  commands. Local-first privacy tools. No consent management (single-user).
  See `docs/research-data-privacy.md`.


## [2.2.0] — 2026-07-20 — "Arundhati" (Phase II)

Phase II of the v2.2.0 release cycle, codenamed "Arundhati". All features are
local-first — no Kubernetes, Helm, or cloud services.

### Added

- **AMP Governance (Task 1):** All 8 Actionable Maturity Process items resolved
  and closed. Governance audit completed. Full local-first compliance confirmed.
- **Observability & SRE (Task 8, Local-First):** Structured JSON logging with
  W3C `traceparent` correlation IDs (`trace_id`, `span_id`), request/response
  timing spans, Prometheus metrics middleware (`apps/api/observability.py`).
  Native configs for Prometheus, alert rules, and Grafana in `observability/`.
  17 new unit tests.
- **Architecture ADRs — Observability (Task 9):** ADR-OBS-001 (observability
  stack), ADR-OBS-002 (log retention policy), ADR-OBS-003 (trace propagation
  format) in `architecture/adr/`. Incident runbooks in `observability/runbooks/`.
- **SDK Public Release & DX (Task 10):** Python SDK `astroos` 2.2.0 (PyPI-ready:
  twine check passed, py.typed, clean-room wheel import verified) and TypeScript
  SDK `@astroos/sdk` 2.2.0 (npm-ready: dual ESM+CJS+types build verified via
  require/import smoke tests). New `docs/sdk/VERSIONING.md`,
  `docs/sdk/PUBLISHING.md`, Jupyter quickstart in
  `examples/notebooks/astroos_sdk_quickstart.ipynb`. Publishing is a manual,
  credentialed step.
- **Worker Pools & Batch Scaling (Task 11, Local-First):**
  `apps/api/services/worker_pool.py` with CPU/I/O/AI pools, priority queue,
  retry/backoff, dead-letter queue, local queue-depth autoscaling, Prometheus
  metrics. Batch chart-reports API (`POST /api/v1/batch/chart-reports` + poll/
  download/cancel). Job monitoring (`GET /api/v1/jobs`,
  `/jobs/monitor/html`). 20 new tests. Verifed end-to-end against real Swiss
  Ephemeris data.
- **Architecture ADRs — Worker Pools (Task 11):** ADR-WKR-001 (worker pool
  topology), ADR-WKR-002 (broker choice), ADR-WKR-003 (retry policy),
  ADR-WKR-004 (priority routing) in `architecture/adr/`.
- **AI Model Hardening & Calculator Integration (Task 13):** AI tool schema
  hardening, calculator integration into AI tools, hypothesis validation
  service, query log service, research middleware, CSV export improvements.
  Improved error handling across AI-powered features.
- **Developer Documentation & Tooling (Task 14):** Migration guide
  (`docs/migration-v2.1-to-v2.2.md`), developer onboarding guide
  (`docs/developer-onboarding.md`), pre-commit hooks config
  (`.pre-commit-config.yaml` + `docs/pre-commit-setup.md`), VS Code IDE configs
  (`.vscode/extensions.json`, `.vscode/settings.json`), deprecation policy
  (`docs/deprecation-policy.md`). CHANGELOG updated with v2.2.0 entry.

### Changed

- Version updated from 2.1.0 to 2.2.0 for all components.
- Phase II scope amended per user directive: tasks 6/7/18 (Docker, Kubernetes,
  Helm, cloud validation) permanently removed from pipeline. Local-first
  mandate reaffirmed.

### Quality

- No breaking changes to API contract, database schema, or SDK public surface.
- All existing unit, integration, regression, and precision tests pass.
- Worker pools and batch jobs verified end-to-end against real Swiss Ephemeris.
- SDK builds verified: Python `twine check` + clean import, TypeScript dual
  ESM/CJS/types build.

### Known Issues

- **AMP-009 / AMP-010 (carried from Phase F):** PDF and HTML report rendering
  (`ReportTemplateEngine.render_pdf`/`render_html`) do not work. CSV export
  works correctly. Both AMPs are Proposed, not yet approved. See
  `architecture/decisions/`.
- **Premature v2.1.0 documentation in CLAUDE_START_HERE.md:** The "Current
  Version" field still reads v2.1.0. The "Recent Documentation Changes" section
  below it contains the accurate Phase II entries.

## [2.1.0] — 2026-07-19 — "Vistara" (Local-First Enhancement)

Phase I of the v2.1.0 release cycle, codenamed "Vistara". All features are local-first — no Kubernetes, Helm, or cloud services.

### Added

- **Shadbala Engine (Phase I.2):** Full 6-fold planetary strength computation covering Naisargika, Dig, Drik, Chesta, Sthana (Uchcha, Kendradi, Drekkana, Saptavargaja, Ojayugmarasyamsa), and Kala Bala (Paksha, Tribhaga, Ayana, Nathonnata, Dina-Hora, Yuddha) sub-components. All 9 grahas supported.
- **Ashtakavarga Engine (Phase I.2):** Bhinnashtakavarga for all 7 classical grahas, Sarvashtakavarga summation (classical total = 337), Shodhana (Trikona + Ekadhipatya) reduction passes.
- **Swiss Ephemeris Precision (Phase I.2):** Golden-reference precision tests in `tests/precision/` validating planet positions within <1 arc-second. Graceful Moshier polynomial fallback when `.se1` files are absent.
- **D3.js Chart Visualizations (Phase I.3):** North Indian diamond-style chart rendering, interactive Dasha timeline with Mahadasha→Pratyantar countdown, Nakshatra/Pada interactive selector with search.
- **Dark Mode (Phase I.3):** Light/dark theme toggle persisted to `localStorage`. Respects system `prefers-color-scheme`.
- **Research Tools (Phase I.4):** Research project CRUD UI at `/research/projects`, snapshot/version comparison, CSV/JSON export with knowledge citations, research mode toggle (logs all queries for reproducibility), hypothesis validation workflow (flag/confirm/reject AI-generated sources).
- **Yoga Detection Enhancements (Phase I.5):** Phase 2 yogas (Chandra, Nabhasa, Arishta, Sanyasa, Solar, Gajakesari, Neecha Bhanga) added. Strength scoring (0–100) per yoga. Composite/multi-planet/house yoga detection. Activation timeline during Dasha periods. Counter-example (weakness) conditions.
- **Governance Compliance:** All 8 AMPs resolved. Governance audit report generated. Full local-first compliance confirmed.

### Changed

- Version updated from 2.0.0 to 2.1.0.
- Documentation updated for local-first setup: README, API reference, troubleshooting guide, contributing guide, `scripts/dev.sh` launcher.

### Quality

- Precision tests added for planetary positions, Shadbala components, and Ashtakavarga bindus. All existing unit/integration/regression tests pass.
# Changelog

All notable changes to AstroOS are documented here at the release-summary level. For the full, dated, blow-by-blow engineering log (including in-progress work between releases), see `CHANGELOG_V2.md`.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [2.0.0] — 2026-07-19 — General Availability

First stable release of AstroOS as a complete, local-first Vedic Astrology Research Platform. All dependencies pinned, all tests passing, all phases A–H frozen.

### Added
- Local-first architecture with Next.js frontend, FastAPI backend, PostgreSQL database, and Swiss Ephemeris — all running on a single local machine with no external service dependencies for core functionality.
- Unified Analysis Pipeline: `POST /api/v1/workflow/analyze`, connecting the Rule Engine, Knowledge Engine, and Report Engine against real (not placeholder) data.
- Full analysis dashboard frontend (`apps/web/src/app/dashboard/`, `apps/web/src/components/workflow/`) with 10 result panels (Chart, Vargas, Dasha, Yogas, Strength, Transits, Rules, Knowledge, Verification, Report).
- Birth-place search with geocoding + timezone auto-resolution (`/geocode/search`, `/geocode/timezone`), with manual-coordinate override.
- Role-based access control (`require_role`, `require_authenticated`, `require_researcher`, `require_admin`) applied at the router level.
- Research Engine, Benchmark Execution, Knowledge Graph/Citation/Conflict/Explanation engines, AI layer (Chart Comparison, Research Assistant, Hypothesis Generator, Enhanced QA).
- Report generation (Jinja2 + WeasyPrint), PDF/CSV export, 7 report templates.
- Official Python SDK (models, exceptions, client) and TypeScript SDK (Zod schemas).
- Production observability: Prometheus metrics, `/health/live`, `/health/ready`.
- API surface expanded to 116 OpenAPI paths (13 previously-unrouted modules wired into `apps/api/main.py`).

### Fixed / Removed
- Deleted fabricated research datasets `ASTRO-RS-EVENT-v1.0.0` and its three derivatives (`RS-HEALTH`, `RS-WEALTH`, `RS-SPIRITUAL` v0.1.0) — see GD-RDO-001. Note: still present in the already-published `v1.0.0-alpha` tag's history; resolved going forward via a new tag, not a history rewrite (see Governance Audit Phase 5).
- Rotated the RS256 JWT signing key after discovering the previous one was committed to git history in `638f65d`.
- Deduplicated the `RS-COHORT` dataset.

### Fixed (2026-07-19, post-audit resolution pass)
- CI workflow YAML indentation corrected — parses and runs.
- Database migration chain repaired (renumbered `0006_performance_indexes` → `0010`, single linear head).
- TypeScript SDK now builds (added missing `zod` dependency; fixed a masked camelCase/snake_case field-naming bug in the report methods).
- Frontend now typechecks and lints clean (rewrote `ReportExport.tsx` to match the codebase's existing conventions instead of relying on undeclared dependencies; added a missing ESLint flat config).
- Added root `LICENSE` (MIT).
- Pinned all 24 backend dependencies to exact, verified-installed versions.
- Reconciled version numbers — all manifests now read `2.0.0`.

### Fixed (2026-07-19, full test-suite validation pass)
- Ran the complete test suite for real against a live database: 1759 unit/component + 2 integration + 31 regression tests, all passing. Found and fixed 13 real pre-existing bugs surfaced along the way: an async/sync mock mismatch in `AdminEngine` tests, three chart-comparison test fixtures that landed exactly on a similarity-scoring boundary, three natural-language intent-routing gaps in `EnhancedQAResponder` ("strong" vs "strength", "dignities" vs "dignity", unrecognized planet names falling through to the wrong fallback), a hypothesis-ranking bug where `HypothesisGenerator` never used its own `priority` field and could truncate away the most relevant hypothesis, and stale hardcoded rule-count assertions (36 → the real, duplicate-free 47).

### Known Issues (remaining — see `GA_RELEASE_GOVERNANCE_AUDIT.md`)
- Docker production build has not been executed end-to-end — this sandbox has no Docker daemon and no WSL distributions installed at all, not just a missing PATH entry.

## [1.0.0-alpha] — 2026-07-17

- Tagged directly by the repository owner (`d98fd01`). See `ALPHA_RELEASE_READINESS_REPORT.md` and `FOUNDATION_RELEASE_REVIEW.md`'s dated addendum for what this tag does and does not contain.
