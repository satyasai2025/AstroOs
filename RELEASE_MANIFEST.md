# AstroOS v2.0.0 — Release Manifest

> Status: **RELEASE CANDIDATE — NOT YET CUT.** Nothing in this manifest has been tagged or published. See `GA_RELEASE_GOVERNANCE_AUDIT.md` for the full validation record — all 7 original blockers are fixed, and the full test suite (1759 unit/component + 2 integration + 31 regression) now passes for real against a live database, including 13 real bugs found and fixed along the way. The one remaining item is a real `docker build`, which cannot run in this sandbox (no Docker daemon or WSL distribution present at all).

## Identity

| Field | Value |
|---|---|
| Target version | 2.0.0 |
| Base commit | `d98fd018055b633cdb7256b329a834b3e8e892b5` (currently tagged `v1.0.0-alpha`) |
| Proposed new tag (not created) | `v2.0.0` — see Governance Audit Phase 5 for why a new tag, not moving the existing one |
| Working tree status | 288 uncommitted changes on top of base commit; not yet committed |

## Components in this release

| Component | Path | Version | Build status |
|---|---|---|---|
| API (FastAPI backend) | `apps/api/` | 2.0.0 (`pyproject.toml`) | ✅ Imports & generates OpenAPI (116 paths); dependencies now pinned |
| Web frontend | `apps/web/` | 2.0.0 | ✅ `tsc --noEmit` clean; ✅ `next lint` clean |
| Python SDK | `sdks/python/` | 2.0.0 | ✅ Builds (`python -m build --wheel`) |
| TypeScript SDK | `sdks/typescript/astroos/` | 2.0.0 | ✅ `tsc` builds clean (zod dependency added, camelCase/snake_case field bug fixed) |
| Database migrations | `database/versions/` | 10 revision files, 0001–0010, linear chain | ✅ `alembic heads` — single head `0010` |
| Docker production image | `Dockerfile.prod` | n/a | ⚠️ Still unverified — no Docker daemon in this sandbox; run a real build before GA |
| CI pipeline | `.github/workflows/ci.yml` | n/a | ✅ Valid YAML, 9 steps parse correctly |

## Research/data assets

| Dataset | Status |
|---|---|
| `ASTRO-RS-COHORT-v1.0.0` | Included |
| `ASTRO-SY-RANDOM-v1.0.0` | Included, correctly labeled synthetic |
| `ASTRO-RS-EVENT-v1.0.0`, `ASTRO-RS-HEALTH/WEALTH/SPIRITUAL-v0.1.0` | **Excluded** — fabricated, deleted from working tree (GD-RDO-001). Still present in the `v1.0.0-alpha` tag's history; will not be present once this release is committed and tagged fresh. |
| `GC-MASTER-v1.0.0` | Included |

## Release-blocking defects — status

All 7 originally-listed defects are **fixed and re-verified** (see `GA_RELEASE_GOVERNANCE_AUDIT.md` Post-Resolution Update):

1. ~~`.github/workflows/ci.yml` — invalid YAML~~ → fixed, parses clean.
2. ~~`database/versions/0006_performance_indexes.py` — duplicate/mismatched revision chain~~ → renumbered to `0010`, single linear head.
3. ~~`sdks/typescript/astroos/package.json` — missing `zod`; conflicting untracked manifest~~ → `zod` added, orphaned duplicate manifest deleted, a second masked field-naming bug also found and fixed.
4. ~~`apps/web/src/components/report/ReportExport.tsx` — imports two non-existent/undeclared modules~~ → rewritten to match the codebase's existing conventions (no new dependencies added).
5. ~~No `LICENSE` file~~ → added (MIT).
6. ~~`apps/api/requirements.txt` — zero pinned versions~~ → all 24 pinned to versions verified installed in this environment.
7. ~~Version numbers inconsistent~~ → all 4 manifests now read `2.0.0`.

**Remaining before `READY FOR GA`:**
- ~~Full `pytest` suite run against a live `TEST_DATABASE_URL`~~ → done: 1759 passed, 0 failed (see Governance Audit "Full Test-Suite Validation").
- A real `docker build -t astroos:2.0.0 -f Dockerfile.prod .` on a Docker-capable host — genuinely unrunnable in this sandbox (no Docker daemon, no WSL distributions).

Full detail, evidence, and recommended fix commands: `GA_RELEASE_GOVERNANCE_AUDIT.md`.
