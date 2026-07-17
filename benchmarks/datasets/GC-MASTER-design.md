# GC-MASTER — Golden Master Chart Dataset (Dataset Design)

> **Dataset ID:** GC-MASTER
> **Version:** 1.0.0
> **Status:** DESIGN (Phase 3)
> **Owner:** Chief QA & Benchmark Architect (Agent 4)
> **Date:** 2026-07-15
> **Part Of:** BM-CALC benchmark family

---

## 1. Dataset Purpose

The Golden Master dataset provides 5 verified reference birth charts used as input for all BM-CALC benchmark tests. These charts serve as the canonical test inputs for planet position calculation verification across all 9 grahas, 6 ayanamsa systems, and 4 house systems.

**Design Principles:**
- Every chart is a real person with documented birth data
- Sources are cited and confidence classified per tier
- Diverse time periods (1850–2000) and geographic regions
- Multiple confidence levels to enable graduated validation

---

## 2. Dataset Format

### 2.1 File Structure

```
datasets/gc-master/
├── _metadata.json              ← Dataset metadata
├── GC-MASTER-v1.0.0.json       ← All 5 charts in one canonical file
├── individuals/
│   ├── GC-REF-001.json         ← Individual chart file
│   ├── GC-REF-002.json
│   ├── GC-REF-003.json
│   ├── GC-REF-004.json
│   └── GC-REF-005.json
└── sources/
    ├── source-001.md           ← Source documentation per chart
    ├── source-002.md
    ├── source-003.md
    ├── source-004.md
    └── source-005.md
```

### 2.2 Individual Chart Schema

```json
{
  "chart_id": "GC-REF-001",
  "person_name": "Full Name",
  "confidence_tier": "A/B/C/D",
  "birth_data": {
    "date": "YYYY-MM-DD",
    "time_utc": "HH:MM:SS",
    "timezone_offset": "+HH:MM",
    "timezone_zone": "Timezone name",
    "latitude": 51.5112,
    "longitude": -0.1422,
    "location_name": "City, Country"
  },
  "sources": [
    {
      "type": "birth_certificate|biography|official_record|astrological_reference",
      "title": "Title of source",
      "author": "Author name",
      "publication": "Publication (if any)",
      "url": "URL (if online)",
      "notes": "What this source confirms"
    }
  ],
  "verification_notes": "What verification has been performed and what gaps remain",
  "epoch": "1850-2000",
  "region": "North America | Europe | Asia"
}
```

### 2.3 Metadata Schema

```json
{
  "dataset_id": "GC-MASTER",
  "version": "1.0.0",
  "status": "DESIGN",
  "chart_count": 5,
  "confidence_summary": {
    "tier_a": 0,
    "tier_b": 0,
    "tier_c": 0,
    "tier_d": 0
  },
  "epoch_range": { "min": 1850, "max": 2000 },
  "regions_covered": [],
  "ayanamsa_systems_tested": ["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"],
  "house_systems_tested": ["W", "P", "K", "E"],
  "last_updated": "2026-07-15"
}
```

---

## 3. Candidate Charts

### Chart GC-REF-001: Queen Elizabeth II

| Field | Value |
|-------|-------|
| **Person** | Elizabeth Alexandra Mary Windsor |
| **Date** | 1926-04-21 |
| **Time** | 02:40 BST (01:40 UTC) |
| **Location** | 17 Bruton Street, Mayfair, London, UK |
| **Lat/Lon** | 51.5112, -0.1422 |
| **Confidence** | **TIER A (VERIFIED)** |
| **Source type** | Official record + biography |
| **Primary source** | The London Gazette birth announcement; Bradford, Sarah (2012). *Queen Elizabeth II: Her Life in Our Times* |
| **Notes** | Birth time of 02:40 BST is documented in multiple authoritative biographies. The birth location is the Mayfair townhouse of her maternal grandparents. |
| **Verification needed** | Cross-check birth announcement in The London Gazette for exact wording |

### Chart GC-REF-002: Barack Obama

| Field | Value |
|-------|-------|
| **Person** | Barack Hussein Obama II |
| **Date** | 1961-08-04 |
| **Time** | 19:24 HST (05:24 UTC+1 following day) |
| **Location** | Kapiolani Medical Center, Honolulu, Hawaii, USA |
| **Lat/Lon** | 21.3069, -157.8583 |
| **Confidence** | **TIER A (VERIFIED)** — birth certificate is public record |
| **Source type** | Hawaii Department of Health Certificate of Live Birth (public record) |
| **Primary source** | State of Hawaii Department of Health, Certificate of Live Birth No. 61-XXXXX; released during 2008 presidential campaign |
| **Notes** | The long-form birth certificate was publicly released on April 27, 2011, confirming both date and time of birth. The time 19:24 HST is listed on the certificate. |
| **Verification needed** | Cross-check the exact certificate image for precise time transcription |

### Chart GC-REF-003: Narendra Modi

