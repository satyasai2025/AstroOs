# AstroOS Persistence Layer — Architecture & Test Coverage Report

**Scope:** Persistence for the existing D1, Divisional, and Dasha engines.
**Status:** Complete, smoke-tested end-to-end against real PostgreSQL 16.
**Date:** 2026-07-10

---

## 1. Executive Summary

The persistence layer requested in the original task is implemented, unit-tested,
integration-tested, and has now been verified against a **real PostgreSQL 16
instance** (not just the SQLite test fixture) via a full live smoke test:
server started, all endpoints hit over HTTP, database inspected directly with
`psql` to confirm the rows the API claims to have saved are actually there.

Three real, pre-existing bugs were found and fixed along the way — none of
them introduced by this work, but all of them blocking it:

| # | Bug | Where found |
|---|-----|-------------|
| 1 | `dasha_type` enum missing `chara`/`narayana`; `dashas.lord` too narrow for Yogini/Rashi names | Design review before writing `DashaRepository` |
| 2 | `ReferenceBase`/`AstroBase` used two disconnected `MetaData` registries, breaking `Base.metadata.create_all()` | Building the SQLite test fixture |
| 3 | `houses`/`planet_positions`/`divisional_planet_positions`/`dashas`/`divisional_charts` missing audit columns (`created_at`/`updated_at`/`deleted_at`); `combustion_orb_deg` too narrow for its real value range (0–180°, not <100°) | **Live smoke test against real Postgres** — neither the SQLite fixture nor unit tests could have caught this |

Bug #3 is the most important one to flag: it only surfaces when you write
through the real Alembic-migrated schema, which is exactly why the live smoke
test mattered — every unit and integration test was passing (406/406) while
this bug was still live, because the SQLite test schema is built from the
Python ORM models directly (`Base.metadata.create_all()`), not from the hand
written migration SQL. The two schemas had quietly drifted apart.

**Current state:** all four migrations (0001–0004) apply cleanly to a fresh
database; all 6 API endpoints (D1, divisional single, divisional all, and all
6 dasha systems) return `200` and persist correctly; re-requesting the same
subject reuses one `birth_charts` row instead of duplicating it. **This has
since been independently reproduced on the actual target machine** (see
§8) — migrations applied, server started, a live `Chara` dasha request
persisted, and the row was confirmed directly in PostgreSQL.

---

## 2. Architecture

```
Input (birth datetime, lat/lon, ayanamsa, house system)
   │
   ▼
Swiss Ephemeris  (ephemeris_wrapper.py — untouched)
   │
   ▼
Calculation  (generate_d1() / compute() / compute_*() — untouched, still
              offloaded via asyncio.to_thread since they're blocking C calls)
   │
   ▼
Persistence  (new — async, DB-only, no thread offload needed)
   │
   ▼
Response  (unchanged request/response schemas)
```

**Layering respected:** Router → Service (engine) → Repository → ORM Model,
matching the project's existing Clean Architecture rule. Engines depend on
repository *interfaces* (duck-typed, optional constructor args), not on
SQLAlchemy directly.

**Six repositories**, one per table family:

| Repository | Table(s) | Write pattern |
|---|---|---|
| `BirthChartRepository` | `birth_charts` | `get_or_create` (dedup on birth input) + `update_d1_summary` |
| `PlanetPositionRepository` | `planet_positions` | delete-then-insert (9 rows) |
| `HouseRepository` | `houses` | delete-then-insert (12 rows) |
| `DivisionalChartRepository` | `divisional_charts` | delete-then-insert (1 row per varga) |
| `DivisionalPlanetRepository` | `divisional_planet_positions` | bulk insert (9 rows per varga) |
| `DashaRepository` | `dashas` | delete-then-insert, recursive tree with client-generated UUIDs |

**Engine changes:** `generate_d1()`, `compute()`/`compute_all()`, and all six
`compute_*()` dasha methods are **byte-for-byte unchanged**. Each engine
gained one or two new async methods (`persist_d1`, `persist_chart`/
`persist_all`, `persist_tree`) and optional repository constructor
arguments (default `None`), so every pre-existing single-argument
construction (`HoroscopeEngine(wrapper)`) still works.

**One `birth_charts` row per subject.** D1, divisional, and dasha requests
for the same birth input resolve to the same row (verified live: 1 row after
8 separate requests in the smoke test). A D1 request additionally fills in
that row's summary columns; a divisional- or dasha-only request leaves them
`NULL` until a D1 request for the same subject arrives.

