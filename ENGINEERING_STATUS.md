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
| **Warnings** | 101 | ⚠️ Cosmetic (sync tests marked async) |

## Dataset Import Framework

| Component | Status |
|---|---|
| Framework pipeline | ✅ Complete |
| Excel Adapter (generic) | ✅ Complete |
| AstroDatabank Adapter | ✅ Complete |
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

## Warnings (101)

All 101 warnings are identical: `PytestWarning: The test is marked with '@pytest.mark.asyncio' but it is not an async function`.

**Root cause:** Test files use `pytestmark = pytest.mark.asyncio` at module level, which applies to ALL test functions in the file — including synchronous ones. Pytest-asyncio warns about this.

**Affected files:**
- `tests/unit/test_ephemeris_wrapper.py` (~44 sync tests with module-level asyncio marker)
- `tests/unit/test_horoscope_engine.py` (~15 sync tests)
- `tests/unit/test_planet_position_repository.py` (1 sync test)
- Other files with module-level `pytestmark`

**Fix:** Remove `pytestmark = pytest.mark.asyncio` from files where not all tests are async, and add individual `@pytest.mark.asyncio` decorators to async tests only. Alternatively, add `asyncio_mode = auto` (already present in pytest.ini) which should handle this automatically — the warnings indicate the auto mode is being overridden by the explicit module-level marker.

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
| 1 | 101 async-marker warnings (sync tests marked `pytestmark.asyncio`) | Low | Cosmetic only — no behavior change, no test failure | 🔴 Acknowledged |
| 2 | Module-level `pytestmark` in test files with mixed sync/async tests | Low | Same root cause as #1 | 🔴 Acknowledged |
| 3 | `poolclass=NullPool` not used for test engine | Low | No evidence of pool exhaustion; current `QueuePool` works | 🔴 Acknowledged |

> **Treatment:** All three items are tracked as Technical Debt. They do not affect test behavior, test correctness, or pytest compatibility at the current version (pytest 9.1.1, pytest-asyncio 1.4.0). They should be resolved before upgrading pytest or pytest-asyncio to the next major version, as newer versions may change warning behavior.

## Open Decisions

| # | Decision | Status |
|---|---|---|
| 1 | Test data cleanup strategy | ✅ Resolved — `_truncate_committed_data` autouse fixture |
| 2 | Module-level `pytestmark` for sync test files | 🔴 Technical Debt — see above |
| 3 | `poolclass=NullPool` for test engine | 🔴 Technical Debt — no evidence of pool exhaustion |

## Repository Hygiene (2026-07-16)

A repository audit and cleanup pass removed 14 obsolete files (backups, Replit-platform leftovers, stray artifacts, superseded implementation scratch — including the entire `AI_CONTEXT delete it once project is built/` folder) and fixed a hardcoded dev password in `.env.example`. A security audit of `.env`/`.env.example` and `apps/api/security/keys/*.pem` found the committed RSA private key predates the current `.gitignore` rule and remains exposed in git history — rotation/history-purge is recommended but **not yet performed**, pending approval. A `.git` size audit found 816 MB of repo bloat (415 MiB reclaimable via `git gc`, 399 MB LFS cache not currently reclaimable) — a cleanup plan was written but **not executed**.

Full detail: [REPOSITORY_CLEANUP_REPORT.md](REPOSITORY_CLEANUP_REPORT.md), [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md), [GIT_CLEANUP_PLAN.md](GIT_CLEANUP_PLAN.md).

| Follow-up | Priority | Status |
|---|---|---|
| Rotate committed RSA private key / decide on history purge | High | 🔴 Pending approval |
| Run `git reflog expire` + `git gc --prune=now` (≈415 MiB reclaim) | Medium | 🔴 Pending approval |
| Consolidate `ENGINEERING_*.md` vs `architecture/*.md` duplicate doc pairs | Low | 🔴 Not started |
| Commit pending `.replit`/`replit.md`/`replit.nix` deletions and `.env.example` fix | Low | 🔴 Pending your review |

---

*Last updated: 2026-07-16*
