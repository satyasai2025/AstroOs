# BM-CALC — Regression Suite

> **Part Of:** BM-CALC Benchmark Family
> **Version:** 1.0.0
> **Status:** DRAFT (Phase 6)
> **Date:** 2026-07-15

---

## 1. Purpose

This regression suite documents known historical bugs in planet position calculation and defines the regression tests that ensure they never reappear. Every regression test in this suite must pass before any AstroOS release can proceed.

**Never write pytest code.** This document defines regression tests by specification only.

---

## 2. Regression Test Index

| Reg ID | Bug Type | Severity | Source |
|--------|----------|----------|--------|
| REG-CALC-001 | Swiss Ephemeris thread-safety | CRITICAL | Module 6.5, architecture.md |
| REG-CALC-002 | Combustion orb precision | CRITICAL | Migration 0004, architecture.md |
| REG-CALC-003 | Reference table degree precision | MAJOR | Migration 0005, architecture.md |
| REG-CALC-004 | Dual DeclarativeBase metadata | MAJOR | Module 6.5, architecture.md |
| REG-CALC-005 | Ayanamsa consistency across threads | CRITICAL | Module 6.5, architecture.md |
| REG-CALC-006 | Rahu/Ketu position consistency | NORMAL | Classical constraint |
| REG-CALC-007 | Mercury/Venus solar elongation | NORMAL | Astronomical constraint |
| REG-CALC-008 | Determinism across repeated calls | CRITICAL | BM-CALC spec §6.3 |
| REG-CALC-009 | Moshier vs Official consistency | NORMAL | BM-CALC spec §3.3 |
| REG-CALC-010 | Moshier boundary accuracy | NORMAL | Fallback mode limits |

---

## 3. Regression Test Specifications

### REG-CALC-001: Swiss Ephemeris Thread-Safety

| Field | Value |
|-------|-------|
| **Purpose** | Verify that planet positions computed from background threads match main-thread results |
| **Previous Bug** | `swe.set_ephe_path()` and `swe.set_sid_mode()` set process-global C state that was NOT reliably visible to different OS threads. Every request via `asyncio.to_thread(...)` used a worker thread that did not see the initialization from the thread that constructed `EphemerisWrapper`. This affected ALL production calculations, not just concurrent ones. |
| **Expected Behaviour** | Planet positions computed from ANY thread (main, worker pool, explicit thread) MUST produce identical results for identical inputs |
| **Acceptance Criteria** | 1. Compute a reference position from main thread (GC-REF-002, Lahiri)<br>2. Compute same position from 5 concurrent `asyncio.to_thread` calls<br>3. Compute same position from a bare `threading.Thread`<br>4. ALL results MUST match within ±0.001° (not ±0.1° — this tests exact ephemeris output)<br>5. Repeated 10 times — every run must produce identical results |
| **Reference** | Fix: both calls are now unconditionally re-run at the start of every locked calculation (`_calculate_locked()` in `ephemeris_wrapper.py`) |

### REG-CALC-002: Combustion Orb Precision

| Field | Value |
|-------|-------|
| **Purpose** | Verify that combustion orbs > 100° are correctly stored and reported |
| **Previous Bug** | `planet_positions.combustion_orb_deg` column was `NUMERIC(6,4)` — max 2 integer digits (99.9999 max). `EphemerisWrapper.is_combust()` returns the TRUE angular distance from the Sun (0-180°) regardless of whether it's within the combustion threshold. A real chart produced 150.03° for a correctly non-combust planet and the insert failed with `NumericValueOutOfRange`. |
| **Expected Behaviour** | Combustion distance values up to 180° must be stored and returned without error |
| **Acceptance Criteria** | 1. Compute position for a chart where Venus is far from Sun (150°+)<br>2. `is_combust` returns `false`<br>3. The angular distance is stored correctly (not truncated)<br>4. Retrieving the stored value returns 150.xx (not 99.99) |
| **Reference** | Migration `0004_audit_column_completeness` widened the column to `NUMERIC(9,6)` |

### REG-CALC-003: Reference Table Degree Precision

