# AstroOS Engineering Roadmap

> Authoritative build plan: modules, milestones, governance decisions.

## Phase A — Foundation & Core Engines (Modules 1–12)

**Status: ✅ Complete**

- Module 1: Foundation
- Module 2: Astronomy Foundation (Swiss Ephemeris)
- Module 3: Birth Chart Engine
- Module 4: Divisional Charts (15 vargas)
- Module 5: Graha (Planet) Engine
- Module 6: House Engine
- Module 7: Aspect Engine
- Module 8: Yoga Engine
- Module 9: Shadbala Engine
- Module 10: Ashtakavarga Engine
- Module 11: Transit Engine
- Module 12: Astrology Ontology

## Phase B — Logic & Events (Modules 13–15)

**Status: ✅ Complete**

- Module 13 Phase 1: Rule Engine Base
- Module 13 Phase 2: Rule Engine Advanced
- Module 14: Event Engine
- Module 15: Timeline Engine

## Phase C — Research & Reporting (Modules 16–20)

**Status: ✅ Complete**

- Module 16: Verification Engine
- Module 17: Research Engine
- Module 18: Statistics Engine
- Module 19: Report Engine
- Module 20: Knowledge Engine

## Phase D — Delivery & AI (Modules 21–27)

**Status: ✅ Complete**

- Module 21: Export Engine
- Module 22: Visualization Engine
- Module 23: Admin Portal
- Module 24: AI Engine
- Module 25: SDK & Public API
- Module 26: Monitoring & Deployment
- Module 27: Production Readiness

## Phase E — Test Infrastructure

**Status: ✅ Complete (2026-07-16)**

| Task | Priority | Status |
|---|---|---|
| E1: Fix test isolation failure (`test_repeated_d1_requests_reuse_birth_chart_row`) | High | ✅ Done — `_truncate_committed_data` autouse fixture (see ENGINEERING_STATUS.md Defect Status) |
| E2: Clean up 101 async-marker warnings | Low | ✅ Done — removed redundant module-level `pytestmark = pytest.mark.asyncio` from 16 test files; `asyncio_mode = auto` already handles async detection without it |
| E3: Remove temp debug files (`_*.py`) | Done | ✅ |
| E4: Fix CI missing `TEST_DATABASE_URL` | High | ✅ Done — `.github/workflows/ci.yml` set `DATABASE_URL` but never `TEST_DATABASE_URL`, which `tests/conftest.py` hard-requires; CI would have failed at collection. Added the missing env var. |

### E1 Implementation Options (resolved — Option B taken)

| Option | Complexity | Impact | Notes |
|---|---|---|---|
| A: Add `TRUNCATE` at end of `birth_chart_id` cleanup | Low | Fixes isolation | Requires session-scoped cleanup |
| B: Add session-scoped cleanup fixture using `test_engine` | Low | Fixes isolation + future-proof | ✅ **Taken** — cleanest approach |
| C: Make `birth_chart_id` not commit (use flush only) | Low | Fixes isolation | May break tests that depend on committed data |

## Phase F — Documentation

**Status: ✅ Complete**

- ENGINEERING_INDEX.md — Complete cross-reference
- ENGINEERING_STATUS.md — Current status
- ENGINEERING_ROADMAP.md — Build plan (this file)

## Milestones

| Milestone | Date | Criteria |
|---|---|---|
| M1: PostgreSQL test DB operational | ✅ Jul 2026 | Test database created, user configured |
| M2: ENUM types created in test DB | ✅ Jul 2026 | All 7 ENUM types working |
| M3: Single engine/session architecture | ✅ Jul 2026 | No duplicate fixtures, single test_engine |
| M4: Test suite green (0 failures) | ✅ Jul 2026 | 0 failures, 1529 passed |
| M5: Warning-free test run | ✅ Jul 2026 | 0 async-marker warnings (was 101) — verified via `pytest --collect-only`, full live run blocked locally by an unrelated `.env` credential placeholder |
| M6: Module 14 tests passing | ✅ Jul 2026 | All 25 event repository/router tests pass |
| M7: Full regression clean for 3 runs | ✅ Jul 2026 | 3 consecutive passes with 0 failures |

## Governance Decisions

| # | Decision | Rationale |
|---|---|---|
| G1 | PostgreSQL-only test database (no SQLite) | Application uses PostgreSQL-specific types (UUID, ENUM, TSVECTOR) |
| G2 | Session-scoped event loop | Matches fixture architecture with session-scoped engine |
| G3 | Single authoritative `test_engine` | Eliminates InterfacError from competing engine/session stacks |
| G4 | `asyncio_mode = auto` in pytest.ini | Simplifies async test declaration |
| G5 | ENUM creation in `_ensure_enums()` before `create_all()` | Required because model definitions use `create_type=False` |

---

*Last updated: July 2026*
