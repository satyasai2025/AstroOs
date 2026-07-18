# AstroOS v2.0.0 — Release Notes

> **Status: Release candidate, not yet published.** All release-blocking code/config defects found in the initial audit have been fixed and re-verified (2026-07-19), and the full test suite now passes for real against a live database (1759 unit/component + 2 integration + 31 regression, 0 failures) — see `GA_RELEASE_GOVERNANCE_AUDIT.md`. One verification step remains genuinely unrun in this sandbox: a real Docker build, since no Docker daemon or WSL distribution exists on this machine at all.

## Highlights

AstroOS v2.0.0 completes the platform's Phase A–H roadmap: a Unified Analysis Pipeline that takes birth details through ephemeris calculation, divisional charts, dasha systems, yoga/strength analysis, rule-based interpretation, knowledge-graph correlation, and report generation, exposed through a 116-endpoint API, a full web dashboard, and official Python and TypeScript SDKs.

- **Unified Analysis Pipeline** — one endpoint (`/api/v1/workflow/analyze`) drives the Rule Engine, Knowledge Engine, and Report Engine together against real computed data.
- **Research & Knowledge intelligence** — Knowledge Graph, citation tracking, conflict detection, and plain-language explanation of astrological findings.
- **AI-assisted analysis** — chart comparison, a research assistant, hypothesis generation, and an enhanced Q&A engine.
- **Geocoding-backed birth details** — search a birth place by name and get latitude/longitude/timezone/DST auto-filled, with a manual override for advanced use.
- **Reporting** — PDF and CSV export across 7 report templates.
- **SDKs** — official Python and TypeScript clients, both building cleanly.
- **Production readiness** — Prometheus metrics and liveness/readiness health checks.

## What changed since `v1.0.0-alpha`

`v1.0.0-alpha` (tagged 2026-07-17, commit `d98fd01`) predates the dashboard frontend, the workflow orchestrator, the geocoding feature, RBAC, and the fabricated-dataset cleanup described below — all of that is new in this release. Full component-by-component detail: `RELEASE_MANIFEST.md`.

## Data integrity note

During preparation of this release, a fabricated research dataset (`ASTRO-RS-EVENT-v1.0.0`) and three datasets derived from it were found to invent specific, false claims about real historical figures. All four have been deleted from the codebase (see `research-data/governance/GD-RDO-001_RS_EVENT_DATA_INTEGRITY.md` for the full record). **These files are still reachable in the git history of the existing `v1.0.0-alpha` tag** — v2.0.0 will be cut as a new tag on a clean commit rather than by altering that existing tag, so no history rewrite is required to ship a clean v2.0.0.

## Known issues resolved before this candidate

- CI pipeline YAML was invalid — fixed, now parses and runs.
- The database migration chain had a duplicate/broken revision — fixed, single linear head (`0010`).
- The TypeScript SDK did not compile — fixed (missing `zod` dependency plus a masked field-naming bug).
- The frontend did not typecheck — fixed (rewrote the offending component to match existing conventions).
- No LICENSE file was present — added (MIT).
- Backend dependencies were unpinned — all 24 now pinned to verified versions.
- The full `pytest` suite (1759 unit/component + 2 integration + 31 regression tests) now passes against a live database — 13 real bugs found along the way (async/sync mock mismatch, chart-comparison boundary-value fixtures, three Q&A intent-routing gaps, a hypothesis-ranking bug, and stale hardcoded rule counts) were fixed, not just re-asserted.

## Known issues still open — resolve before tagging `v2.0.0`

- The production Docker build has not been verified end-to-end — this sandbox has no Docker daemon and no WSL distributions installed at all.

See `GA_RELEASE_GOVERNANCE_AUDIT.md` for the complete evidence trail.

## Upgrade notes

No prior GA release exists to upgrade from — `v1.0.0-alpha` was an internal/alpha checkpoint. This will be the first General Availability release once the known issues above are closed.
