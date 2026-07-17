# BM-HOUSE — House Calculation Test Datasets

> **Part Of:** BM-HOUSE Benchmark Family
> **Version:** 1.0.0
> **Status:** DRAFT (Phase 3)
> **Date:** 2026-07-15

---

## 1. Dataset Overview

BM-HOUSE uses two data sources:
- **Primary:** GC-MASTER (5 reference charts) — identical to BM-CALC
- **Additional:** Latitude Sweep Dataset — synthetic latitude values for house system behavior testing

No new birth data is fabricated. Latitude sweep uses existing GC-MASTER birth times with varied latitudes.

---

## 2. Primary Data (GC-MASTER)

Uses all 5 GC-REF charts from [GC-MASTER-design.md](../datasets/GC-MASTER-design.md) with all 4 house systems and Lahiri ayanamsa.

---

## 3. Latitude Sweep Dataset

### 3.1 Purpose

Test house system behavior across Earth's latitude range. Whole Sign (W) and Equal (E) should be latitude-independent; Placidus (P) and Koch (K) should vary.

### 3.2 Design

| Sweep ID | Base Chart | Latitudes Tested | Purpose |
|----------|-----------|------------------|---------|
| LAT-001 | GC-REF-001 (London, 51.5°N) | 0°, 23.4°N, 51.5°N, 66.5°N, -33.9°S | Moderate latitude range covering major zones |
| LAT-002 | GC-REF-002 (Honolulu, 21.3°N) | 0°, 21.3°N, 45°N, 60°N | Mid-latitude variation |

Both sweeps use the chart's original birth datetime and longitude; only latitude varies.

### 3.3 Latitude Values

| Label | Value | Zone | Example Location |
|-------|-------|------|-----------------|
| EQUATOR | 0° | Equatorial | Quito, Ecuador |
| TROPIC | 23.44°N | Subtropical | Tropic of Cancer |
| MID | 45°N | Temperate | Bordeaux, France |
| HIGH | 60°N | Subarctic | Oslo, Norway |
| ARCTIC | 66.5°N | Arctic Circle | Theoretical boundary |

### 3.4 Stability Check

| System | Expected Behavior | Fail Condition |
|--------|------------------|----------------|
| W | All cusps identical across all latitudes | Any cusp differs by > 0.001° |
| E | All cusps identical across all latitudes (ascendant affected only) | Any cusp differs by > 0.001° |
| P | Cusps vary with latitude | Cusps identical (indicates bug) |
| K | Cusps vary with latitude | Cusps identical (indicates bug) |

---

## 4. Configuration Matrix

### 4.1 Standard Matrix (16 configs per chart)

Each of the 5 GC-MASTER charts is tested with:
- 4 house systems (W, P, K, E)
- 1 ayanamsa (Lahiri, primary)
- 1 ephemeris mode (official)

= 5 × 4 = 20 standard test configurations.

### 4.2 Latitude Matrix

Chart LAT-001 × 5 latitude values × 4 house systems = 20 configurations
Chart LAT-002 × 5 latitude values × 4 house systems = 20 configurations

### 4.3 Total Configurations

| Source | Configurations | Test Cases |
|--------|---------------|------------|
| GC-MASTER (5 charts × 4 systems) | 20 | BM-HOUSE-001 through -012 |
| Latitude Sweep Classifications | 40 | BM-HOUSE-013, -014 |
| Ayanamsa Cross-check | 1 | BM-HOUSE-015 |
| Cross-chart consistency | 5 | BM-HOUSE-016 |
| **Total** | **66** | **16 test cases** |

---

## 5. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief QA & Benchmark Architect (Agent 4) | Initial dataset design |

---

*End of BM-HOUSE Dataset Design.*
