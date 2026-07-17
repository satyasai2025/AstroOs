# BM-CALC — Expected Results Specification

> **Part Of:** BM-CALC Benchmark Family
> **Version:** 1.0.0
> **Status:** DRAFT (Phase 4)
> **Date:** 2026-07-15

---

## 1. Purpose

This document defines the expected outcomes and validation criteria for all BM-CALC benchmark tests. Per the Benchmark Office methodology, this document does NOT compute actual planet positions — the expected values are derived from a canonical reference run of the Swiss Ephemeris engine, captured at benchmark creation time and stored as content-addressed golden results.

---

## 2. Reference Computation Method

### 2.1 Primary Reference Engine

```yaml
engine: Swiss Ephemeris (pyswisseph)
mode: official  # .se1 data files preferred; Moshier fallback documented
ayanamsa: per test case  # all 6 systems tested
precision: IEEE 754 double-precision floating point
calling_code: EphemerisWrapper (apps/api/services/ephemeris_wrapper.py)
```

### 2.2 Reference Run Protocol

1. Set environment: `ASTROOS_BENCHMARK_MODE=reference`
2. For each (chart, ayanamsa, house_system, ephemeris_mode):
   a. Construct `EphemerisWrapper` with the specified parameters
   b. Call `get_planet_positions()` for all 9 grahas
   c. Call `calculate_lagna()` for ascendant
   d. Call `get_ayanamsa_value()` for the ayanamsa
   e. Serialize full output to deterministic JSON
3. Compute SHA-256 content hash of the JSON output
4. Store as the expected result

### 2.3 Determinism Guarantee

Multiple reference runs with identical inputs MUST produce identical JSON output. If non-determinism is detected:

1. Flag the benchmark as UNSTABLE
2. Identify the source of non-determinism (floating-point, threading, random seeds)
3. Do not promote to STABLE until resolved

---

## 3. Expected Output per Test Case

### 3.1 BM-CALC-001 through BM-CALC-005 (Single Chart × Lahiri)

Each test produces one expected result file containing:

```json
{
  "benchmark_id": "BM-CALC-NNN",
  "chart_id": "GC-REF-00N",
  "reference_run_id": "sha256:<hash>",
  "reference_timestamp": "2026-07-15T00:00:00Z",
  "ephemeris_mode": "official",
  "configuration": {
    "ayanamsa": "lahiri",
    "house_system": "W"
  },
  "expected": {
    "ayanamsa_value": "<float>",
    "lagna": {
      "longitude": "<float>",
      "rashi": "<string>",
      "rashi_degree": "<float>"
    },
    "planets": [
      {
        "planet": "Sun",
        "sidereal_longitude": "<float>",
        "latitude_deg": "<float>",
        "speed_deg_per_day": "<float>",
        "declination_deg": "<float>",
        "rashi": "<string>",
        "rashi_degree": "<float>",
        "nakshatra": "<string>",
        "nakshatra_pada": "<int>",
        "is_retrograde": false,
        "is_combust": false,
        "distance_au": "<float>"
      }
    ]
  }
}
```

**Expected outcome:** All 9 grahas present; all fields populated; content hash matches reference.

### 3.2 BM-CALC-006 through BM-CALC-007 (Ayanamsa Cross-Check)

Same structure as above, repeated for each of the 6 ayanamsa systems.

**Expected outcome:** 6 result files per chart, each with different `ayanamsa_value` and correspondingly shifted `sidereal_longitude` values. Every other field (latitude, speed, declination, retrograde, combust) MUST be identical across ayanamsa systems for the same planet — only longitude and its derivatives (rashi, rashi_degree) change.

### 3.3 BM-CALC-008 (Ephemeris Mode Comparison)

Two expected result files:
- BM-CALC-008a: Official .se1 mode
- BM-CALC-008b: Moshier fallback mode

**Expected outcome:** Longitude disagreement ≤ 0.0167° (1 arc-minute) between modes. Moshier positions recorded separately, NEVER conflated with official-mode results. Files carry different `ephemeris_mode` and different expected values.

### 3.4 BM-CALC-009 (Retrograde Determination)

**Expected outcome:** For each of the 9 grahas, the `is_retrograde` flag is determined by the sign of `speed_deg_per_day`:
- Positive speed → direct motion → `is_retrograde: false`
- Negative speed → retrograde motion → `is_retrograde: true`
- Speed = 0 → stationary → `is_retrograde: false` (flagged as edge case)

**Validation:** Cross-check against `swe_get_planet`s retrograde flag from pyswisseph.

### 3.5 BM-CALC-010 (Combustion Determination)

**Expected outcome:** For each of the 9 grahas, `is_combust` is true if the planet's angular distance from the Sun is within its classical combustion orb:

| Planet | Orb (degrees) |
|--------|--------------|
| Moon | 12 |
| Mars | 17 |
| Mercury | 14 (or 7° if heliacal rising) |
| Jupiter | 11 |
| Venus | 10 (or 8° if heliacal rising) |
| Saturn | 15 |
| Rahu | N/A (never combust) |
| Ketu | N/A (never combust) |