---

## 3. Schema Fixes (Migrations 0003 & 0004)

### 0003 — Dasha Persistence Fixes
- `dasha_type` enum: added `'chara'`, `'narayana'` (was missing 2 of 6 systems the engine already computes and the API already exposes).
- `dashas.lord`: widened from the 9-planet `graha` enum to `VARCHAR(40)` — it holds Graha names (Vimshottari/Ashtottari), Yogini names (Yogini), or Rashi names (Kalachakra/Chara/Narayana), per the domain model's own docstring.

### 0004 — Audit Column Completeness
Found via live smoke test, not by any test suite:
- `planet_positions`, `houses`, `divisional_planet_positions` were missing **all three** of `created_at`/`updated_at`/`deleted_at`.
- `dashas` was missing `updated_at`/`deleted_at`.
- `divisional_charts` was missing `deleted_at`.
- `combustion_orb_deg` (`planet_positions`) was `NUMERIC(6,4)` (max ~100°) but holds a true 0–180° angular distance from the Sun — widened to `NUMERIC(9,6)`.

**Not fixed (explicitly out of scope):** `transits`, `books`, `verses`,
`karakatvas`, `research_snapshots` have the identical missing-audit-column
gap, but nothing writes to them yet (no Transit/Research/Knowledge Engine
exists), so fixing them is deferred to whichever module builds on top of
them.

### Also fixed: `ReferenceBase`/`AstroBase` metadata split
`signs`/`nakshatras`/`padas` (`ReferenceBase`) and everything else
(`AstroBase`) were two separate `DeclarativeBase` classes with two separate
`MetaData` registries — meaning `planet_positions.nakshatra_id`'s foreign key
into `nakshatras` could never be resolved by `Base.metadata.create_all()`.
Fixed by sharing one `MetaData`. No column or table shape changed; Alembic
was unaffected either way since it creates tables explicitly, not via
`create_all()`.

---

## 4. Live Smoke Test Results

Performed against a real PostgreSQL 16 instance (not SQLite), all four
migrations applied from a clean database, real API server, real HTTP
requests, direct `psql` verification.

| Step | Result |
|---|---|
| `alembic upgrade head` (0001→0004, clean DB) | ✅ Applied cleanly |
| `GET /api/healthz` | ✅ 200, `mode: swiss_ephemeris`, `official_data: true` |
| `POST /horoscope/d1` | ✅ 200 (after fixes) |
| `POST /divisional/D9` | ✅ 200 |
| `POST /divisional/all` (15 vargas) | ✅ 200 |
| `POST /dasha/vimshottari` | ✅ 200 |
| `POST /dasha/yogini` | ✅ 200 |
| `POST /dasha/ashtottari` | ✅ 200 |
| `POST /dasha/kalachakra` | ✅ 200 |
| `POST /dasha/chara` | ✅ 200 |
| `POST /dasha/narayana` | ✅ 200 |
| Repeat D1 request (dedup check) | ✅ 200, same `birth_chart_id` reused |

**Database state after the above sequence** (verified via direct `psql`
queries, not the API):

| Table | Row count | Notes |
|---|---|---|
| `birth_charts` | 1 | One row shared across all 8 requests |
| `planet_positions` | 9 | All 9 Graha |
| `houses` | 12 | All 12 bhavas |
| `divisional_charts` | 15 | D2 through D60 |
| `divisional_planet_positions` | 135 | 15 × 9 |
| `dashas` | 7,639 | Across all 6 systems, `max_depth=3` |

Per-system dasha row counts: vimshottari 819, ashtottari 584, yogini 584,
kalachakra 1,884, chara 1,884, narayana 1,884 — confirming Chara and
Narayana (impossible to persist before migration 0003) now save correctly.

`birth_charts` row after the D1 request: `lagna_rashi = 'libra'`,
`moon_nakshatra = 'shatabhisha'` — matches the API response's ascendant
exactly.

---

## 5. Test Coverage

**406 tests passing, 0 failures** (391 unit + 15 persistence integration),
plus 2 tests requiring live infra (`.se1` files + real Postgres) excluded by
default via `-m "not integration"`.

Coverage on persistence-relevant modules (`pytest-cov`, real numbers from
this run):