| Field | Value |
|-------|-------|
| **Purpose** | Verify that sign, nakshatra, and pada end degrees up to 360° are stored correctly |
| **Previous Bug** | `signs.start_degree`/`end_degree` (`NUMERIC(6,4)`) and `nakshatras`/`padas` degree columns (`NUMERIC(8,6)`) all capped below 100. Pisces legitimately reaches 360° (end of Revati, pada 108). All six columns too narrow. |
| **Expected Behaviour** | All degree values 0–360° must be storable and retrievable without overflow |
| **Acceptance Criteria** | 1. Verify RF-SIGNS end_degree for Pisces = 360.0°<br>2. Verify RF-NAK end_degree for Revati = 360.0°<br>3. Verify RF-PADA end_degree for pada 108 = 360.0°<br>4. All stored values must round-trip through PostgreSQL without precision loss |
| **Reference** | Migration `0005_seed_reference_tables` widened all six columns to `NUMERIC(9,6)` |

### REG-CALC-004: Dual DeclarativeBase Metadata

| Field | Value |
|-------|-------|
| **Purpose** | Verify that all SQLAlchemy models share a single MetaData registry |
| **Previous Bug** | `ReferenceBase` (used by `signs`/`nakshatras`/`padas`) and `AstroBase` were two separate `DeclarativeBase` classes with two separate `MetaData` registries. Foreign keys from `AstroBase` tables into `ReferenceBase` tables (e.g. `planet_positions.nakshatra_id`) couldn't be resolved by `Base.metadata.create_all()`. |
| **Expected Behaviour** | All table definitions must resolve through a single MetaData registry |
| **Acceptance Criteria** | 1. Verify `planet_positions.nakshatra_id` foreign key resolves to `nakshatras.id`<br>2. Verify no `ForeignKeyError` when building the full schema<br>3. Verify all model imports succeed without circular dependency errors |
| **Reference** | Fix: `ReferenceBase` now shares `AstroBase`'s `MetaData` |

### REG-CALC-005: Ayanamsa Consistency Across Threads

| Field | Value |
|-------|-------|
| **Purpose** | Verify that ayanamsa calculation produces identical values regardless of calling thread |
| **Previous Bug** | Same root cause as REG-CALC-001 — `swe.set_sid_mode()` was not reliably visible across threads. The first calculation from any new OS thread could differ by up to 0.88°. |
| **Expected Behaviour** | Ayanamsa value for the same Julian Day MUST be identical across all threads |
| **Acceptance Criteria** | 1. Compute ayanamsa from main thread for JD of GC-REF-001<br>2. Compute ayanamsa from 3 worker threads for same JD<br>3. Compute ayanamsa from explicit `threading.Thread` for same JD<br>4. ALL values match within ±0.001°<br>5. All 6 ayanamsa systems tested independently |
| **Reference** | Fix: `swe.set_sid_mode()` now unconditionally re-run at the start of every locked calculation |

### REG-CALC-006: Rahu/Ketu Position Consistency

| Field | Value |
|-------|-------|
| **Purpose** | Verify that Rahu and Ketu positions are always ~180° apart |
| **Previous Bug** | N/A — classical astronomical invariant, not a previous code bug |
| **Expected Behaviour** | Rahu longitude + 180° = Ketu longitude (mod 360), within ±0.001° |
| **Acceptance Criteria** | 1. Compute Rahu and Ketu positions for all 5 GC-MASTER charts<br>2. Verify |(rahu_long + 180) - ketu_long| ≤ 0.001° for all configurations<br>3. Verify this holds across all 6 ayanamsa systems<br>4. Verify this holds across both ephemeris modes |
| **Rationale** | Regression guard — if the computational invariant breaks, the ephemeris integration has a fundamental error |

### REG-CALC-007: Mercury/Venus Solar Elongation

| Field | Value |
|-------|-------|
| **Purpose** | Verify that Mercury and Venus never exceed their maximum solar elongation |
| **Previous Bug** | N/A — astronomical constraint |
| **Expected Behaviour** | Mercury's distance from the Sun (angular) ≤ 28°. Venus' distance from the Sun ≤ 47°. |
| **Acceptance Criteria** | 1. Compute Mercury elongation for all 5 GC-MASTER charts<br>2. Compute Venus elongation for all 5 GC-MASTER charts<br>3. Verify Mercury ≤ 28° for all configurations<br>4. Verify Venus ≤ 47° for all configurations<br>5. These are epoch-independent astronomical constraints |
| **Rationale** | Regression guard — if violated, the ecliptic coordinate conversion is incorrect |

