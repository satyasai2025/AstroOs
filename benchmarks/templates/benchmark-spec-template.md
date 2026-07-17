# Benchmark Specification Template

> **Template Version:** 1.0
> **Purpose:** Standardized format for all AstroOS benchmark specifications

---

## 1. Benchmark Identification

| Field | Value |
|-------|-------|
| **Benchmark ID** | `BM-{CATEGORY}-{NNN}` |
| **Family** | BM-{CATEGORY} |
| **Version** | x.y.z |
| **Status** | DRAFT / APPROVED / FROZEN / SUPERSEDED |

---

## 2. Purpose & Scope

**Purpose:**
One paragraph describing what this benchmark validates and why it matters.

**Category:**
(Calculation Accuracy / Detection Accuracy / Rule Evaluation / API Correctness / Performance / Regression / Edge Case)

**Difficulty:**
(FOUNDATION / INTERMEDIATE / ADVANCED / RESEARCH)

**Related Benchmarks:**
- Links to dependent or related benchmarks

---

## 3. Input Data

### 3.1 Required Inputs

| Input | Type | Description | Source |
|-------|------|-------------|--------|
| `birth_datetime_utc` | ISO 8601 timestamp | UTC birth datetime | Birth record |
| `latitude` | float (decimal degrees) | Geographic latitude WGS84 | Birth location |
| `longitude` | float (decimal degrees) | Geographic longitude WGS84 | Birth location |
| `ayanamsa` | string | Ayanamsa system identifier | Config |
| `house_system` | string | House system identifier | Config |

### 3.2 Reference Charts

| Chart ID | Person | Birth Date (UTC) | Lat | Lon | Source | Tier |
|----------|--------|-------------------|-----|-----|--------|------|
| REF-XXX-001 | ... | ... | ... | ... | [source] | A/B/C |

### 3.3 Reference Values

Reference values are computed from:

- **Primary:** Swiss Ephemeris (official .se1 files) — the production engine itself
- **Secondary:** JPL Horizons API — independent NASA ephemeris
- **Cross-check:** Position disagreement between primary and secondary → flagged, not averaged

---

## 4. Expected Outputs

### 4.1 Per-Planet Fields

| Field | Type | Tolerance | Description |
|-------|------|-----------|-------------|
| `planet` | enum | — | Graha name (Sun/Moon/.../Ketu) |
| `sidereal_longitude` | float (deg) | ±0.1° | Sidereal longitude in degrees |
| `latitude_deg` | float (deg) | ±0.1° | Celestial latitude |
| `speed_deg_per_day` | float | ±0.01°/day | Daily motion rate |
| `declination_deg` | float (deg) | ±0.1° | Equatorial declination |
| `rashi` | string | — | Zodiac sign (Aries–Pisces) |
| `rashi_degree` | float (deg) | ±0.1° | Degree within sign |
| `nakshatra` | string | — | Lunar mansion (27) |
| `nakshatra_pada` | int (1–4) | — | Pada within nakshatra |
| `is_retrograde` | bool | — | Retrograde flag |
| `is_combust` | bool | — | Combustion flag |

### 4.2 Per-Chart Fields

| Field | Type | Tolerance | Description |
|-------|------|-----------|-------------|
| `ayanamsa_value` | float (deg) | ±0.01° | Ayanamsa used |
| `lagna_rashi` | string | — | Ascendant sign |
| `lagna_degree` | float (deg) | ±0.1° | Ascendant degree |

### 4.3 Output Format

Deterministic JSON with content hash. Every chart × ayanamsa configuration produces exactly one output file.

---

## 5. Acceptance Criteria

| # | Criterion | Condition | Hard/Soft |
|---|-----------|-----------|-----------|
| 1 | Planet positions | All 9 grahas within tolerance | HARD |
| 2 | Ayanamsa value | Within 0.01° of Swiss Ephemeris value | HARD |
| 3 | Lagna position | Within 0.1° of reference | HARD |
| 4 | Retrograde flag | Matches reference exactly | HARD |
| 5 | Combustion flag | Matches reference exactly | HARD |
| 6 | Rashi assignment | Matches reference exactly | HARD |
| 7 | Nakshatra assignment | Matches reference exactly | HARD |

**HARD** = Must pass 100% for benchmark approval. Any failure blocks release.
**SOFT** = Must pass ≥ 95%, reported but not blocking.

---

## 6. Validation Method

### 6.1 Automated Validation

| Check | Tool/Method | When |
|-------|------------|------|
| Position within tolerance | Comparison script | Each benchmark run |
| Content hash match | SHA-256 | Each benchmark run |
| Schema conformance | JSON Schema validation | Each benchmark run |

### 6.2 Manual Validation

| Check | Method | Frequency |
|-------|--------|-----------|
| Reference chart sourcing audit | Source document review | Per chart addition |
| Tolerance boundary review | Spot-check near-boundary values | Per benchmark version |

---

## 7. Confidence Classification

Every expected result carries a confidence designation:

| Tier | Label | Meaning |
|------|-------|---------|
| **A** | VERIFIED | Confirmed against ≥ 2 independent reference sources |
| **B** | ESTIMATED | Consistent with known data but not independently verified |
| **C** | SYNTHETIC | Machine-generated (random, Monte Carlo) |
| **D** | UNKNOWN | Source cannot be verified |

---

## 8. Evidence & References

| Reference | Type | Location |
|-----------|------|----------|
| Source documents | Birth records | `datasets/ref-xxx/sources/` |
| Calculation references | Ephemeris docs | Swiss Ephemeris documentation |
| Validation scripts | Code | `scripts/validate/` |

---

## 9. Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| ... | ... | ... |

---

## 10. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | YYYY-MM-DD | Chief QA & Benchmark Architect | Initial specification |

---

*End of template. Every benchmark specification must include all sections above.*
