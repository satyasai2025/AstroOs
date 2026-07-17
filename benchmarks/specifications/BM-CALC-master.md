# BM-CALC — Planet Position Calculation Benchmarks (Master Specification)

> **Benchmark Family:** BM-CALC
> **Version:** 1.0.0
> **Status:** DRAFT
> **Owner:** Chief QA & Benchmark Architect (Agent 4)
> **Date:** 2026-07-15

---

## 1. Identification

| Field | Value |
|-------|-------|
| **Family ID** | `BM-CALC` |
| **Full Title** | Planet Position Calculation Benchmarks |
| **AstroOS Modules Tested** | M2 — Chart Engine (EphemerisWrapper, EphemerisService) |
| **Depends On** | Swiss Ephemeris (pyswisseph), JPL Horizons reference data |
| **Required By** | BM-HOUSE, BM-VARGA, BM-YOGA, BM-BALA, BM-ASTAK, BM-TRANSIT, BM-DASHA |

---

## 2. Purpose & Scope

**Purpose:**
Verify that AstroOS computes planetary positions (sidereal longitude, latitude, speed, declination, rashi, nakshatra, pada) for all 9 grahas (Sun through Ketu) with accuracy matching the Swiss Ephemeris reference engine. This is the foundational benchmark — every higher-order calculation (houses, vargas, yogas, dashas, transits, shadbala) depends on correct planet positions.

**Category:** Calculation Accuracy
**Difficulty:** FOUNDATION
**Risk if Failed:** All higher-order calculations produce incorrect results

**Related Benchmarks:**
- Required by: BM-HOUSE (house cusps), BM-VARGA (divisional charts), BM-YOGA (yoga detection), BM-BALA (shadbala), BM-ASTAK (ashtakavarga), BM-TRANSIT (gochara), BM-DASHA (dasha computation)
- Also uses: RF-AYAN (ayanamsa reference data from RDO)

---

## 3. Test Matrix

### 3.1 Dimensions Tested

| Dimension | Values | Coverage |
|-----------|--------|----------|
| **Grahas** | Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu | All 9 |
| **Ayanamsa systems** | Lahiri, KP, Raman, Yukteshwar, Fagan-Bradley, True Chitra | All 6 supported |
| **Reference charts** | 5 charts (see §4) | Diverse birth epochs |
| **House systems** | Whole Sign, Placidus, Koch, Equal | All 4 supported |
| **Ephemeris modes** | Moshier fallback, Official .se1 | Both modes |

### 3.2 Individual Test Cases

| Test ID | Focus | Input Variation |
|---------|-------|----------------|
| BM-CALC-001 | Full position set — 9 grahas, Lahiri, REF-001 | Chart 1, 1 ayanamsa |
| BM-CALC-002 | Full position set — 9 grahas, Lahiri, REF-002 | Chart 2, 1 ayanamsa |
| BM-CALC-003 | Full position set — 9 grahas, Lahiri, REF-003 | Chart 3, 1 ayanamsa |
| BM-CALC-004 | Full position set — 9 grahas, Lahiri, REF-004 | Chart 4, 1 ayanamsa |
| BM-CALC-005 | Full position set — 9 grahas, Lahiri, REF-005 | Chart 5, 1 ayanamsa |
| BM-CALC-006 | Ayanamsa cross-check — REF-001, all 6 ayanamsa systems | Chart 1, 6 ayanamsa |
| BM-CALC-007 | Ayanamsa cross-check — REF-002, all 6 ayanamsa systems | Chart 2, 6 ayanamsa |
| BM-CALC-008 | Ephemeris mode comparison — Moshier vs Official, REF-001 | Chart 1, both modes |
| BM-CALC-009 | Retrograde determination — all 9 grahas, REF-003 | Chart 3, retrograde flags |
| BM-CALC-010 | Combustion determination — all 9 grahas, REF-004 | Chart 4, combustion flags |
| BM-CALC-011 | Nakshatra/pada assignment — all 9 grahas, REF-005 | Chart 5, nakshatra binding |
| BM-CALC-012 | Planet longitude precision — boundary values | Boundary cases (0°, 360°, sign edges) |
| BM-CALC-013 | Declination computation — all 9 grahas, REF-001 | Chart 1, declination check |
| BM-CALC-014 | Speed computation — all 9 grahas, REF-002 | Chart 2, speed check |

---

## 4. Reference Charts

### 4.1 Chart Candidates (Phase 3 — Dataset Design)

The following candidate charts are identified for the GC-MASTER dataset. Actual inclusion requires birth data sourcing and verification (Phase 3).

| Candidate ID | Person | Birth Date | Birth Location | Source Status |
|-------------|--------|-------------|----------------|---------------|
| REF-001 | TBD — Chart 1 candidate | TBD | TBD | Source identification needed |
| REF-002 | TBD — Chart 2 candidate | TBD | TBD | Source identification needed |
| REF-003 | TBD — Chart 3 candidate | TBD | TBD | Source identification needed |
| REF-004 | TBD — Chart 4 candidate | TBD | TBD | Source identification needed |
| REF-005 | TBD — Chart 5 candidate | TBD | TBD | Source identification needed |

