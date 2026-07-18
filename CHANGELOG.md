# Changelog

All notable changes to AstroOS are documented here at the release-summary level. For the full, dated, blow-by-blow engineering log (including in-progress work between releases), see `CHANGELOG_V2.md`.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] — targeting 2.0.0

Everything below is currently in the working tree on top of commit `d98fd01` (tag `v1.0.0-alpha`) and **has not yet been committed or tagged**. See `RELEASE_MANIFEST.md` for build status per component and `GA_RELEASE_GOVERNANCE_AUDIT.md` for the full validation record.

### Added
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
