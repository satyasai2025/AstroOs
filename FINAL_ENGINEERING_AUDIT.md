# AstroOS Final Engineering Audit

> Scope, per approved revised Engineering Request: CI reliability review, API functionality verification, engineering integration validation (imports, dependencies, package structure, configuration), and this report.
> Explicitly out of scope: Phase E (already complete, not reopened), architecture redesign, new features, governance documents outside Engineering.
> Date: 2026-07-16

---

## 1. CI Reliability Review

**File reviewed:** [.github/workflows/ci.yml](.github/workflows/ci.yml)

Verified before making any change:

| Check | Result |
|---|---|
| `database/alembic.ini` `script_location = database` resolves correctly against CI's working directory (repo root) | ✅ Correct |
| `data/ephemeris/*.se1` binary data files are committed and present (integration tests need them) | ✅ Present |
| `apps/api/pytest.ini` marker config (`integration` marker, `not integration` default) | ✅ Correct |
| `apps/api/security/generate_keys.py` writes keys to an absolute path derived from `__file__`, independent of CI's cwd | ✅ Correct |
| `TEST_DATABASE_URL` present in workflow env (prior fix, confirmed still in place) | ✅ Present |
| `apps/web/package.json` has `typecheck`/`lint` scripts the workflow calls | ✅ Present |
| pnpm workspace (`pnpm-workspace.yaml` + root `pnpm-lock.yaml`) installs correctly when invoked from `apps/web` subdirectory | ✅ Correct (pnpm resolves the workspace root automatically) |

**Findings, not changed (recommendations only):**