**Chart selection criteria:**
1. Birth timestamp documented to minute precision (Tier B+)
2. Geographic coordinates known to city level
3. Diverse birth epochs (spanning 1850–2000 at minimum)
4. Diverse geographic regions (North America, Europe, Asia, at minimum)
5. Public figure with documented biographical record
6. Not fabricated — every candidate must have a citable source

**Source requirement:** Every chart's birth data must be traceable to a primary or authoritative secondary source (biography, birth certificate, official record, or verified astrological reference citing same).

### 4.2 Chart Configuration Dimensions

Every chart in the benchmark suite is tested across:

| Parameter | Values to Test |
|-----------|---------------|
| ayanamsa | Lahiri, KP, Raman, Yukteshwar, Fagan-Bradley, True Chitra |
| house_system | W (Whole Sign), P (Placidus), K (Koch), E (Equal) |
| ephemeris_mode | moshier, official |

**Full matrix per chart:** 6 ayanamsa × 4 house systems × 2 ephemeris modes = 48 configurations per chart.

---

## 5. Expected Outputs

### 5.1 Per-Planet Output Structure

Every benchmark test produces, for each of the 9 grahas:

```json
{
  "planet": "Jupiter",
  "sidereal_longitude": 128.4567,
  "latitude_deg": 0.9876,
  "speed_deg_per_day": 0.1234,
  "declination_deg": 15.6789,
  "rashi": "Leo",
  "rashi_degree": 8.4567,
  "nakshatra": "Magha",
  "nakshatra_pada": 2,
  "is_retrograde": false,
  "is_combust": false,
  "distance_au": 5.203
}
```

### 5.2 Per-Chart Output Structure

```json
{
  "chart_id": "REF-001",
  "ayanamsa_system": "lahiri",
  "ayanamsa_value": 24.1234,
  "house_system": "W",
  "lagna_rashi": "Virgo",
  "lagna_degree": 12.3456,
  "planet_positions": [ ... 9 entries ... ]
}
```

### 5.3 Benchmark Result Structure

```json
{
  "benchmark_id": "BM-CALC-001",
  "version": "1.0.0",
  "timestamp": "2026-07-15T00:00:00Z",
  "result": "PASS" | "FAIL" | "WARN",
  "summary": {
    "total_checks": 99,
    "passed": 99,
    "failed": 0,
    "warnings": 0,
    "pass_rate": 1.0
  },
  "checks": [
    {
      "planet": "Jupiter",
      "field": "sidereal_longitude",
      "expected": 128.4567,
      "actual": 128.4568,
      "tolerance": 0.1,
      "diff": 0.0001,
      "passed": true
    }
  ]
}
```

---

## 6. Acceptance Criteria

### 6.1 Hard Requirements (100% Pass Required)

| # | Criterion | Tolerance | Source |
|---|-----------|-----------|--------|
| H1 | Sidereal longitude — 9 grahas | ±0.1° | Swiss Ephemeris reference |
| H2 | Ayanamsa value | ±0.01° | Swiss Ephemeris `swe_get_ayanamsa` |
| H3 | Lagna (ascendant) longitude | ±0.1° | Swiss Ephemeris reference |
| H4 | Rashi assignment | Exact match | Derived from H1 |
| H5 | Nakshatra assignment | Exact match | Derived from H1 |
| H6 | Nakshatra pada | Exact match | Derived from H1 |
| H7 | Retrograde flag | Exact match | Speed sign check |
| H8 | Combustion flag | Exact match | Angular distance from Sun |

### 6.2 Soft Requirements (≥ 95% Pass, Reported)

| # | Criterion | Tolerance | Source |
|---|-----------|-----------|--------|
| S1 | Celestial latitude | ±0.1° | Swiss Ephemeris reference |
| S2 | Speed (deg/day) | ±0.01°/day | Swiss Ephemeris reference |
| S3 | Declination | ±0.1° | Swiss Ephemeris reference |
| S4 | Distance (AU) | ±0.001 AU | Swiss Ephemeris reference |
| S5 | Moshier-vs-Official agreement | ±1.0 arc-minute (0.0167°) | Both ephemeris modes |

### 6.3 Determinism Requirement

Running the same benchmark input twice MUST produce identical output (content hash match). Non-determinism is an automatic FAIL.

---

## 7. Validation Method

### 7.1 Primary Validation

Reference values computed using **Swiss Ephemeris** (pyswisseph) with official `.se1` data files, running the exact same `EphemerisWrapper` code path that AstroOS uses in production.

**Rationale:** The benchmark validates that AstroOS's own calculation engine produces correct results. Using Swiss Ephemeris as both the production engine and the reference eliminates toolchain variance as a confounding factor. The question being answered is: "Does AstroOS use Swiss Ephemeris correctly?"

### 7.2 Secondary Validation (Independent)

A subset of positions (1 chart × Lahiri ayanamsa) is independently computed using **JPL Horizons** ephemeris to confirm that Swiss Ephemeris itself is producing astronomically correct values. Any disagreement between Swiss Ephemeris and JPL Horizons is flagged and documented as a known ephemeris limitation, not an AstroOS bug.

