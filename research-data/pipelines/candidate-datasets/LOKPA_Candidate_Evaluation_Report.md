# Candidate Dataset Evaluation Report

## LOKPA_Persons_WithEvents.csv

> **Evaluator:** Chief Dataset & Research Curator
> **Date:** 2026-07-15
> **Status:** COMPLETE — Pending governance approval
> **Recommendation:** **Reject**

---

## 1. Dataset Identification

| Field | Value |
|-------|-------|
| **Filename** | `LOKPA_Persons_WithEvents.csv` |
| **Location** | `C:\Users\rkmau\Downloads\LOKPA_Persons_WithEvents.csv` |
| **Format** | CSV (comma-delimited, no header quoting observed) |
| **Encoding** | Appears to be mixed (some UTF-8, some Windows-1252) |
| **File Size** | ~2.3 MB |
| **Record Count** | 28,246 rows (+ 1 header) |
| **Fields** | 14 columns |

---

## 2. Schema Analysis

### 2.1 Fields

| # | Field | Type | Completeness | Notes |
|---|-------|------|-------------|-------|
| 1 | DocID | Integer | 100% | Sequential document identifier |
| 2 | Last Name | String | 100% | Contains study IDs and coded identifiers |
| 3 | First Name | String | ~87% | 13% empty (3,716 of 28,246) |
| 4 | Day | Integer (1-31) | 100% | Day of birth |
| 5 | Month | String (3-letter) | 100% | Month abbreviation (Jan, Feb, etc.) |
| 6 | Year | Integer (4-digit) | 100% | Year of birth |
| 7 | Time | String (HH:MM) | 100% | Birth time — all records have time! |
| 8 | Place | String | ~99% | Birthplace location description |
| 9 | Country | String | 100% | Country name at time of birth |
| 10 | Lat | Decimal | 100% | WGS84 latitude |
| 11 | Lng | Decimal | 100% | WGS84 longitude |
| 12 | RR | String (1-2 chars) | 100% | **Rodden Rating** — accuracy classification |
| 13 | Gender | String (M/F) | 100% | Male/Female |
| 14 | Events | String | ~14.4% | Life events; **85.6% empty** |

### 2.2 Rodden Rating (RR) Distribution

| Rating | Meaning | Count | % |
|--------|---------|-------|---|
| AA | Accurate — birth certificate / official | **7,090** | 25.1% |
| A | Accurate — family record / equivalent | **1,903** | 6.7% |
| B | Biography — from biographical source | **16,723** | 59.2% |
| C | Caution — no time or unspecified | **1,303** | 4.6% |
| D | Dirty — speculative / incorrect | **9** | 0.03% |
| X | Rectified — astrological rectification | **1,218** | 4.3% |

---

## 3. Provenance Assessment

### 3.1 Source Identification

The dataset uses several signature elements that strongly indicate origin from **Astro-Databank** (a commercial astrology database maintained by Astrodienst):

- **Rodden Rating system (AA/A/B/C/D/X)**: This is the trademarked accuracy classification system developed by Lois Rodden and used exclusively by Astro-Databank.
- **DocID format**: Sequential numeric identifiers consistent with Astro-Databank's internal record numbering.
- **Coded "Last Name" values**: Entries such as "AIDS 11189" appear to be study/condition identifier codes, not actual surnames — consistent with how Astro-Databank categorizes non-celebrity records.
- **Event annotations**: Event strings such as "Alternative rectified time", "Event#780" match the format of Astro-Databank's event annotation system.

### 3.2 Provenance Verdict

| Dimension | Assessment |
|-----------|------------|
| **Origin** | Highly likely derived from Astro-Databank |
| **Collection Method** | Unknown — appears to be a partial/extracted export |
| **Source Documentation** | None provided |
| **Timestamp** | No extraction date or version recorded |
| **Attribution** | None — originator not credited |
| **Provenance Verdict** | **Unverifiable** — cannot confirm source or collection ethics |

---

## 4. Licensing Assessment

### 4.1 Known Licensing Context

Astro-Databank data is available under two primary mechanisms:
1. **Astro-Databank Wiki** (wiki.astro.com) — Creative Commons BY-SA for wiki contributions
2. **Astro-Databank professional data files** — Licensed/paid distribution; terms restrict redistribution

### 4.2 License Findings

| Concern | Detail |
|---------|--------|
| **No license file** | The CSV carries no license, README, or terms of use |
| **No attribution** | Astro-Databank requires attribution if data is derived from their wiki |
| **Commercial restrictions** | If from the professional database, redistribution is likely prohibited |
| **Unknown origin** | Cannot determine whether this is a wiki export (CC-BY-SA) or a licensed database dump (restricted) |

