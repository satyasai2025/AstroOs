# AstroOS Engineering Status

> Current status of all modules and test infrastructure as of July 2026.

## Test Suite Status

| Metric | Count | Trend |
|---|---|---|
| **Passed** | **1529** | ✅ Stable |
| **Failed** | **0** | ✅ Fixed |
| **Errors** | **0** | ✅ Clean |
| **Skipped** | **17** | ⏸ Expected (8 env + 9 xlsx path) |
| **Duration** | 39.22s | ✅ Fast |
| **Warnings** | 0 | ✅ Fixed 2026-07-16 (was 101, sync tests marked async) |

> **Note on Passed/Failed/Duration figures above:** these carry over from the last live run and were **not** re-executed on 2026-07-16 — the local `.env` has an unfilled `<db-password>` placeholder, so there's no working DB connection in this environment. The Warnings fix was verified statically instead: `py_compile` on all 16 edited files, plus `pytest --collect-only` against the real `pytest.ini`, which collects all 1566 non-integration tests with zero async-marker warnings. Someone with real DB credentials should re-run the full suite to confirm Passed/Failed/Duration are unchanged (the fix only removed a marker line — no test logic changed — so no regression is expected).

## Dataset Import Framework

| Component | Status |
|---|---|
| Framework pipeline | ✅ Complete |
| Excel Adapter (generic) | ✅ Complete |
| Cohort Excel Adapter | ✅ Complete |
| Schema Mapper | ✅ Complete |
| Validator (L1/L2) | ✅ Complete |
| Normalizer | ✅ Complete |
| Deduplicator | ✅ Complete |
| Quality Scorer (RDO §3) | ✅ Complete |
| Exporter (CSV/JSON/JSONL) | ✅ Complete |
| Import Validation Report | ✅ Produced |
| Unit tests (22 passing) | ✅ Complete |
| Architecture docs | ✅ Complete |

## Defect Status

### Fixed: `test_repeated_d1_requests_reuse_birth_chart_row`

**Category:** Test Infrastructure (fixture cleanup)
**File:** `tests/integration/test_persistence_integration.py`
**Behavior:** Passes in isolation, failed only in full suite.
**Root cause:** `birth_chart_id` fixture committed data to the database. The root `db_session` fixture rolls back uncommitted changes but does not undo committed rows. Birth chart data from other tests in the same session accumulated, causing this test's assertion (which expects exactly 1 row) to fail.
**Fix:** Added `_truncate_committed_data` autouse fixture to `tests/integration/conftest.py` that truncates all transactional tables (`birth_charts`, `events`, `dashas`, `planet_positions`, `houses`, `divisional_charts`, `divisional_planet_positions`) before and after each integration test.

## Warnings (0 — fixed 2026-07-16)

Previously 101 identical warnings: `PytestWarning: The test is marked with '@pytest.mark.asyncio' but it is not an async function`.

**Root cause:** 16 test files used `pytestmark = pytest.mark.asyncio` at module level, which applies to ALL test functions in the file — including synchronous ones. Pytest-asyncio warns about this. The marker was always redundant: `asyncio_mode = auto` in `pytest.ini` already auto-detects `async def test_*` functions without any marker.

**Fixed files (16):** `test_admin_engine.py`, `test_auth_service.py`, `test_birth_chart_repository.py`, `test_dasha_repository.py`, `test_divisional_repositories.py`, `test_aspect_engine_integration.py`, `test_ephemeris_wrapper.py` (41 sync tests — the marker was doing nothing useful, file has zero async tests), `test_ephemeris_service.py` (11 sync tests, zero async), `test_events_router.py`, `test_event_repository.py`, `test_persistence_integration.py`, `test_horoscope_engine.py` (23 sync tests, zero async), `test_house_repository.py`, `test_knowledge_engine.py`, `test_research_engine.py`, `test_planet_position_repository.py`.

**Fix applied:** Deleted the module-level `pytestmark = pytest.mark.asyncio` line from all 16 files. No decorators were added — `asyncio_mode = auto` handles async detection on its own.

