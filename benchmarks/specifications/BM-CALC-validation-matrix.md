# BM-CALC — Validation Matrix

> **Part Of:** BM-CALC Benchmark Family
> **Version:** 1.0.0
> **Status:** DRAFT (Phase 5)
> **Date:** 2026-07-15

---

## 1. Purpose

This validation matrix defines the complete set of validation checks applied to planet position calculations in AstroOS. Every row represents one validation point. The matrix maps: what is validated → how it is validated → what reference it is validated against → what passes or fails.

---

## 2. Core Validation Matrix

### 2.1 Planet Position Calculation — Individual Fields

| ID | Component | Validation Method | Reference Source | Hard/Soft | Tolerance |
|----|-----------|-------------------|-----------------|-----------|-----------|
| VC-001 | Sun — sidereal longitude | Compare vs reference run | Swiss Ephemeris | HARD | ±0.1° |
| VC-002 | Moon — sidereal longitude | Compare vs reference run | Swiss Ephemeris | HARD | ±0.1° |
| VC-003 | Mars — sidereal longitude | Compare vs reference run | Swiss Ephemeris | HARD | ±0.1° |
| VC-004 | Mercury — sidereal longitude | Compare vs reference run | Swiss Ephemeris | HARD | ±0.1° |
| VC-005 | Jupiter — sidereal longitude | Compare vs reference run | Swiss Ephemeris | HARD | ±0.1° |
| VC-006 | Venus — sidereal longitude | Compare vs reference run | Swiss Ephemeris | HARD | ±0.1° |
| VC-007 | Saturn — sidereal longitude | Compare vs reference run | Swiss Ephemeris | HARD | ±0.1° |
| VC-008 | Rahu — sidereal longitude | Compare vs reference run | Swiss Ephemeris | HARD | ±0.1° |
| VC-009 | Ketu — sidereal longitude | Compare vs reference run | Swiss Ephemeris | HARD | ±0.1° |
| VC-010 | Sun — latitude | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-011 | Moon — latitude | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-012 | Mars — latitude | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-013 | Mercury — latitude | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-014 | Jupiter — latitude | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-015 | Venus — latitude | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-016 | Saturn — latitude | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-017 | Rahu — latitude | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-018 | Ketu — latitude | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-019 | Sun — speed | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.01°/day |
| VC-020 | Moon — speed | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.01°/day |
| VC-021 | Mars — speed | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.01°/day |
| VC-022 | Mercury — speed | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.01°/day |
| VC-023 | Jupiter — speed | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.01°/day |
| VC-024 | Venus — speed | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.01°/day |
| VC-025 | Saturn — speed | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.01°/day |
| VC-026 | Rahu — speed | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.01°/day |
| VC-027 | Ketu — speed | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.01°/day |
| VC-028 | Sun — declination | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-029 | Moon — declination | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-030 | Mars — declination | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-031 | Mercury — declination | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-032 | Jupiter — declination | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-033 | Venus — declination | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-034 | Saturn — declination | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-035 | Rahu — declination | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-036 | Ketu — declination | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.1° |
| VC-037 | Sun — Rashi assignment | Longitude → Rashi mapping | RF-SIGNS | HARD | Exact |
| VC-038 | Moon — Rashi assignment | Longitude → Rashi mapping | RF-SIGNS | HARD | Exact |
| VC-039 | Mars — Rashi assignment | Longitude → Rashi mapping | RF-SIGNS | HARD | Exact |
| VC-040 | Mercury — Rashi assignment | Longitude → Rashi mapping | RF-SIGNS | HARD | Exact |
| VC-041 | Jupiter — Rashi assignment | Longitude → Rashi mapping | RF-SIGNS | HARD | Exact |
| VC-042 | Venus — Rashi assignment | Longitude → Rashi mapping | RF-SIGNS | HARD | Exact |
| VC-043 | Saturn — Rashi assignment | Longitude → Rashi mapping | RF-SIGNS | HARD | Exact |
| VC-044 | Rahu — Rashi assignment | Longitude → Rashi mapping | RF-SIGNS | HARD | Exact |
| VC-045 | Ketu — Rashi assignment | Longitude → Rashi mapping | RF-SIGNS | HARD | Exact |
| VC-046 | Sun — Nakshatra assignment | Longitude → Nakshatra mapping | RF-NAK | HARD | Exact |
| VC-047 | Moon — Nakshatra assignment | Longitude → Nakshatra mapping | RF-NAK | HARD | Exact |
| VC-048 | Mars — Nakshatra assignment | Longitude → Nakshatra mapping | RF-NAK | HARD | Exact |
| VC-049 | Mercury — Nakshatra assignment | Longitude → Nakshatra mapping | RF-NAK | HARD | Exact |
| VC-050 | Jupiter — Nakshatra assignment | Longitude → Nakshatra mapping | RF-NAK | HARD | Exact |
| VC-051 | Venus — Nakshatra assignment | Longitude → Nakshatra mapping | RF-NAK | HARD | Exact |
| VC-052 | Saturn — Nakshatra assignment | Longitude → Nakshatra mapping | RF-NAK | HARD | Exact |
| VC-053 | Rahu — Nakshatra assignment | Longitude → Nakshatra mapping | RF-NAK | HARD | Exact |
| VC-054 | Ketu — Nakshatra assignment | Longitude → Nakshatra mapping | RF-NAK | HARD | Exact |
| VC-055 | Sun — Nakshatra pada | Longitude → Pada mapping | RF-PADA | HARD | Exact |
| VC-056 | Moon — Nakshatra pada | Longitude → Pada mapping | RF-PADA | HARD | Exact |
| VC-057 | Mars — Nakshatra pada | Longitude → Pada mapping | RF-PADA | HARD | Exact |
| VC-058 | Mercury — Nakshatra pada | Longitude → Pada mapping | RF-PADA | HARD | Exact |
| VC-059 | Jupiter — Nakshatra pada | Longitude → Pada mapping | RF-PADA | HARD | Exact |
| VC-060 | Venus — Nakshatra pada | Longitude → Pada mapping | RF-PADA | HARD | Exact |
| VC-061 | Saturn — Nakshatra pada | Longitude → Pada mapping | RF-PADA | HARD | Exact |
| VC-062 | Rahu — Nakshatra pada | Longitude → Pada mapping | RF-PADA | HARD | Exact |
| VC-063 | Ketu — Nakshatra pada | Longitude → Pada mapping | RF-PADA | HARD | Exact |
| VC-064 | Sun — retrograde flag | Speed sign check | Swiss Ephemeris | HARD | Exact |
| VC-065 | Moon — retrograde flag | Speed sign check | Swiss Ephemeris | HARD | Exact |
| VC-066 | Mars — retrograde flag | Speed sign check | Swiss Ephemeris | HARD | Exact |
| VC-067 | Mercury — retrograde flag | Speed sign check | Swiss Ephemeris | HARD | Exact |
| VC-068 | Jupiter — retrograde flag | Speed sign check | Swiss Ephemeris | HARD | Exact |
| VC-069 | Venus — retrograde flag | Speed sign check | Swiss Ephemeris | HARD | Exact |
| VC-070 | Saturn — retrograde flag | Speed sign check | Swiss Ephemeris | HARD | Exact |
| VC-071 | Rahu — retrograde flag | Speed sign check | Swiss Ephemeris | HARD | Exact |
| VC-072 | Ketu — retrograde flag | Speed sign check | Swiss Ephemeris | HARD | Exact |
| VC-073 | Sun — combustion flag | Angular distance from Sun | Swiss Ephemeris | HARD | Exact |
| VC-074 | Moon — combustion flag | Angular distance from Sun | Swiss Ephemeris | HARD | Exact |
| VC-075 | Mars — combustion flag | Angular distance from Sun | Swiss Ephemeris | HARD | Exact |
| VC-076 | Mercury — combustion flag | Angular distance from Sun | Swiss Ephemeris | HARD | Exact |
| VC-077 | Jupiter — combustion flag | Angular distance from Sun | Swiss Ephemeris | HARD | Exact |
| VC-078 | Venus — combustion flag | Angular distance from Sun | Swiss Ephemeris | HARD | Exact |
| VC-079 | Saturn — combustion flag | Angular distance from Sun | Swiss Ephemeris | HARD | Exact |
| VC-080 | Rahu — combustion flag | Never combust | N/A | HARD | Trivially false |
| VC-081 | Ketu — combustion flag | Never combust | N/A | HARD | Trivially false |
| VC-082 | Sun — distance AU | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.001 AU |
| VC-083 | Moon — distance AU | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.001 AU |
| VC-084 | Mars — distance AU | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.001 AU |
| VC-085 | Mercury — distance AU | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.001 AU |
| VC-086 | Jupiter — distance AU | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.001 AU |
| VC-087 | Venus — distance AU | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.001 AU |
| VC-088 | Saturn — distance AU | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.001 AU |
| VC-089 | Rahu — distance AU | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.001 AU |
| VC-090 | Ketu — distance AU | Compare vs reference run | Swiss Ephemeris | SOFT | ±0.001 AU |