**Validation:** Cross-check against `EphemerisWrapper.is_combust()` method.

### 3.6 BM-CALC-011 (Nakshatra/Pada Assignment)

**Expected outcome:** For each planet at its computed sidereal longitude:
- `nakshatra` — determined by which of the 27 equal 13.333...° lunar mansions contains the longitude
- `nakshatra_pada` — determined by which of the 4 equal 3.333...° quarters within that nakshatra

**Validation:** Cross-check against Nakshatra/Pada reference tables from RF-NAK and RF-PADA (RDO datasets).

### 3.7 BM-CALC-014 (Speed Computation)

**Expected outcome:** `speed_deg_per_day` for each planet reflects the instantaneous daily motion:
- Outer planets (Jupiter, Saturn): ~0°–0.25°/day
- Inner planets (Mercury, Venus): ~0°–2°/day
- Mars: ~0°–0.8°/day
- Sun: ~0.9856°/day (nearly constant)
- Moon: ~12°–15°/day (fastest)
- Rahu/Ketu: ~-0.053°/day (always retrograde)

**Validation:** Cross-check against `swe_get_planet`s speed field from pyswisseph.

---

## 4. Validation Criteria

### 4.1 Numeric Field Validation

| Field | Validation Type | Check |
|-------|----------------|-------|
| `sidereal_longitude` | Range | [0, 360) |
| `latitude_deg` | Range | [-90, 90] |
| `speed_deg_per_day` | Range | [-30, 30] |
| `declination_deg` | Range | [-90, 90] |
| `distance_au` | Range | (0, 50] |
| `rashi_degree` | Range | [0, 30) |
| `nakshatra_pada` | Range | {1, 2, 3, 4} |

### 4.2 Consistency Validation

| Check | Description |
|-------|-------------|
| Sun longitude ≠ Moon longitude | At any epoch |
| All 9 grahas present | No missing planets |
| No duplicate planets | Exactly one entry per graha |
| Rashi consistent with longitude | floor(longitude / 30) + 1 = rashi index |
| Nakshatra consistent with longitude | floor(longitude / 13.333...) = nakshatra index |
| Pada consistent with nakshatra position | floor((longitude % 13.333...) / 3.333...) + 1 = pada |

### 4.3 Determinism Validation

| Check | Method |
|-------|--------|
| Same input → same output | Content hash comparison |
| Cross-run identical | Consecutive runs produce byte-identical JSON |

---

## 5. Known Expected Behaviors

| Behavior | Expected | Rationale |
|----------|----------|-----------|
| Sun's speed near 0.9856°/day | Always true | Earth's orbital motion is nearly constant |
| Moon's speed 12–15°/day | Always true | Moon's orbital motion is fast |
| Rahu/Ketu always within 0–1° of opposite | Always true | Nodes are always ~180° apart |
| Rahu/Ketu speed ~ -0.053°/day | Always true | Lunar nodes regress ~19.3°/year |
| Rahu/Ketu never combust | Always true | Nodes are shadow planets, no physical body |
| Inner planets retrograde ~3×/year | True for Mars, Mercury, Venus, Jupiter, Saturn | Synodic cycle |
| Outer planets retrograde ~1×/year | True for Jupiter, Saturn | Opposition cycle |
| Mercury always within 28° of Sun | Always true | Maximum elongation of Mercury |

---

## 6. Reference Data Sources

| Reference | Type | Used For |
|-----------|------|----------|
| Swiss Ephemeris (pyswisseph) | Primary engine | All expected values |
| JPL DE431/DE440 | Underlying ephemeris | Swiss Ephemeris source data |
| RF-SIGNS (RDO dataset) | Reference | Rashi names, lords, elements |
| RF-NAK (RDO dataset) | Reference | Nakshatra names, lords, degrees |
| RF-PADA (RDO dataset) | Reference | Pada degrees, Navamsha mapping |
| RF-AYAN (RDO dataset) | Reference | Ayanamsa values per system |
| Nakshatra/Pada computation | Derived | Longitude → Nakshatra → Pada |

---

## 7. Versioning & Updates

Expected results are versioned with the benchmark:

| Event | Action | Version Impact |
|-------|--------|----------------|
| New chart added | Add expected result file | MINOR version bump |
| Ephemeris engine change | Re-compute all expected results | MAJOR version bump |
| Ayanamsa value change | Re-compute affected results | MAJOR version bump |
| Tolerance change | Document in spec only | PATCH version bump |
| New graha/field added | Add to expected structure | MINOR version bump |

---

## 8. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief QA & Benchmark Architect (Agent 4) | Initial expected results specification |

---

*End of BM-CALC Expected Results Specification. Expected values are NOT computed in this document — they are captured from a canonical reference run when the benchmark is executed.*