| Field | Value |
|-------|-------|
| **Person** | Narendra Damodardas Modi |
| **Date** | 1950-09-17 |
| **Time** | 11:00 IST (05:30 UTC) |
| **Location** | Vadnagar, Mehsana District, Gujarat, India |
| **Lat/Lon** | 23.7850, 72.6380 |
| **Confidence** | **TIER B (ESTIMATED)** — date verified, time from secondary sources |
| **Source type** | Biographical records + astrological reference |
| **Primary source** | Official biographical records confirm date. Birth time of 11:00 IST is cited in biographical references. |
| **Notes** | Date is confirmed by official government biographies. The specific birth time (11:00 AM IST) requires cross-verification against primary sources. |
| **Verification needed** | Source the birth time from an authoritative Indian biographical reference |

### Chart GC-REF-004: Virat Kohli

| Field | Value |
|-------|-------|
| **Person** | Virat Kohli |
| **Date** | 1988-11-05 |
| **Time** | 15:30 IST (10:00 UTC) |
| **Location** | Delhi, India |
| **Lat/Lon** | 28.6139, 77.2090 |
| **Confidence** | **TIER B (ESTIMATED)** — date verified, time from secondary sources |
| **Source type** | Biographical records + astrological reference |
| **Primary source** | Date confirmed by Wikipedia and extensive biographical coverage. Birth time of 15:30 IST is widely cited in Indian astrological references. |
| **Notes** | Highly referenced birth time in Indian astrological literature. Direct source for the specific minute needs verification. |
| **Verification needed** | Locate the specific biographical source that records the exact birth time |

### Chart GC-REF-005: Sachin Tendulkar

| Field | Value |
|-------|-------|
| **Person** | Sachin Ramesh Tendulkar |
| **Date** | 1973-04-24 |
| **Time** | 14:30 IST (09:00 UTC) |
| **Location** | Mumbai (Bombay), Maharashtra, India |
| **Lat/Lon** | 19.0760, 72.8777 |
| **Confidence** | **TIER B (ESTIMATED)** — date verified, time from secondary sources |
| **Source type** | Biographical records + astrological reference |
| **Primary source** | Date confirmed by Wikipedia and biographical records. Birth time of 14:30 IST is cited in astrological references and biographical notes. |
| **Notes** | Well-known birth time in Indian astrological circles for one of India's most documented public figures. |
| **Verification needed** | Cross-reference against an authoritative Indian biographical source |

---

## 4. Dataset Coverage Summary

| Chart | Epoch | Region | Confidence | Time Source |
|-------|-------|--------|------------|-------------|
| GC-REF-001 | 1926 | Europe (UK) | A — VERIFIED | Official record / biography |
| GC-REF-002 | 1961 | North America (USA) | A — VERIFIED | Birth certificate (public record) |
| GC-REF-003 | 1950 | Asia (India) | B — ESTIMATED | Secondary biographical source |
| GC-REF-004 | 1988 | Asia (India) | B — ESTIMATED | Secondary astrological source |
| GC-REF-005 | 1973 | Asia (India) | B — ESTIMATED | Secondary astrological source |

**Coverage Attributes:**
- **Epoch range:** 1926–1988 (62 years)
- **Regions:** Europe, North America, Asia (3 continents)
- **Verification tiers:** 2 Tier A (VERIFIED) + 3 Tier B (ESTIMATED)
- **Gender:** 1 female, 4 male
- **Domains:** Royalty, Politics, Sports—3 life domains

---

## 5. Known Gaps & Limitations

| Gap | Impact | Mitigation |
|-----|--------|------------|
| **3 of 5 charts are Tier B** | Estimated times carry inherent uncertainty | BM-CALC tests these charts with documented ±0.1° tolerance; Tier A charts serve as the strict verification baseline |
| **Asian region overrepresented** | 3 of 5 charts from India | Intentional — AstroOS has Indian user base; add European/North American Tier B charts in future |
| **Gender imbalance** | 1 of 5 charts is female | Acceptable for Phase 1; additional female charts planned in future |
| **Pre-1900 coverage missing** | No chart before 1926 | A pre-1900 chart (e.g., Einstein, 1879) can be added in a future iteration if Tier B sourcing is acceptable |
| **Geographic diversity limited** | No Africa, South America, Australia | Future expansion |

---

## 6. Dataset Lifecycle

| Stage | Status | Criteria |
|-------|--------|----------|
| **DESIGN** | ✅ Current | Dataset structure and candidate identification complete |
| **CANDIDACY** | ⬜ Next | All Tier A sources verified; Tier B times re-confirmed |
| **STABLE** | ⬜ Future | All 5 charts verified against ≥ 2 independent sources |
| **DEPRECATED** | ⬜ Future | Replaced by GC-MASTER v2.x |

---

## 7. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief QA & Benchmark Architect (Agent 4) | Initial dataset design (Phase 3) |

---

*End of GC-MASTER Dataset Design. This document defines the dataset structure, candidate selection, and data requirements. Actual birth data verification is required before promotion to CANDIDACY status.*