### 2.2 Summary

| Dimension | Count |
|-----------|-------|
| Total validation checks | 90 |
| Hard checks | 63 (70%) |
| Soft checks | 27 (30%) |
| Charts covered | 5 (GC-REF-001 through GC-REF-005) |
| Ayanamsa systems | 6 |
| House systems | 4 |
| Total distinct configurations | 5 charts × 6 ayanamsa × 4 house = 120 configurations |
| Total validation points (full matrix) | 120 × 90 checks = 10,800 |

---

## 3. Cross-Dimension Validation

### 3.1 Ayanamsa Consistency

| ID | Check | Method |
|----|-------|--------|
| VC-AY-001 | Ayanamsa value matches Swiss Ephemeris | `swe_get_ayanamsa(jd)` |
| VC-AY-002 | Ayanamsa is monotonic (increasing with date) | Check epoch 1850 < 1950 < 2000 |
| VC-AY-003 | Ayanamsa values distinct per system | Lahiri ≠ KP ≠ Raman ≠ Yukteshwar ≠ Fagan-Bradley ≠ True Chitra |
| VC-AY-004 | Longitude shift matches ayanamsa difference | Δlongitude = Δayanamsa across any 2 systems |
| VC-AY-005 | Latitude/speed/declination independent of ayanamsa | Identical values across all 6 systems for same planet |