| Module | Statements | Coverage |
|---|---|---|
| `apps/api/models/astrology.py` | 217 | **100%** |
| `apps/api/repositories/birth_chart_repository.py` | 35 | 97% |
| `apps/api/repositories/dasha_repository.py` | 22 | **100%** |
| `apps/api/repositories/divisional_chart_repository.py` | 20 | **100%** |
| `apps/api/repositories/divisional_planet_repository.py` | 14 | **100%** |
| `apps/api/repositories/house_repository.py` | 16 | **100%** |
| `apps/api/repositories/planet_position_repository.py` | 18 | **100%** |
| `apps/api/services/dasha_engine.py` | 220 | 98% |
| `apps/api/services/divisional_engine.py` | 189 | 99% |
| `apps/api/services/horoscope_engine.py` | 107 | 98% |
| **Overall project total** | 1,841 | **94%** |

Lower-coverage modules (`auth_service.py` 75%, `security/jwt.py` 35%,
`user_repository.py` 35%) are pre-existing, unrelated to this work, and out
of scope for this pass.

### One known pre-existing test failure, unrelated to persistence

`tests/integration/test_ephemeris_wrapper_concurrency.py::test_concurrent_calculations_do_not_cross_contaminate`
fails consistently (reproduced 3× in a row) once real `.se1` files and a
multi-threaded run are actually exercised:

```
Obtained: 60.34677141138641
Expected: 60.34676000122384 ± 1.0e-06
```

This is in `EphemerisWrapper`'s thread-safety handling (Module 2 territory)
— nothing in this persistence pass touches that file's calculation or
locking logic. It's flagged here rather than silently left for someone to
discover later, but fixing it is outside this task's scope.

---

## 6. Known Limitations

- `nakshatra_id` on `planet_positions` is always `NULL` — the `nakshatras`
  reference table exists but has no seed data.
- `subject_name` defaults to `"Unnamed"`; `timezone_offset_minutes` is
  derived from the birth datetime's own UTC offset (0, since the API
  requires true UTC) — neither is collected by any request schema.
- `planet_positions.longitude_deg` (tropical) is recovered as
  `sidereal_longitude + ayanamsa_value` since `SiderealPosition` never
  carries the raw tropical value.
- A full 5-level dasha tree can produce ~59,000 rows per request — not
  capped, since `max_depth` is an existing user-controlled parameter.
- `rules`, `karakatvas`, `books`, `verses`, `research_projects`,
  `research_snapshots`, `events`, `transits` remain unpopulated, per the
  "stop after persistence integration" scope.

---

## 7. Independent Verification on Target Environment

Everything above was verified in a sandboxed build environment. The
following was subsequently reproduced independently, live, on the actual
target machine (Windows, native PostgreSQL — not the sandbox used to
build this report):

| Step | Result |
|---|---|
| `alembic upgrade head` (0003 → 0004) | ✅ Applied cleanly |
| `alembic current` | ✅ `0004 (head)` |
| `uvicorn apps.api.main:app` | ✅ Clean startup, no errors |
| `POST /api/v1/dasha/chara` (live HTTP request) | ✅ `200 OK` |
| Direct DB query: `SELECT dasha_type, count(*) FROM dashas GROUP BY dasha_type` | ✅ `('chara', 156)` |

This closes the loop: Chara dasha — one of the two systems that could not
be persisted at all before migration 0003 (`dasha_type` enum didn't
recognize it) — now computes, saves, and is independently queryable
straight from PostgreSQL on the real deployment target, not just the
sandbox this work was built in.

**Status: complete and independently confirmed working end-to-end.**

---

## 8. Recommendation

The persistence layer is production-ready for the three engines in scope.
Suggested before starting Module 7 (Ashtakavarga):

1. Migrations 0003 and 0004 are confirmed applied on the primary target
   machine (§8) — if there are other environments running this schema
   (staging, a second dev machine, etc.), apply the same two migrations
   there before relying on Chara/Narayana dasha or any D1/divisional
   persistence.
2. Consider seeding the `nakshatras` reference table so `nakshatra_id` can
   be populated (small, isolated task, unblocks a currently-`NULL` FK).
3. The `EphemerisWrapper` concurrency test failure is worth a look before
   it's forgotten — it indicates the thread-safety guarantee the code
   comments promise may not currently hold under real load.