### 4.3 Licensing Verdict

| Dimension | Assessment |
|-----------|------------|
| **License Identified** | None |
| **SPDX Identifier** | None |
| **Redistribution Rights** | Unknown — likely restricted |
| **Commercial Use** | Unknown — likely prohibited |
| **Attribution Requirements** | Cannot determine — Astro-Databank attribution likely required |
| **Licensing Verdict** | **Unusable** — cannot determine legal status |

---

## 5. Data Quality Assessment

### 5.1 Completeness

| Metric | Value | Assessment |
|--------|-------|------------|
| Record completeness | 100% (28,246/28,246) | ✅ Excellent |
| Field completeness (core) | 100% (time, date, place for all) | ✅ Excellent |
| Field completeness (events) | 14.4% (4,070/28,246) | ❌ Poor |
| First Name completeness | 87% | ⚠️ Moderate |
| Coordinate completeness | 100% | ✅ Excellent |

### 5.2 Accuracy

| Element | Assessment | Detail |
|---------|------------|--------|
| Birth dates | ✅ Good | Well-formed dates; year range ~1800–2000 |
| Birth times | ✅ Excellent | All records have times — rare for any public dataset |
| RR = AA/A (accurate) | 31.8% | Verified/official source times |
| RR = B (biography) | 59.2% | Times from biography — moderate reliability |
| RR = C/D (caution) | 4.6% | Low reliability |
| RR = X (rectified) | 4.3% | Rectified — method reliability varies |
| **Time accuracy overall** | **~32% high-confidence** | ⚠️ Majority is biographical-grade |

### 5.3 Consistency

| Check | Result |
|-------|--------|
| Date parseability | ✅ All dates parseable |
| Coordinate ranges | ✅ All within valid ranges |
| Enum consistency (RR) | ✅ All known RR values |
| Enum consistency (Gender) | ✅ M/F only |
| Temporal ordering | ⚠️ Cannot verify — no chronological relationship between birth + events |
| Event format consistency | ❌ Highly inconsistent — some are structured, some cryptic ("Event#780") |

### 5.4 Example Records by Quality

**High quality (RR=AA/A with events):**
```
DocID: 4260, Born: 1949-03-08 18:05, Bronx NY, USA
Events: "Body changes (menopause, etc.)"
RR: A — good time, event present but subjective
```

**Low quality (RR=C/X, cryptic events):**
```
DocID: 465, Born: 1938-11-01 19:30, Chicago IL, USA
Events: "Alternative rectified time"
RR: A — time appears rectified, not original
```

**No events (85.6% of data):**
```
Most records — birth data present but no life events recorded
```

---

## 6. Research Suitability Assessment

### 6.1 Strengths

| Strength | Detail |
|----------|--------|
| Large sample | 28,246 records — statistically significant |
| Universal birth times | Every record has a birth time (rare in public datasets) |
| Geographic diversity | Multiple countries represented |
| Time span | Records span ~200 years of birth dates |
| Event annotations | ~4K records with life events |

### 6.2 Weaknesses

| Weakness | Impact |
|----------|--------|
| **85.6% lack events** | Majority of records cannot be used for event-based verification studies |
| **Event quality is poor** | Events are unstructured, cryptic, or subjective ("Body changes", "Great Publicity") |
| **RR=B majority (59.2%)** | Over half the data is biographical-grade accuracy — not verified |
| **Coded identifiers** | Many "Last Name" fields are study IDs, not verifiable identities |
| **No event dates** | Events have no associated dates — cannot be used for timing studies |
| **No death dates** | Cannot determine longevity or life span |
| **Unknown rectification methods** | RR=X records — no documentation of rectification methodology |

### 6.3 Suitability by AstroOS Engine

| Engine | Suitability | Rationale |
|--------|-------------|-----------|
| **Verification Engine** | ❌ Poor | Only 14.4% have events; events have no dates; event quality is poor |
| **Statistics Engine** | ⚠️ Moderate | Large sample, good birth data — useful for base rates, but no computed chart data included |
| **Research Engine** | ❌ Poor | Missing event dates, unknown provenance, privacy concerns |
| **AI Engine** | ❌ Poor | Cannot verify factual claims; unknown data quality |
| **Benchmark Suite** | ❌ Poor | No reference calculations; no expected outputs |

---

## 7. Privacy Implications

### 7.1 PII Assessment