### 7.3 Validation Process

```
1. Compute reference values →
   Run EphemerisWrapper with official .se1 data, dump JSON
2. Compute test values →
   Run AstroOS API endpoint /api/v1/horoscope/d1 with same inputs
3. Compare →
   Structured comparison script: every field × every planet × tolerance check
4. Report →
   PASS/FAIL per test case, aggregated into family report
5. Archive →
   Result file + content hash stored in benchmarks/results/
```

### 7.4 Reference Value Computation

Reference values are NOT hand-calculated or asserted by fiat. They are computed by the same `EphemerisWrapper` engine, but flagged as the "reference run" via environment variable `ASTROOS_BENCHMARK_MODE=reference`. This run's output is captured, content-hashed, and stored as the expected result. Future runs compare against the stored hash.

**This means** a benchmark update is required whenever the ephemeris engine changes — the reference values are re-computed and the hash updated. This is intentional: the benchmark verifies that the engine produces CONSISTENT results, not that some externally-sourced numbers match.

---

## 8. Tolerance Specification

| Field | Absolute Tolerance | Relative Tolerance | Unit | Rationale |
|-------|-------------------|-------------------|------|-----------|
| `sidereal_longitude` | ±0.1 | — | degrees | ~6 arc-minutes; accommodates Moshier fallback |
| `latitude_deg` | ±0.1 | — | degrees | Celestial latitude precision |
| `speed_deg_per_day` | ±0.01 | — | deg/day | Daily motion is a smooth derivative |
| `declination_deg` | ±0.1 | — | degrees | Equatorial frame precision |
| `distance_au` | ±0.001 | — | AU | Heliocentric distance |
| `ayanamsa_value` | ±0.01 | — | degrees | Ayanamsa precision |
| `rashi_degree` | ±0.1 | — | degrees | Within-sign position |
| `lagna_degree` | ±0.1 | — | degrees | Ascendant precision |

**Tolerance note:** The ±0.1° longitude tolerance is set to accommodate the Moshier polynomial approximation (~1 arc-minute = 0.0167°). When running with official `.se1` data, actual disagreement should be < 0.001°.

---

## 9. Confidence Classification

| Tier | Label | Applicable To |
|------|-------|---------------|
| **A** | VERIFIED | Positions computed with official .se1 data AND cross-checked against JPL Horizons |
| **B** | ESTIMATED | Positions consistent with Swiss Ephemeris but not independently cross-checked |
| **C** | SYNTHETIC | Random chart positions (future Phase B synthetic datasets) |
| **D** | UNKNOWN | Any position where ephemeris source is uncertain |

All BM-CALC reference values initially carry **Tier A (VERIFIED)** for the primary reference run and **Tier B (ESTIMATED)** for cross-mode comparisons (Moshier vs Official).

---

## 10. Evidence & References

| Reference | Type | Location/Status |
|-----------|------|-----------------|
| Swiss Ephemeris documentation | API docs | https://www.astro.com/swisseph/swephprg.htm |
| JPL Horizons Web API | API | https://ssd-api.jpl.nasa.gov/doc/horizons.html |
| pyswisseph source | Library | https://github.com/astrorigin/pyswisseph |
| AstroOS EphemerisWrapper | Source | `apps/api/services/ephemeris_wrapper.py` |
| AstroOS EphemerisService | Source | `apps/api/services/ephemeris_service.py` |
| AstroOS HoroscopeEngine | Source | `apps/api/services/horoscope_engine.py` |
| Test ephemeris wrapper | Tests | `tests/unit/test_ephemeris_wrapper.py` (existing, 100% coverage) |
| Reference chart sources | TBD | Phase 3 deliverable |

---

## 11. Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Moshier fallback accuracy** | ±1 arc-minute vs official ephemeris | Official .se1 data is recommended; Moshier tolerance set to ±0.1° |
| **Rahu/Ketu positions** | Computed as mean lunar nodes, not true nodes | Matches Swiss Ephemeris default; document which node type is used |
| **JPL Horizons discrepancy** | Swiss Ephemeris may differ from JPL at sub-arcsecond level | Flagged, not failed; documented in results |
| **Ayanamsa value drift over time** | Ayanamsa is recomputed per epoch; reference values are epoch-specific | Every reference value carries its computation epoch |
| **Ephemeris file availability** | Official .se1 files require download from astro.com | Benchmark documents ephemeris file presence in results |
| **Pre-1600 dates** | Swiss Ephemeris accuracy degrades before 1600 CE | BM-CALC charts are restricted to 1850–present |

---

## 12. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief QA & Benchmark Architect (Agent 4) | Initial specification |

---

## 13. Approval

| Role | Status | Date |
|------|--------|------|
| Chief QA & Benchmark Architect | PENDING | — |

---

*End of BM-CALC Master Specification. This document defines the WHAT and WHY of planet position benchmarks. The actual reference chart data and expected values are Phase 3/Phase 4 deliverables.*
