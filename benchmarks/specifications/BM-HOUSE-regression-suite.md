# BM-HOUSE — Regression Suite

> **Part Of:** BM-HOUSE Benchmark Family
> **Version:** 1.0.0
> **Status:** DRAFT (Phase 6)
> **Date:** 2026-07-15

---

## 1. Purpose

This regression suite documents known and potential house calculation bugs. Every regression test must pass before any AstroOS release.

---

## 2. Regression Test Index

| Reg ID | Bug Type | Severity | Source |
|--------|----------|----------|--------|
| REG-HOUSE-001 | Whole Sign cusp not at rashi boundary | CRITICAL | System architecture |
| REG-HOUSE-002 | House cusp ordering violation | CRITICAL | Mathematical invariant |
| REG-HOUSE-003 | Missing house number | CRITICAL | Completeness |
| REG-HOUSE-004 | Latitude boundary — Placidus at equator | MAJOR | System behavior |
| REG-HOUSE-005 | Latitude boundary — Placidus at polar circle | MAJOR | System behavior |
| REG-HOUSE-006 | Ayanamsa consistency — house cusps | CRITICAL | Shared with BM-CALC |
| REG-HOUSE-007 | House classification consistency | NORMAL | Deterministic guarantee |
| REG-HOUSE-008 | House lordship consistency across systems | NORMAL | Cross-system check |
| REG-HOUSE-009 | Planet-house assignment — Whole Sign invariant | CRITICAL | Mathematical invariant |
| REG-HOUSE-010 | Equal house formula correctness | CRITICAL | Mathematical invariant |

---

## 3. Regression Test Specifications

### REG-HOUSE-001: Whole Sign Cusp at Rashi Boundary

| Field | Value |
|-------|-------|
| **Purpose** | Verify that Whole Sign house cusps are exactly at 0° of each rashi |
| **Previous Bug** | N/A — preventive regression. Whole Sign must set each house cusp at the exact starting point of its sign, NOT at the tropical cusp longitude from `swe.houses()`. |
| **Expected Behaviour** | House N sidereal cusp = `(lagna_rashi_index + N - 1) × 30°` (exact, no fractional degree) |
| **Acceptance Criteria** | 1. For each of the 5 GC-MASTER charts, compute Whole Sign houses<br>2. For houses 1–12, verify sidereal_cusp_deg % 30 = 0<br>3. House N's sidereal cusp is exactly (N-1) × 30° from lagna<br>4. Any fractional degree indicates the tropical cusp was used instead of the sign boundary |
| **Root Cause** | Code had to be written to explicitly override Swiss Ephemeris cusps for Whole Sign mode — if this code path breaks, Whole Sign silently falls back to Placidus cusps |

### REG-HOUSE-002: House Cusp Ordering

| Field | Value |
|-------|-------|
| **Purpose** | Verify that house cusps are in ascending longitude order |
| **Previous Bug** | N/A — preventive regression. House cusps must maintain order N < N+1 (mod 360). Crossing cusps would produce negative house sizes. |
| **Expected Behaviour** | For every configuration: `cusp_N ≤ cusp_{N+1}` for N=1..11, and `cusp_12 < cusp_1 + 360` |
| **Acceptance Criteria** | 1. Compute houses for all 4 systems × 5 GC-MASTER charts<br>2. Verify cusp_N ≤ cusp_{N+1} for all N in 1..11<br>3. Verify cusp_12 < cusp_1 + 360<br>4. Any violation → house cusp calculation error |

### REG-HOUSE-003: Twelve Distinct Houses

| Field | Value |
|-------|-------|
| **Purpose** | Verify that exactly 12 houses are computed per configuration |
| **Previous Bug** | N/A — preventive. Swiss Ephemeris `swe.houses()` should always return 12 cusps. |
| **Expected Behaviour** | Exactly 12 `HouseCusp` objects, house numbers 1 through 12 |
| **Acceptance Criteria** | 1. Count houses — must equal 12<br>2. House numbers must be 1, 2, 3, ..., 12 (no duplicates, no gaps)<br>3. All 4 house systems produce exactly 12 |

### REG-HOUSE-004: Placidus at Equator

| Field | Value |
|-------|-------|
| **Purpose** | Verify that Placidus house calculation works at equatorial latitudes |
| **Previous Bug** | N/A — Placidus becomes degenerate at the equator (house cusps approach equal division). |
| **Expected Behaviour** | Placidus house cusps at 0° latitude should be nearly equal (~30° apart). No crashes, no NaN values, no out-of-range cusps. |
| **Acceptance Criteria** | 1. Compute Placidus houses at 0° latitude for any GC-MASTER chart<br>2. All cusps must be in [0, 360)<br>3. No division-by-zero or Swiss Ephemeris errors<br>4. House sizes should be clustered near 30° |

### REG-HOUSE-005: Placidus at Polar Circle

| Field | Value |
|-------|-------|
| **Purpose** | Verify that Placidus handles polar-adjacent latitudes without crashing |
| **Previous Bug** | N/A — Placidus is undefined at polar latitudes (>66.5°). The engine should handle this gracefully. |
| **Expected Behaviour** | At 66.5°N, Placidus may produce extreme house sizes. The engine must not crash, return NaN, or produce out-of-range values. |
| **Acceptance Criteria** | 1. Compute Placidus houses at 66.5°N for any chart<br>2. All cusps must be in [0, 360)<br>3. No Swiss Ephemeris errors<br>4. House size extremes documented as warnings, not errors |