**Verification:** All 16 edited files pass `python -m py_compile`. `pytest -c apps/api/pytest.ini -m "not integration" --collect-only` against the real config collects all 1566 non-integration tests with **zero** `PytestWarning`/async-marker output (previously 101). A full live run (pass/fail counts) could not be re-verified in this environment: the local `.env` still has the `<db-password>` template placeholder unfilled, so there's no working `DATABASE_URL`/`TEST_DATABASE_URL` to connect with locally. This is a pre-existing local-environment gap, unrelated to this fix — the actual database credential needs to be filled in by whoever owns that secret.

**Related fix:** `.github/workflows/ci.yml` was missing `TEST_DATABASE_URL` entirely (only `DATABASE_URL` was set), which would have made CI fail at test collection every run, since `tests/conftest.py` hard-requires it. Added the missing env var pointing at the same ephemeral CI Postgres service.

## Module Status

### Modules 1–27: All Complete

All 27 modules are implemented and have test coverage. See `ENGINEERING_INDEX.md` for the full module inventory.

| Area | Modules | Coverage |
|---|---|---|
| Foundation & Auth | 1-2 | Unit tests |
| Chart Computation | 3-4 | Unit + Integration |
| Planetary Analysis | 5-11 | Unit + Integration |
| Ontology & Rules | 12-13 | Unit + Integration |
| Events & Timeline | 14-15 | Unit + Integration |
| Research & Knowledge | 16-20 | Unit + Integration |
| Export & Visualization | 21-22 | Unit + Integration |
| AI, SDK, Ops | 23-27 | Unit + Integration |

## Test Infrastructure Status

| Component | Status | Notes |
|---|---|---|
| PostgreSQL test database | ✅ | `astroos_test` user, `astroos_test_db` database |
| ENUM type creation | ✅ | 7 types created before `create_all()` |
| Schema lifecycle | ✅ | Created at session start, dropped at session end |
| Event loop scope | ✅ | Session-scoped, configured via `asyncio_default_fixture_loop_scope` |
| Engine ownership | ✅ | Single `test_engine` in root conftest |
| Session ownership | ✅ | Root `db_session` for all tests |
| Integration fixtures | ✅ | `birth_chart_id` uses dedicated session from `test_engine` |
| Duplicate module dir | ✅ | Removed |

## Technical Debt

| # | Issue | Priority | Impact | Status |
|---|---|---|---|---|
| 1 | 101 async-marker warnings (sync tests marked `pytestmark.asyncio`) | Low | Cosmetic only — no behavior change, no test failure | ✅ Fixed 2026-07-16 |
| 2 | Module-level `pytestmark` in test files with mixed sync/async tests | Low | Same root cause as #1 | ✅ Fixed 2026-07-16 |
| 3 | `poolclass=NullPool` not used for test engine | Low | No evidence of pool exhaustion; current `QueuePool` works | 🔴 Acknowledged |

> **Treatment:** Item 3 remains tracked as Technical Debt — no evidence of pool exhaustion, so left as-is. It should be resolved before upgrading pytest or pytest-asyncio to the next major version, as newer versions may change warning behavior.

## Open Decisions

| # | Decision | Status |
|---|---|---|
| 1 | Test data cleanup strategy | ✅ Resolved — `_truncate_committed_data` autouse fixture |
| 2 | Module-level `pytestmark` for sync test files | ✅ Resolved 2026-07-16 — removed from all 16 files |
| 3 | `poolclass=NullPool` for test engine | 🔴 Technical Debt — no evidence of pool exhaustion |

## Inbound Requests (from Other Offices)