| # | Finding | Why not fixed now |
|---|---|---|
| 1 | All Python dependencies in `apps/api/requirements.txt` use floating `>=` version bounds | Repinning to exact versions is a larger dependency-management decision (could shift many transitive versions at once) — flagging for a separate, explicitly-scoped Engineering Request rather than bundling into this audit |
| 2 | Frontend job has no pnpm store cache (`actions/setup-node`'s `cache: pnpm` needs pnpm on `PATH` before that step, which requires reordering `corepack enable` ahead of `setup-node`) | Step-reordering risk vs. minor CI speed gain; recommend as a follow-up, not a same-audit change |

**Fixes applied (low-risk, config-only):**

- Added `concurrency: { group: ci-${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }` — stale runs on rapid pushes no longer queue up.
- Added `permissions: contents: read` at the workflow level — narrows the default `GITHUB_TOKEN` scope.
- Added `timeout-minutes: 20` (backend) / `timeout-minutes: 15` (frontend) — bounds worst-case hang time instead of the GitHub default (360 min).

---

## 2. API Functionality Verification

**Method:** static compilation (`py_compile`) of all 150 `.py` files under `apps/api`, individual `importlib.import_module` of each, then a full `FastAPI` app import (`apps.api.main:app`) with a syntactically-valid but unreachable `DATABASE_URL`, followed by OpenAPI schema generation to enumerate the actual exposed HTTP surface.

| Check | Result |
|---|---|
| `py_compile` across all 150 files | 0 errors |
| Individual import of all 150 modules | 0 errors |
| `apps.api.main:app` import (lifespan not invoked, no live DB/Redis needed for import) | ✅ Succeeds |
| OpenAPI schema generation | ✅ Succeeds, 17 endpoints enumerated |

**Confirmed live HTTP surface** (`/api/v1/*` + `/api/healthz`):

```
POST /api/v1/auth/register        POST /api/v1/divisional/all
POST /api/v1/auth/login           POST /api/v1/divisional/{varga}
POST /api/v1/auth/refresh         POST /api/v1/dasha/vimshottari
POST /api/v1/auth/logout          POST /api/v1/dasha/yogini
GET  /api/v1/auth/me              POST /api/v1/dasha/ashtottari
POST /api/v1/horoscope/d1         POST /api/v1/dasha/kalachakra
GET  /api/v1/events               POST /api/v1/dasha/chara
POST /api/v1/events               POST /api/v1/dasha/narayana
GET/PATCH/DELETE /api/v1/events/{event_id}
GET  /api/healthz
```

**Key finding — API surface gap:** Only 5 of the ~20 domain areas listed as "Complete" in [ENGINEERING_INDEX.md](ENGINEERING_INDEX.md) have a registered `APIRouter`: **Auth, Horoscope (D1), Divisional Charts, Dasha, Events**. A repo-wide search for `APIRouter(` confirms these are the *only* five router definitions in the codebase.

The following modules are fully implemented (domain objects + services + repositories) and covered by unit/integration tests, but have **no HTTP endpoint** — they are reachable only as internal Python APIs, not from outside the process: Ashtakavarga, Shadbala, Yoga, Transit, Timeline, Ontology, Rule Engine, Verification, **Research Engine**, Statistics, Report, **Knowledge Engine**, Export, Visualization, Admin Portal, AI Engine, SDK & Public API.

This is a scope/completeness gap, not a defect — the code that exists is correct and import-clean. It directly affects the mission's Knowledge Office / Research Data Office integration-validation objective: those engines are *implemented* and *internally correct*, but not yet *API-integrated*. No router code was added here (out of scope: "do not create new features" / "do not redesign architecture") — flagging for a dedicated, explicitly-approved Engineering Request if external/API access to these engines is required.

---

## 3. Engineering Integration Validation

**Package structure:** every subdirectory under `apps/api/` and `packages/` has an `__init__.py`; no missing-package gaps found.

**Dependency completeness:** cross-referenced every third-party top-level import across `apps/api/**/*.py` against `apps/api/requirements.txt`.

| Finding | Status |
|---|---|
| `apps/api/services/dataset_import/adapters/excel_adapter.py` imports `openpyxl`, which was **not declared** in `requirements.txt`. It happened to be installed in this dev environment already, masking the gap — a clean CI/production install (`pip install -r apps/api/requirements.txt`) would raise `ModuleNotFoundError` the first time that code path executes. | ✅ Fixed — added `openpyxl>=3.1.0` to [apps/api/requirements.txt](apps/api/requirements.txt) |

**Configuration consistency:** every field in `Settings` (`apps/api/config.py`) has a matching, correctly-named entry in `.env.example`, and vice versa — no drift.

**Build configuration:** root [pyproject.toml](pyproject.toml) declared `build-backend = "setuptools.backends._legacy:_Backend"`, which does not exist in real `setuptools` (verified: `ModuleNotFoundError: No module named 'setuptools.backends'`). Not currently exercised by the documented workflow (CI installs via `requirements.txt`, not `pip install .`), but would break immediately on any `pip install .` / `python -m build`.

| Finding | Status |
|---|---|
| Invalid `build-backend` in `pyproject.toml` | ✅ Fixed — corrected to `setuptools.build_meta` |

**Knowledge Office / Research Data Office / Benchmark Office integration:** `apps/api/domain/knowledge.py`, `apps/api/domain/research.py`, `apps/api/repositories/knowledge_repository.py`, `apps/api/repositories/research_repository.py`, and their corresponding services all import cleanly and are internally consistent (research domain objects correctly reference ashtakavarga, dasha, divisional, events, horoscope, shadbala, timeline, verification, and yoga domain types). No "Benchmark Office" module was found under `apps/api/` by name — if this refers to the Statistics Engine (Module 19) or a planned future module, it exists at the domain/service level under the same API-surface-gap caveat as §2.

---

## 4. Summary of Changes Made in This Audit

| File | Change | Risk |
|---|---|---|
| `.github/workflows/ci.yml` | Added `concurrency`, `permissions: contents: read`, `timeout-minutes` on both jobs | Low — config-only, no behavior change to test execution |
| `apps/api/requirements.txt` | Added missing `openpyxl>=3.1.0` | Low — declares an already-used, already-installed dependency |
| `pyproject.toml` | Fixed invalid `build-backend` to `setuptools.build_meta` | Low — corrects a non-functional value; not exercised by current CI/dev flow |

No test files, domain logic, service logic, or router logic were modified. No new endpoints, modules, or abstractions were introduced.

## 5. Open Items Requiring a Separate Engineering Request

1. Wire HTTP endpoints for the 16 domain areas currently without an `APIRouter` (Knowledge, Research, Statistics, Report, Export, Visualization, Admin, AI, SDK, Ashtakavarga, Shadbala, Yoga, Transit, Timeline, Ontology, Verification) — if external access to these engines is required.
2. Pin `apps/api/requirements.txt` to exact versions (currently all `>=`).
3. Reorder CI frontend job steps to enable pnpm store caching.
4. Carried over from `ENGINEERING_STATUS.md` (unchanged by this audit, still pending your approval): RSA key rotation/history purge, `git gc --prune=now` (~415 MiB reclaim), `ENGINEERING_*.md` vs `architecture/*.md` doc consolidation.

---

*Audit performed: 2026-07-16*
