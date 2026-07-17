# BM-HOUSE — House Cusp Calculation Benchmarks (Master Specification)

> **Benchmark Family:** BM-HOUSE
> **Version:** 1.0.0
> **Status:** DRAFT
> **Owner:** Chief QA & Benchmark Architect (Agent 4)
> **Date:** 2026-07-15

---

## 1. Identification

| Field | Value |
|-------|-------|
| **Family ID** | `BM-HOUSE` |
| **Full Title** | House Cusp Calculation Benchmarks |
| **AstroOS Modules Tested** | M3 — House Engine (`HouseEngine`, `EphemerisWrapper.get_ascendant_and_cusps`) |
| **Depends On** | BM-CALC (planet positions), Swiss Ephemeris `swe.houses()` |
| **Required By** | BM-VARGA, BM-YOGA, BM-BALA, BM-TRANSIT, BM-RULE |

---

## 2. Purpose & Scope

**Purpose:**
Verify that AstroOS computes house cusps correctly across all 4 supported house systems (Whole Sign, Placidus, Koch, Equal). House cusps determine which sign occupies which house, which directly affects house lordship, planet-house assignment, and every higher-order calculation. Unlike planet positions (which are celestial), house cusps depend on terrestrial latitude and the chosen house system — making this a distinct validation challenge.

**Category:** Calculation Accuracy
**Difficulty:** FOUNDATION
**Risk if Failed:** All house-dependent calculations (lordship, planetary strength, yogas with house conditions, transit house placement) produce incorrect results.

**Related Benchmarks:**
- Required by: BM-VARGA (varga D1 assignment), BM-YOGA (house-based yoga conditions), BM-BALA (Dig Bala, Kendradi Bala), BM-TRANSIT (house-from-Moon), BM-RULE (house-lord rules)
- Uses: BM-CALC (planet positions), RF-SIGNS (rashi lords)

---

## 3. Test Matrix

### 3.1 Dimensions Tested

| Dimension | Values | Coverage |
|-----------|--------|----------|
| **House systems** | W (Whole Sign), P (Placidus), K (Koch), E (Equal) | All 4 supported |
| **Reference charts** | GC-REF-001 through GC-REF-005 | 5 charts, diverse latitudes |
| **Ayanamsa** | Lahiri (primary), plus 1 cross-check (True Chitra) | 1 primary + 1 cross |
| **Houses** | Cusp 1–12 (full set per configuration) | All 12 bhavas |
| **House classifications** | Quadrant, trikona, dusthana, upachaya | All 12 houses |
| **House lords** | All 9 grahas as lords | All sign-lord mappings |

### 3.2 Individual Test Cases

| Test ID | Focus | Input Variation |
|---------|-------|----------------|
| BM-HOUSE-001 | Whole Sign house cusps — REF-001 | Chart 1, W, Lahiri |
| BM-HOUSE-002 | Whole Sign house cusps — REF-002 | Chart 2, W, Lahiri |
| BM-HOUSE-003 | Whole Sign house cusps — REF-003 | Chart 3, W, Lahiri |
| BM-HOUSE-004 | Whole Sign house cusps — REF-004 | Chart 4, W, Lahiri |
| BM-HOUSE-005 | Whole Sign house cusps — REF-005 | Chart 5, W, Lahiri |
| BM-HOUSE-006 | Placidus house cusps — REF-001 | Chart 1, P, Lahiri |
| BM-HOUSE-007 | Placidus house cusps — REF-002 | Chart 2, P, Lahiri |
| BM-HOUSE-008 | Koch house cusps — REF-001 | Chart 1, K, Lahiri |
| BM-HOUSE-009 | Equal house cusps — REF-001 | Chart 1, E, Lahiri |
| BM-HOUSE-010 | House classification — all 4 systems, REF-001 | All systems × 12 houses |
| BM-HOUSE-011 | House lordship — all 4 systems, REF-001 | 12 houses × lord |
| BM-HOUSE-012 | Planet-house assignment — all 4 systems, REF-001 | 9 grahas × which house |
| BM-HOUSE-013 | Whole Sign latitude independence — REF-001, -002 | Whole Sign cusps don't change with latitude |
| BM-HOUSE-014 | Placidus latitude sensitivity — REF-001, multiple lats | Placidus cusps DO change with latitude |
| BM-HOUSE-015 | Ayanamsa cross-check — REF-001, W, True Chitra | Verify cusp shift = ayanamsa delta |
| BM-HOUSE-016 | House consistency — all 5 charts, W vs P differences | Document systematic differences |

---

## 4. Input Data

### 4.1 Standard Inputs (from GC-MASTER)

For each chart, the standard set:
- `birth_datetime_utc`, `latitude`, `longitude` (from GC-REF-00N)
- `ayanamsa`: Primary = Lahiri; Cross-check = True Chitra
- `house_system`: W, P, K, E (4 values)

### 4.2 Additional Inputs for House System Tests

