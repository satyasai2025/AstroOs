# Module 6.5 — Foundation Completion: Architecture & Test Coverage Report

**Scope:** Fix the Swiss Ephemeris concurrency bug, seed reference tables, extract Graha/House/Aspect engines as independent services.
**Status:** Complete, all changes smoke-tested end-to-end against real PostgreSQL.
**Date:** 2026-07-10

---

## 1. Executive Summary

All five items are complete and verified:

| # | Item | Result |
|---|------|--------|
| 1 | Fix Swiss Ephemeris concurrency bug | **Real bug found and fixed** — not what the test's own docstring assumed. See §2. |
| 2 | Seed reference tables | `signs` (12), `nakshatras` (27), `padas` (108) seeded — the only 3 real reference tables in this schema. See §3. |
| 3 | Complete Graha Engine | Extracted to `graha_engine.py`, +1 new capability (`is_moolatrikona`). |
| 4 | Complete House Engine | New `house_engine.py` — genuinely new completion work, not extraction. |
| 5 | Extract Aspect Engine + tests | `aspect_engine.py`, 20 unit + 6 integration tests. |

Test suite: **486 passing** (up from 406), plus both real-infra tests now **genuinely** passing (not just re-marked). Coverage on every new/touched engine file: 98-100%.

Two more schema precision bugs (same pattern as `combustion_orb_deg` found during the persistence pass) surfaced while seeding reference tables and were fixed in the same migration.

---

## 2. Swiss Ephemeris Concurrency Bug — Root Cause and Fix

### What the test's docstring assumed
The pre-existing `test_ephemeris_wrapper_concurrency.py` assumed the failure was two concurrent calls with *different* ayanamsas interleaving their check-set-calculate sequence, causing one to silently borrow the other's ayanamsa mid-flight.

### What actually happens
That model doesn't fit the evidence. The observed diff (`1.14e-5`°) is roughly 50,000x smaller than what a genuine wrong-ayanamsa result would look like (Lahiri vs Raman differ by ~1.45° in this era).

Diagnosis, empirically, step by step:
1. **Purely single-threaded, repeated calls**: fully deterministic, always identical. Rules out general floating-point jitter.
2. **Sequential alternation between two ayanamsas, still single-threaded**: still fully deterministic. Rules out the lock's ayanamsa-switching logic itself.
3. **Same call from a brand-new OS thread, zero concurrency**: **already wrong** — differs from the main thread's result by up to 0.88° in one reproduction, every single time. Not a race; fully deterministic per-thread.
4. **Isolating which call matters**: neither `swe.set_ephe_path()` nor `swe.set_sid_mode()` alone, called fresh in the new thread, fully fixes it — **both together** are required to reproduce the main thread's exact result.

### Root cause
`EphemerisWrapper.__init__` calls both `swe.set_ephe_path()` and `swe.set_sid_mode()` exactly once, from whichever thread constructs the wrapper (the main thread, at process startup). Both are documented by pyswisseph as setting process-global C state. Empirically, that state is **not reliably visible to a different OS thread**. Every real request runs via `asyncio.to_thread(...)`, which always uses a worker thread from Python's default executor pool — never the thread that constructed the wrapper. **This means every production request was silently exposed to this precision loss, not just the test.**

### Fix
`_calculate_locked()` now unconditionally re-runs both calls at the start of every locked calculation, regardless of which thread calls it or whether the ayanamsa "changed" from last time. Both calls are cheap; the fix removes any dependency on cross-thread visibility rather than trying to reason about which thread "owns" correct state.

### Verification
- The previously-failing test (`test_concurrent_calculations_do_not_cross_contaminate`) now passes.
- Reproduced independently via raw `threading.Thread` (not just the test's own harness), confirming the fix at the mechanism level, not just the assertion level.
- Live-verified through the actual running API: 5 repeated D1 requests via real `asyncio.to_thread` (production code path) all returned the bit-identical ascendant longitude.

---

## 3. Reference Table Seeding

### Scope correction
The task named "Nakshatras, Padas, Signs, Planets, Houses." Only three of these are actual tables in this schema: `signs`, `nakshatras`, `padas`. Graha (planet) is a fixed PostgreSQL enum, not a table — nothing to seed. `houses` is the transactional per-birth-chart table, already populated by the persistence layer for every chart computed; it isn't a lookup table and has no generic rows to seed.

### What was seeded
| Table | Rows | Source |
|---|---|---|
| `signs` | 12 | `packages/shared/constants.py` (lords) + standard triplicities (element/modality/gender) |
| `nakshatras` | 27 | `packages/shared/constants.py`'s `VIMSHOTTARI_NAKSHATRA_LORDS` (same source `DashaEngine` uses) |
| `padas` | 108 | Computed programmatically, cross-checked against `divisional_engine.py`'s live `_d9_navamsha()` formula |

**Verification, not just self-consistency:** pada 10 (absolute 30°, start of Taurus) computed to Navamsha sign `capricorn` in the seed data — and calling `divisional_engine._d9_navamsha(1, 0.0)` (Taurus, 0°) directly returns `('capricorn', 0.0)` independently. The two are mathematically identical, not just "probably compatible."

### What was deliberately left NULL
`signs.direction`, and `nakshatras.deity/symbol/gana/nadi/varna/yoni/shakti`. These are real classical attributes, but hand-typing 27 nakshatras' worth of deity names, symbols, and especially shakti descriptions from unverified recall into a research platform's database is a worse outcome than leaving them NULL until sourced from a verified classical reference. All are nullable columns specifically to allow this kind of incremental fill later.

### A third precision bug found (same pattern as `combustion_orb_deg`)
`signs.start_degree/end_degree` (`NUMERIC(6,4)`) and `nakshatras`/`padas`' degree columns (`NUMERIC(8,6)`) all capped below 100 — but Pisces, Revati, and pada 108 all legitimately end at exactly 360°. Fixed by widening all six columns to `NUMERIC(9,6)` in the same migration, immediately before the inserts that need it.

---

## 4. Graha Engine (`graha_engine.py`)

Relocated from `horoscope_engine.py`'s private methods — algorithm unchanged, verified via the full pre-existing test suite passing unmodified against the new code path (which itself is strong evidence the extraction didn't alter behavior).