### REG-CALC-008: Determinism Across Repeated Calls

| Field | Value |
|-------|-------|
| **Purpose** | Verify that the same chart × ayanamsa configuration produces byte-identical output on repeated calls |
| **Previous Bug** | Non-determinism in floating-point operations across threads can cause subtle output differences |
| **Expected Behaviour** | 10 consecutive calls with identical inputs produce byte-identical JSON output |
| **Acceptance Criteria** | 1. Call `EphemerisWrapper.get_planet_positions()` 10× with same inputs<br>2. Serialize each result to JSON<br>3. Compute SHA-256 of each JSON<br>4. All 10 hashes MUST be identical<br>5. Test across all 6 ayanamsa systems<br>6. Test across both ephemeris modes |
| **Note** | If non-determinism is detected, the benchmark run is INVALID and must be investigated |

### REG-CALC-009: Moshier vs Official Consistency

| Field | Value |
|-------|-------|
| **Purpose** | Verify that Moshier fallback mode produces results consistent with official ephemeris mode |
| **Previous Bug** | N/A — documented accuracy limit |
| **Expected Behaviour** | Moshier results must be within 1 arc-minute (0.0167°) of official-mode results |
| **Acceptance Criteria** | 1. Compute positions for all 5 GC-MASTER charts in official mode<br>2. Compute positions for same charts in Moshier mode<br>3. Compare every longitude field — difference ≤ 0.0167°<br>4. Retrograde/combustion flags must match exactly<br>5. Test across all 6 ayanamsa systems |
| **Note** | This is a SOFT regression requirement — Moshier is documented as lower accuracy. If tolerance is exceeded, log the discrepancy but do not block release. |

### REG-CALC-010: Moshier Boundary Accuracy

| Field | Value |
|-------|-------|
| **Purpose** | Verify Moshier accuracy specifically at boundary positions (near 0°, near 360°, at sign cusps) |
| **Previous Bug** | Moshier polynomial approximations can have larger errors at certain points in the orbit |
| **Expected Behaviour** | Moshier accuracy at boundaries must still be within 0.1° of official ephemeris |
| **Acceptance Criteria** | 1. Find a planet near 0° sidereal longitude (end of Pisces / start of Aries)<br>2. Find a planet near 180° (start of Libra)<br>3. Compare Moshier vs Official for both positions<br>4. Disagreement must be ≤ 0.1° (the BM-CALC standard tolerance)<br>5. If disagreement exceeds 0.1°, document as a known limitation of Moshier mode |
| **Note** | Results that exceed tolerance are documented as warnings, not failures |

---

## 4. Regression Run Protocol

### 4.1 Per-Commit Regression (Fast)

Run before every commit to planet position code:

| Test | Est. Time |
|------|-----------|
| REG-CALC-001 (thread safety) | 2s |
| REG-CALC-005 (ayanamsa threads) | 1s |
| REG-CALC-008 (determinism) | 2s |
| REG-CALC-006 (Rahu/Ketu) | 1s |
| REG-CALC-007 (elongation) | 1s |
| **Total** | **~7s** |

### 4.2 Full Regression (Slow)

Run before every release:

| Phase | Est. Time |
|-------|-----------|
| All 10 regression tests × 5 charts × 6 ayanamsa × 2 ephemeris modes | ~120s |
| Comparison + reporting | ~10s |

### 4.3 Failure Response

| Failure | Response |
|---------|----------|
| REG-CALC-001 or REG-CALC-005 fails | **BLOCKING** — thread-safety regression, must fix before any release |
| REG-CALC-002 or REG-CALC-003 fails | **BLOCKING** — database schema regression, must fix before any release |
| REG-CALC-008 fails | **BLOCKING** — fundamental correctness regression |
| REG-CALC-004 fails | **BLOCKING** — model architecture regression |
| REG-CALC-006 or REG-CALC-007 fails | **MAJOR** — astronomical invariant violated |
| REG-CALC-009 or REG-CALC-010 fails | **WARNING** — log, document, investigate drift |

---

## 5. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief QA & Benchmark Architect (Agent 4) | Initial regression suite |

---

*End of BM-CALC Regression Suite. These 10 regression tests must pass before any AstroOS release proceeds.*