| ID | Request | Requesting Office | Priority | Status |
|---|---|---|---|---|
| **ER-001** | Fix `ASPECT-SPECIAL-GRAHA` ontology description drift in `apps/api/services/ontology_registry.py`'s `_populate_aspect()` — description string omits Rahu/Ketu even though `aspect_engine.py`'s `SPECIAL_ASPECTS` implements special aspects for both nodes. Documentation-accuracy fix only, no behavior change. | Knowledge Office | Low | 🟡 In Progress — work session started 2026-07-16 |
| **ER-002** | Investigate `ontology_registry.py`: intentionally unused, awaiting integration, obsolete, or should another module already depend on it? | Direct request | — | 🔵 **CLOSED** (2026-07-16) — investigation complete, no code changed. See [ONTOLOGY_REGISTRY_INTEGRATION_ASSESSMENT.md](ONTOLOGY_REGISTRY_INTEGRATION_ASSESSMENT.md) for full findings. Per instruction, `ontology_registry.py`/`ai_engine.py` were **not** modified; the dependency-model decision was referred to the Architecture Office as **[AMP-008](architecture/decisions/AMP-008-ontology-registry-dependency-model.md)**. A new Engineering Request will be opened only if/when AMP-008 is approved. |

## Repository Hygiene (2026-07-16)

A repository audit and cleanup pass removed 14 obsolete files (backups, Replit-platform leftovers, stray artifacts, superseded implementation scratch — including the entire `AI_CONTEXT delete it once project is built/` folder) and fixed a hardcoded dev password in `.env.example`. A security audit of `.env`/`.env.example` and `apps/api/security/keys/*.pem` found the committed RSA private key predates the current `.gitignore` rule and remains exposed in git history — rotation/history-purge is recommended but **not yet performed**, pending approval. A `.git` size audit found 816 MB of repo bloat (415 MiB reclaimable via `git gc`, 399 MB LFS cache not currently reclaimable) — a cleanup plan was written but **not executed**.

Full detail: [REPOSITORY_CLEANUP_REPORT.md](REPOSITORY_CLEANUP_REPORT.md), [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md), [GIT_CLEANUP_PLAN.md](GIT_CLEANUP_PLAN.md).

| Follow-up | Priority | Status |
|---|---|---|
| Rotate committed RSA private key / decide on history purge | High | 🔴 Pending approval |
| Run `git reflog expire` + `git gc --prune=now` (≈415 MiB reclaim) | Medium | 🔴 Pending approval |
| Consolidate `ENGINEERING_*.md` vs `architecture/*.md` duplicate doc pairs | Low | 🔴 Not started |
| Commit pending `.replit`/`replit.md`/`replit.nix` deletions and `.env.example` fix | Low | 🔴 Pending your review |

## Final Engineering Audit (2026-07-16)

Full detail: [FINAL_ENGINEERING_AUDIT.md](FINAL_ENGINEERING_AUDIT.md). Scope: CI reliability, API functionality verification, and engineering integration validation (imports, dependencies, package structure, configuration).

| Area | Result |
|---|---|
| CI reliability | ✅ Reviewed — added `concurrency`, `permissions: contents: read`, `timeout-minutes` to `.github/workflows/ci.yml` (config-only, no test-execution changes) |
| API import health | ✅ All 150 `apps/api` modules + 7 `packages/shared` modules import cleanly; `apps.api.main:app` imports and generates a valid OpenAPI schema (17 endpoints) |
| Dependency completeness | ✅ Fixed — `openpyxl` was used by the Excel dataset-import adapter but missing from `apps/api/requirements.txt`; added |
| Build configuration | ✅ Fixed — `pyproject.toml` had an invalid `build-backend` (`setuptools.backends._legacy:_Backend`, a nonexistent module); corrected to `setuptools.build_meta` |
| Package structure | ✅ No missing `__init__.py` anywhere under `apps/api` or `packages` |
| Configuration consistency | ✅ `Settings` fields in `apps/api/config.py` and `.env.example` are in 1:1 sync |

**Key finding — API surface gap:** Only 5 of ~20 "Complete" domain areas (Auth, Horoscope, Divisional Charts, Dasha, Events) have a registered `APIRouter`. Ashtakavarga, Shadbala, Yoga, Transit, Timeline, Ontology, Rule Engine, Verification, Research Engine, Statistics, Report, Knowledge Engine, Export, Visualization, Admin Portal, AI Engine, and SDK & Public API are fully implemented and tested at the domain/service/repository layer but have no HTTP endpoint — internally correct, not yet externally reachable. This is a scope gap, not a defect; see the audit's §5 for follow-up.