### REG-HOUSE-006: Ayanamsa Consistency on House Cusps

| Field | Value |
|-------|-------|
| **Purpose** | Verify that ayanamsa is applied consistently to house cusps |
| **Previous Bug** | Same root cause as REG-CALC-005 — ayanamsa thread-safety issue could affect house sidereal conversions |
| **Expected Behaviour** | For any non-Whole Sign, non-Equal system: `sidereal_cusp = tropical_cusp - ayanamsa_value (mod 360)` within ±0.01° |
| **Acceptance Criteria** | 1. Compute houses in Placidus mode for one chart<br>2. For all 12 cusps: verify `tropical - sidereal ≈ ayanamsa_value`<br>3. Repeat for all 6 ayanamsa systems<br>4. All must match within ±0.01° |

### REG-HOUSE-007: House Classification Consistency

| Field | Value |
|-------|-------|
| **Purpose** | Verify that house classification never changes between runs |
| **Previous Bug** | N/A — deterministic guarantee |
| **Expected Behaviour** | House classification is purely deterministic (fixed lookup). Same house number must always produce same classification. |
| **Acceptance Criteria** | 1. Call `HouseEngine.classify(N)` for N=1..12<br>2. Verify results match the fixed mapping table<br>3. Repeat 10 times — must be identical every time<br>4. Test across all 4 house systems (if house number changes, classification still matches the NUMBER, not the sign) |

### REG-HOUSE-008: House Lordship Consistency

| Field | Value |
|-------|-------|
| **Purpose** | Verify that house lordship is deterministic from rashi |
| **Previous Bug** | N/A — deterministic |
| **Expected Behaviour** | Given a rashi, `get_house_lord()` always returns the same lord from SIGN_LORDS |
| **Acceptance Criteria** | 1. Call `get_house_lord()` for all 12 rashis<br>2. Verify each matches SIGN_LORDS<br>3. Repeat 10 times — identical each time |

### REG-HOUSE-009: Planet-House Assignment Invariant (Whole Sign)

| Field | Value |
|-------|-------|
| **Purpose** | Verify that planet-house assignment in Whole Sign follows the mathematical invariant |
| **Previous Bug** | N/A — preventive. Whole Sign's invariant (rashi-index-from-lagna) must hold. |
| **Expected Behaviour** | `planet_house = (planet_rashi_index - lagna_rashi_index) % 12 + 1` |
| **Acceptance Criteria** | 1. For each chart in Whole Sign, compute each planet's house<br>2. Verify the formula above produces the same result<br>3. Any mismatch → house assignment code path is wrong |

### REG-HOUSE-010: Equal House Formula

| Field | Value |
|-------|-------|
| **Purpose** | Verify that Equal house cusps follow the mathematical formula |
| **Previous Bug** | N/A — preventive. Equal house is a simple formula. |
| **Expected Behaviour** | House N sidereal cusp = `(ascendant_sidereal + (N-1) × 30°) mod 360` |
| **Acceptance Criteria** | 1. Compute Equal houses for each of the 5 GC-MASTER charts<br>2. For houses 1–12: verify `computed_cusp ≈ asc + (N-1) × 30°` within ±0.001°<br>3. Any larger deviation → Equal house code path uses wrong formula |

---

## 4. Regression Run Protocol

### 4.1 Per-Commit (Fast)

| Test | Est. Time |
|------|-----------|
| REG-HOUSE-001, -003, -009, -010 (Whole Sign invariants) | 1s |
| REG-HOUSE-006 (ayanamsa) | 1s |
| REG-HOUSE-007, -008 (classification/lordship) | 0.5s |
| **Total** | **~2.5s** |

### 4.2 Full Regression (Pre-Release)

| Phase | Est. Time |
|-------|-----------|
| All 10 regression tests × 5 charts × 4 systems | ~30s |

### 4.3 Failure Response

| Reg ID | Failure | Response |
|--------|---------|----------|
| REG-HOUSE-001 | **BLOCKING** | Whole Sign cusps not at boundaries |
| REG-HOUSE-002 | **BLOCKING** | Cusp ordering violated |
| REG-HOUSE-003 | **BLOCKING** | Missing house |
| REG-HOUSE-006 | **BLOCKING** | Ayanamsa inconsistency |
| REG-HOUSE-009 | **BLOCKING** | Whole Sign planet-house invariant broken |
| REG-HOUSE-010 | **BLOCKING** | Equal house formula broken |
| REG-HOUSE-004 | WARNING | Equatorial Placidus behavior |
| REG-HOUSE-005 | WARNING | Polar Placidus behavior |
| REG-HOUSE-007 | WARNING | Classification determinism |
| REG-HOUSE-008 | WARNING | Lordship determinism |

---

## 5. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief QA & Benchmark Architect (Agent 4) | Initial regression suite |

---

*End of BM-HOUSE Regression Suite.*