### 3.2 Ephemeris Mode Consistency

| ID | Check | Tolerance |
|----|-------|-----------|
| VC-EM-001 | Official vs Moshier longitude match | ≤ 0.0167° (1 arc-minute) |
| VC-EM-002 | Official vs Moshier retrograde flag match | Exact |
| VC-EM-003 | Official vs Moshier combustion flag match | Exact |
| VC-EM-004 | Official vs Moshier Rashi assignment match | Exact (within tolerance of VC-EM-001) |

### 3.3 Planetary Relationship Validity

| ID | Check | Rationale |
|----|-------|-----------|
| VC-PR-001 | Sun ≠ Moon longitude at any epoch | Always separated |
| VC-PR-002 | Mercury within 28° of Sun | Maximum elongation constraint |
| VC-PR-003 | Venus within 47° of Sun | Maximum elongation constraint |
| VC-PR-004 | Rahu + 180° ≈ Ketu longitude | Nodes always ~opposite |
| VC-PR-005 | Rahu/Ketu speed ≈ -0.053°/day (always retrograde) | Nodal regression rate |
| VC-PR-006 | Moon speed >> all other planet speeds | Moon completes 360° in ~27.3 days |
| VC-PR-007 | Sun speed ~0.9856°/day | Earth's orbital period |

### 3.4 Range Validation