**Status as of 2026-07-17: closed** — see "API Surface Expansion" below. This finding is preserved as-written for historical record; it no longer reflects current state.

## API Surface Expansion (2026-07-17)

Per [API_EXPOSURE_ASSESSMENT.md](API_EXPOSURE_ASSESSMENT.md)'s classification, all 13 "Candidate public API" modules now have a registered `APIRouter`: Ashtakavarga, Shadbala, Yoga, Transit, Timeline, Knowledge, Research, Statistics, Report, Export, Visualization, Admin Portal, AI Engine. HTTP surface grew from 17 to **87 endpoints**. The 6 "Intended internal" / "Supporting library" modules that assessment said should stay unrouted (Astronomy Foundation, House/Bhava Engine, Ontology, Rule Engine substrate, Verification, SDK domain objects) remain unrouted, per that same classification.

| Area | Result |
|---|---|
| New routers/schemas | ✅ 13 router files + 13 schema files added under `apps/api/routers/` and `apps/api/schemas/` |
| `apps/api/main.py` wiring | ✅ All 13 registered via `app.include_router(..., prefix="/api/v1")` |
| Verification method | `py_compile` on every new/touched file, individual module import checks, full `apps.api.main:app` import + `app.openapi()` schema generation (87 endpoints enumerated) — **no live-DB test run**, same local-environment gap noted throughout this document (`TEST_DATABASE_URL` unavailable) |
| API contract review | ✅ 8-angle diff review performed; 10 findings confirmed and fixed — see below |

**Contract review fixes applied:**
- `ai.py` — `TransitEngine()` was missing its required `wrapper` arg (100% failure on `/ai/read-transit`); fixed
- `admin_engine.py` — `list_users()` awaited a non-awaitable (`.scalars().all()`, 100% failure on `GET /admin/users`); `get_user()` passed a raw `uuid.UUID` where `UserRepository.get_by_id` expects a `UserId` value object (100% failure on `GET /admin/users/{id}`); both fixed
- `admin.py` / `admin_engine.py` — pagination `total` was reporting page size, not the true matching-row count; added `AdminEngine.count_users()` (real `COUNT` query, same filter as `list_users`) and wired it in
- `ashtakavarga_engine.py` / `ashtakavarga.py` — `compute_all`/`sarvashtakavarga` endpoints recomputed the full bindu table up to 4x per request; added optional pass-through params (`bhinna_results`, `sarvashtakavarga`) to `compute_sarvashtakavarga`/`compute_reduced_bhinnashtakavarga`/`verify_checksum`, fully backward-compatible (existing single-arg call sites in `tests/unit/test_ashtakavarga_engine.py` and `tests/integration/test_ashtakavarga_engine_integration.py` unaffected); router now computes the bindu table once per request instead of 4x
- `yoga.py` — `total_evaluated` was computed after the `only_present` filter, silently reporting the post-filter count instead of the true evaluated count; fixed
- `knowledge.py` (schema + router) — `RuleResponse`/`KarakatvaResponse` omitted the `source` citation even though the domain objects and create requests carry it; added
- `ai.py` — `/ai/explain-yoga` had no try/except around a call that can raise `ValueError`, unlike the equivalent `/yoga/evaluate/{yoga_id}` (inconsistent 500 vs. 422); fixed
- `knowledge.py` schema / `report.py` schema — two fields dropped from the API contract instead of fixed at the data layer: `rule_definition_id` (no matching column on `RuleModel` — would require a migration) and `chart_ids` on `ComparisonReportResponse` (`D1Chart` has no `id` field — `ReportEngine.build_comparison_report`'s `chart_ids` was structurally always empty)

**Not done in this pass:** no auth/role-gating added to any new router (matches pre-existing convention); nothing run against a live database.

---

*Last updated: 2026-07-17*