| Test | Additional Inputs | Purpose |
|------|-------------------|---------|
| BM-HOUSE-013 | Same birth time at 3 different latitudes (0°, 45°N, 90°N theoretical) | Verify Whole Sign ignores latitude |
| BM-HOUSE-014 | Same birth time at latitudes 0°, ±23.4°, ±45°, ±66.5° | Verify Placidus changes with latitude |

---

## 5. Expected Outputs

### 5.1 House Cusp Output Structure

```json
{
  "chart_id": "GC-REF-001",
  "house_system": "W",
  "ayanamsa": "lahiri",
  "houses": [
    {
      "house_number": 1,
      "tropical_longitude": 197.3456,
      "sidereal_longitude": 173.3456,
      "rashi": "Virgo",
      "lord": "Mercury",
      "classification": {
        "quadrant": "kendra",
        "is_trikona": true,
        "is_dusthana": false,
        "is_upachaya": false
      }
    }
  ]
}
```

### 5.2 House Classification Rules

| House | Quadrant | Trikona | Dusthana | Upachaya |
|-------|----------|---------|----------|----------|
| 1 | kendra | ✅ | — | — |
| 2 | panapara | — | — | — |
| 3 | apoklima | — | — | ✅ |
| 4 | kendra | — | — | — |
| 5 | panapara | ✅ | — | — |
| 6 | apoklima | — | ✅ | ✅ |
| 7 | kendra | — | — | — |
| 8 | panapara | — | ✅ | — |
| 9 | apoklima | ✅ | — | — |
| 10 | kendra | — | — | ✅ |
| 11 | panapara | — | — | ✅ |
| 12 | apoklima | — | ✅ | — |

### 5.3 House Lord Rules

Each rashi has exactly one lord per `SIGN_LORDS` from `packages/shared/constants.py`:

| Rashi | Lord | Rashi | Lord |
|-------|------|-------|------|
| Aries (Mesha) | Mars | Libra (Tula) | Venus |
| Taurus (Vrishabha) | Venus | Scorpio (Vrishchika) | Mars |
| Gemini (Mithuna) | Mercury | Sagittarius (Dhanus) | Jupiter |
| Cancer (Karka) | Moon | Capricorn (Makara) | Saturn |
| Leo (Simha) | Sun | Aquarius (Kumbha) | Saturn |
| Virgo (Kanya) | Mercury | Pisces (Meena) | Jupiter |

### 5.4 Whole Sign House-Rashi Mapping

In Whole Sign, house N's rashi = lagna rashi + (N - 1) signs:

```
House 1 = Lagna Rashi
House 2 = Next rashi (cyclically)
...
House 12 = 11th rashi from lagna
```

For Placidus/Koch/Equal, house cusp rashis are computed from the sidereal cusp longitude directly and may interlace (same rashi appearing on multiple cusps, or signs intercepted — a sign that does NOT appear on any cusp).

---

## 6. Acceptance Criteria

### 6.1 Hard Requirements (100% Pass Required)

| # | Criterion | Tolerance | Condition |
|---|-----------|-----------|-----------|
| H1 | House cusp sidereal longitude — all 4 systems | ±0.1° | Per chart per system |
| H2 | House rashi assignment — Whole Sign | Exact | House N = (lagna_rashi + N - 1) % 12 |
| H3 | House rashi assignment — Placidus/Koch/Equal | Exact | From sidereal cusp longitude |
| H4 | House classification — all 12 houses | Exact | Per mapping in §5.2 |
| H5 | House lord — all 12 houses | Exact | Per SIGN_LORDS lookup |
| H6 | Whole Sign longitude independent of latitude | Exact | Same cusps at any latitude |
| H7 | 12 houses present per configuration | Exact | No missing houses |
| H8 | House numbers 1–12 in order | Exact | No duplicate or out-of-order cusps |

### 6.2 Soft Requirements (≥ 95% Pass, Reported)

| # | Criterion | Tolerance | Condition |
|---|-----------|-----------|-----------|
| S1 | Placidus cusp longitude matches external reference | ±0.5° | Cross-check |
| S2 | Koch cusp longitude matches external reference | ±1.0° | Cross-check (Koch less common) |
| S3 | Equal cusp longitude matches external reference | ±0.1° | Equal is simple: asc + (N-1)×30° |
| S4 | Intercepted signs correctly identified | Exact | Placidus/Koch only |
| S5 | Ayanamsa shift applies consistently | ±0.01° | Tropical cusp - ayanamsa = sidereal cusp |

### 6.3 Determinism Requirement

Same input → same output (content hash match), identical to BM-CALC.

---

## 7. House System Behavior Rules

### 7.1 Whole Sign (W)

**Algorithm:** House 1 cusp = lagna rashi at 0° sidereal longitude. Each subsequent house cusp = next rashi at 0°.

**Key property:** Completely latitude-independent. House-rashi mapping is fixed once lagna rashi is known. No intercepted signs.

**Validation:** For any chart in Whole Sign, the rashi on house N is `(lagna_rashi_index + N - 1) % 12`. This is a mathematical invariant.

### 7.2 Placidus (P)

**Algorithm:** Time-based quadrant system. House cusps are computed from the intersection of the ecliptic with spatial great circles dividing the local celestial sphere.