| PII Type | Present | Detail |
|----------|---------|--------|
| Full name | Partial | Many records have coded IDs instead of names |
| Birth date | Yes | Full date of birth |
| Birth place | Yes | City, state/province, country |
| Coordinates | Yes | Geographic coordinates of birthplace |
| Life events | Yes | Health conditions, life milestones, sensitive events |
| Sensitive data | **Yes** | Contains: suicide attempts, sexual abuse, health conditions |

### 7.2 Privacy Verdict

| Dimension | Assessment |
|-----------|------------|
| **Contains PII** | Yes — birth date, place, some names, life events |
| **Contains sensitive PII** | Yes — health events, sexual content, personal milestones |
| **Anonymization** | None — raw data as collected |
| **Consent** | Unknown — no consent documentation |
| **Re-identification Risk** | Moderate — birth date + place + events can identify individuals |
| **Privacy Verdict** | **Unacceptable** without significant anonymization |

---

## 8. Legal & Ethical Considerations

### 8.1 Legal Concerns

| Concern | Severity | Detail |
|---------|----------|--------|
| Unknown license | Critical | No license terms attached |
| Possible Astro-Databank TOS violation | High | Appears to be derived from a commercial data source |
| Data subject rights (GDPR) | High | EU subjects have rights over their data; no consent documented |
| Redistribution restriction | High | Cannot legally redistribute without license clarity |

### 8.2 Ethical Concerns

| Concern | Severity | Detail |
|---------|----------|--------|
| Sensitive life events without consent | High | Health, sexual, and personal events of possibly living individuals |
| No consent documentation | Critical | No record of whether subjects consented to research use |
| Coded identifiers as pseudo-anonymization | Medium | Weak anonymization — birth dates + places can re-identify |
| Potentially living individuals | Medium | Some records may be for living persons (birth data post-1970) |
| No withdrawal mechanism | Critical | No way for subjects to request removal |

---

## 9. Confidence Summary

| Dimension | Score (0-10) | Assessment |
|-----------|--------------|------------|
| Provenance | 2/10 | Origin unverifiable; appears to be sourced from commercial database |
| Licensing | 1/10 | No license; likely restricted; cannot use |
| Data Quality | 5/10 | Good birth data but poor events |
| Completeness | 4/10 | Great for birth data; poor for events |
| Consistency | 6/10 | Birth data consistent; events inconsistent |
| Research Suitability | 3/10 | Only useful for base-rate studies; verification requires events with dates |
| Privacy | 2/10 | Contains PII and sensitive data without consent |
| Legal | 1/10 | Unknown license; potential TOS violation |
| Ethical | 2/10 | Sensitive data without consent or withdrawal mechanism |

**Overall Score:** **2.9/10**

---

## 10. Recommendation

### ❌ REJECT

**This dataset should not be ingested into the AstroOS Research Dataset Repository.**

### Rationale

1. **Unverifiable provenance**: Strongly appears to derive from Astro-Databank, a commercial database, but without attribution, license, or documentation. Cannot legally or ethically incorporate data of unknown origin.

2. **No license**: Without a license file or terms of use, the dataset cannot be distributed, modified, or used for research with legal certainty.

3. **Privacy violations**: Contains birth dates, places, and sensitive life events (health conditions, sexual events, suicide attempts) without any documented consent or anonymization.

4. **Poor research utility for AstroOS purposes**: 85.6% of records lack events. The 14.4% that have events lack **event dates** — making them unusable for the Verification Engine, Dasha timing studies, transit analysis, or any time-based research.

5. **Superior alternatives exist**: The user has confirmed they are creating their own datasets (PB-WIKI, PB-EVENTS) from properly licensed public sources with full provenance documentation.

### If Governance Overrules

If this dataset were to be considered for use despite the above, the following **minimum requirements** would apply:

- **Accept with Restrictions**: Research use only. Requires full anonymization (remove names, generalize dates). Requires legal review of Astro-Databank terms. Requires ethical review board approval. Publish only aggregated statistics, never individual records.

- **Conditions**: Must obtain documented license terms. Must implement k-anonymity (k≥5). Must exclude sensitive event categories. Must implement data subject withdrawal mechanism.

---

## Appendix: Quick Reference

| Attribute | Value |
|-----------|-------|
| **Candidate** | LOKPA_Persons_WithEvents.csv |
| **Evaluator** | Chief Dataset & Research Curator |
| **Date** | 2026-07-15 |
| **Recommendation** | Reject |
| **Fallback** | Accept with Restrictions (if governance overrules) |
| **Risk Level** | High |
| **Replaces** | N/A — first evaluation |