**One addition:** `is_moolatrikona()`. `MOOLATRIKONA_RASHIS` already existed in `packages/shared/constants.py` but had zero callers anywhere in the codebase — a real, if minor, gap. Now exposed as a proper dignity check alongside own-sign/exalted/debilitated.

19 new unit tests, covering dignity classification, strength scoring bounds (0-10), kendra/trikona/dusthana bonuses and penalties, combustion/retrograde modifiers, and the Rahu/Ketu no-dignity edge case.

---

## 5. House Engine (`house_engine.py`)

This is genuinely new completion work, not an extraction — `horoscope_engine.py` never computed house lordship or full quadrant classification; it only used the kendra/trikona/dusthana sets internally for Graha strength scoring.

New capability:
- `classify()` — the mutually-exclusive kendra/panapara/apoklima quadrant (every house is exactly one), plus separate non-exclusive trikona/dusthana/upachaya flags.
- `get_house_lord()` — which Graha rules a house, from its occupying sign.
- `build_house_summary()` — combines cusps, occupants, lordship, and classification into one `HouseInfo` per bhava.

**Deliberately not wired into `D1Chart`/the API response.** Adding fields to an existing response schema is a contract change outside the scope of "complete this engine as an independent service" — this was an explicit scoping decision, not an oversight. The engine is fully usable standalone today; wiring its output into the D1 endpoint is a separate decision for later.

35 new unit tests, including a check that the quadrant classification genuinely partitions all 12 houses with no gaps or overlaps.

---

## 6. Aspect Engine (`aspect_engine.py`)

Relocated verbatim from `horoscope_engine.py`'s private `_compute_aspects()`/`_classify_aspect()`.

**20 unit tests** (synthetic positions): all 5 aspect-offset special cases (Mars 4th/8th, Jupiter 5th/9th, Saturn 3rd/10th, Rahu/Ketu matching Jupiter), universal 7th-house rule, orb calculation and its 15° wraparound, and the "never aspects itself" invariant.

**6 integration tests** (real computed charts via `EphemerisWrapper`, Moshier fallback — no live infra required): including the specific test that matters most for a refactor like this — calling `AspectEngine.compute()` directly on a real chart's planets produces **byte-identical** output to what `HoroscopeEngine.generate_d1()` returns via delegation, across multiple ayanamsa systems.

---

## 7. Test Suite Summary

| Category | Count |
|---|---|
| Pre-existing (persistence pass baseline) | 406 |
| GrahaEngine unit tests (new) | 19 |
| HouseEngine unit tests (new) | 35 |
| AspectEngine unit tests (new) | 20 |
| AspectEngine integration tests (new) | 6 |
| **Total, default run** | **486 passing, 0 failures** |
| Real-infra-only (`.se1` + threading) | 2 passing (previously 1 pass / 1 genuine fail) |

Coverage on new/touched files: `aspect_engine.py` 100%, `horoscope_engine.py` 100%, `house_engine.py` 100%, `graha_engine.py` 98%, `ephemeris_wrapper.py` 99%.

---

## 8. Live Verification

Performed against real PostgreSQL 16 (migrations 0001-0005 applied from clean), real running API, real HTTP requests — not just the test suite:

| Check | Result |
|---|---|
| `alembic upgrade head` (0004 → 0005, clean apply) | ✅ |
| `signs`/`nakshatras`/`padas` row counts | ✅ 12 / 27 / 108 |
| D1 endpoint, post-refactor | ✅ 200, correct output |
| 5 repeated identical requests via real `asyncio.to_thread` | ✅ Bit-identical ascendant every time (concurrency fix holds under real request handling) |
| Server log | ✅ Clean, no errors |

---

## 9. Recommendation

Foundation is now genuinely complete for Modules 1-2, 5-7, and the persistence layer underneath them. Reasonable next steps:

1. Apply migration 0005 (and 0003/0004 if not already applied) to any other environment running this schema.
2. If `HouseEngine`'s output should appear in the D1 API response, that's a deliberate, separate schema-contract decision — flag it explicitly rather than adding it incidentally to a future change.
3. Module 8 (Yoga Engine) or Module 9 (Shadbala Engine) are the natural next steps per the original 27-module plan — both now sit on a foundation that's been audited, tested, and live-verified rather than assumed correct.