| ID | Check | Allowed Range |
|----|-------|---------------|
| VC-RNG-001 | Sidereal longitude | [0, 360) |
| VC-RNG-002 | Latitude | [-90, 90] |
| VC-RNG-003 | Speed | [-30, 30] for Moon; [-2, 2] for all others |
| VC-RNG-004 | Declination | [-90, 90] |
| VC-RNG-005 | Distance AU | (0, 50] |
| VC-RNG-006 | Rashi degree | [0, 30) |
| VC-RNG-007 | Nakshatra pada | {1, 2, 3, 4} |
| VC-RNG-008 | 9 grahas present | Exactly 9 entries |
| VC-RNG-009 | No duplicate grahas | All graha names unique |

---

## 4. Chart-Specific Validation

### 4.1 Expected Invariants Per Chart

| Chart | Known Planet | Expected Behavior |
|-------|-------------|-------------------|
| GC-REF-001 (Elizabeth II) | Jupiter | In Aquarius (1926) — personal research correlation |
| GC-REF-002 (Barack Obama) | Sun | In Leo (1961) — Sun in its own sign |
| GC-REF-003 (Narendra Modi) | Saturn | Check sign — epoch 1950 |
| GC-REF-004 (Virat Kohli) | Mercury | Check sign — epoch 1988 |
| GC-REF-005 (Sachin Tendulkar) | Moon | Check sign — epoch 1973 |

**Note:** These are directional indicators for manual spot-checking, NOT automated validation criteria. Actual expected values come from the reference run.

### 4.2 Boundary Positions Per Chart

| Chart | Expected Boundary Cases |
|-------|------------------------|
| GC-REF-001 (1926) | Verify Mercury near Sun longitude; Moon phase |
| GC-REF-002 (1961) | Verify Sun in late Leo or early Virgo; Saturn position |
| GC-REF-003 (1950) | Verify outer planets (Jupiter, Saturn) in specific signs |
| GC-REF-004 (1988) | Verify Uranus, Neptune, Pluto positions (epoch close to present) |
| GC-REF-005 (1973) | Verify Jupiter, Saturn positions |

---

## 5. Pass/Fail Criteria

### 5.1 Per-Configuration Pass/Fail

A single configuration (1 chart × 1 ayanamsa × 1 house system × 1 ephemeris mode) PASSES if:

- ALL HARD checks pass for all 9 grahas (63 checks)
- ≥ 95% of SOFT checks pass for all 9 grahas
- No content hash mismatch

### 5.2 Per-Benchmark-Family Pass/Fail

BM-CALC family PASSES if:

- ALL 14 test cases (BM-CALC-001 through BM-CALC-014) pass
- At least 1 chart tested across all 6 ayanamsa systems
- At least 1 chart tested across both ephemeris modes
- Determinism confirmed (consecutive runs identical)

### 5.3 Failure Escalation

| Failure Level | Action |
|---------------|--------|
| Single SOFT check fails | LOG — not blocking |
| > 5% SOFT checks fail | WARN — investigate drift |
| Single HARD check fails | FAIL — block release |
| Content hash mismatch | FAIL — investigate non-determinism |
| Missing graha | FAIL — critical calculation bug |
| Non-deterministic output | FAIL — block benchmark promotion |

---

## 6. Validation Execution

### 6.1 Automated Execution

```yaml
frequency:
  per_commit: BM-CALC-001 through BM-CALC-005 (Lahiri, Whole Sign, official)
  nightly: Full matrix (all 14 test cases)
  pre_release: Full matrix × all configs

tooling:
  comparator: Structured JSON diff with tolerance-aware comparison
  reporter: JUnit XML or JSON Lines report
  archiver: Results stored in benchmarks/results/ with content hash
```

### 6.2 Manual Execution (Cross-Check)

Quarterly: Manual cross-check of 1 chart × Lahiri × Whole Sign against JPL Horizons.
Procedure:
1. Extract birth data from GC-REF-002 (Obama, Tier A)
2. Query JPL Horizions for planetary positions at that epoch
3. Convert J2000 equatorial → sidereal ecliptic coordinates
4. Compare sidereal longitudes
5. Document any systematic offset

---

## 7. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief QA & Benchmark Architect (Agent 4) | Initial validation matrix |

---

*End of BM-CALC Validation Matrix. This matrix covers 90 validation checks × 120 configurations = 10,800 total validation points for the planet position calculation benchmark family.*