**Key property:** Latitude-dependent. House sizes vary with latitude. Intercepted signs are possible (a sign that never touches a cusp).

**Validation:** Cross-check against independently computed Placidus cusps (from astro.com or Jagannatha Hora).

### 7.3 Koch (K)

**Algorithm:** Based on the difference between the oblique ascension of a point on the ecliptic and the RAMC.

**Key property:** Latitude-dependent, similar to Placidus. Less commonly used.

**Validation:** Cross-check against external reference implementations.

### 7.4 Equal House (E)

**Algorithm:** Each house is exactly 30° starting from the ascendant. House N cusp = ascendant + (N - 1) × 30°.

**Key property:** Simple mathematical relationship. No latitude dependence beyond the ascendant itself. No intercepted signs.

**Validation:** Mathematical invariant: H(N).sidereal = (asc_sidereal + (N - 1) × 30°) mod 360.

---

## 8. Validation Method

### 8.1 Automated Validation

| Check | Method | When |
|-------|--------|------|
| House cusp longitude vs reference run | Comparison script | Each benchmark run |
| House-rashi consistency | Rashi from longitude must match claimed rashi | Each benchmark run |
| Classification table conformity | All 12 houses × all flags verified | Each benchmark run |
| System-specific invariants | See §7 — Whole Sign/Equal are checkable, Placidus/Koch cross-check | Per run |

### 8.2 Cross-Check Procedure

Placidus and Koch cusps require external verification because Swiss Ephemeris is both the production engine AND the reference. Recommended cross-check:

1. Run the same birth data through Jagannatha Hora or astro.com
2. Compare Placidus cusp degrees
3. Document any systematic offset

### 8.3 Invariant Checks (Always Testable Without External Reference)

| Invariant | Applies To |
|-----------|------------|
| House N sidereal = asc + (N-1)×30° mod 360 | Equal only |
| House N rashi = (lagna_rashi + N - 1) % 12 | Whole Sign only |
| House N cusp ≤ House N+1 cusp (mod 360) | All systems |
| Cusps are in [0, 360) | All systems |
| 12 distinct house numbers 1–12 | All systems |

---

## 9. Tolerance Specification

| Field | Absolute Tolerance | System | Notes |
|-------|-------------------|--------|-------|
| Whole Sign sidereal cusp | ±0.001° | W | Should be exact (sign boundary) |
| Equal sidereal cusp | ±0.001° | E | Should be exact (asc + offset) |
| Placidus sidereal cusp | ±0.1° | P | May vary with ephemeris precision |
| Koch sidereal cusp | ±0.1° | K | May vary with ephemeris precision |
| House rashi | Exact | All | Determined from longitude |
| Classification | Exact | All | Deterministic lookup |
| House lord | Exact | All | Deterministic lookup |
| Planet-house assignment | Exact | All | Determined by planet rashi vs house cusp rashi |

---

## 10. Confidence Classification

| Tier | Label | Applicable To |
|------|-------|---------------|
| **A** | VERIFIED | Whole Sign cusps (mathematically exact), Equal cusps (mathematically exact), House classifications (deterministic), House lords (deterministic) |
| **B** | ESTIMATED | Placidus cusps, Koch cusps — consistent with Swiss Ephemeris but not independently verified |
| **C** | SYNTHETIC | Future latitude-sweep synthetic data |
| **D** | UNKNOWN | Any external house cross-check where tool version is uncertain |

---

## 11. Evidence & References

| Reference | Type | Location |
|-----------|------|----------|
| Swiss Ephemeris `swe.houses()` | API documentation | https://www.astro.com/swisseph/swephprg.htm |
| AstroOS EphemerisWrapper.get_ascendant_and_cusps | Source | `apps/api/services/ephemeris_wrapper.py` |
| AstroOS HouseEngine | Source | `apps/api/services/house_engine.py` |
| AstroOS House domain models | Source | `apps/api/domain/house.py` |
| SIGN_LORDS constant | Source | `packages/shared/constants.py` |
| RF-SIGNS (RDO) | Dataset | RDO Phase A |
| External house reference (astro.com) | Web tool | https://www.astro.com |

---

## 12. Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **No independent Placidus reference** | Placidus cusps validated against Swiss Ephemeris itself, not an independent source | Cross-check against astro.com or Jagannatha Hora recommended in documentation |
| **Koch is rarely used in Vedic** | Lower priority for independent verification | Accept Swiss Ephemeris as reference |
| **Intercepted signs** | Complex to validate programmatically | Document intercepted signs as special cases |
| **Polar latitude ambiguity** | Placidus/Koch break down at polar latitudes (>66.5°) | Restrict benchmark to latitudes ≤66°; document polar limitation |
| **House number assignment in Whole Sign** | Uses rashi-index-from-lagna, which is classical but not universally accepted | Benchmark documents the convention |

---

## 13. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief QA & Benchmark Architect (Agent 4) | Initial specification |

---

*End of BM-HOUSE Master Specification. Defines the WHAT and WHY of house cusp benchmarks across all 4 house systems.*
