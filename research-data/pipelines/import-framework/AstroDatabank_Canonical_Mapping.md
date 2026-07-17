# AstroDatabank Canonical Mapping Specification

> **Status:** ACTIVE — pending Engineering Office delivery (ER-001)
> **Owner:** Chief Dataset & Research Curator
> **Version:** 1.0
> **Date:** 2026-07-15

---

## 1. Source Schema (AstroDatabank.xlsx)

| # | Source Field | Type | Description | Example |
|---|-------------|------|-------------|---------|
| 1 | DocID | Integer | AstroDatabank record identifier | 4260 |
| 2 | Last Name | String | Surname or coded identifier | "Einstein" or "AIDS 11189" |
| 3 | First Name | String | Given name (may be empty) | "Albert" |
| 4 | Day | Integer (1-31) | Birth day | 14 |
| 5 | Month | String (3-letter) | Birth month abbreviation | "Mar" |
| 6 | Year | Integer (4-digit) | Birth year | 1879 |
| 7 | Time | String (HH:MM) | Birth time (24h format) | "18:05" |
| 8 | Place | String | Birth place description | "Ulm Germany" |
| 9 | Country | String | Country name | "Germany" |
| 10 | Lat | Decimal | WGS84 latitude | 48.4010 |
| 11 | Lng | Decimal | WGS84 longitude | 9.9876 |
| 12 | RR | String (1-2 chars) | Rodden Rating — birth time accuracy | "AA" |
| 13 | Gender | String (M/F) | Sex | "M" |
| 14 | Events | String | Life events (may contain multiple pipe-separated events) | "Great Publicity" |

---

## 2. Target Schema (AstroOS Record Envelope)

The target is the AstroOS record envelope as defined in Phase 4 (Record Standards). The mapping converts source fields into the canonical envelope structure.

### 2.1 Envelope Mapping

| Source Field | Envelope Path | Transformation | Notes |
|-------------|---------------|----------------|-------|
| DocID | `_record_id` | `ASTRO-REC-AD-{DocID}` | Prefix with AstroDatabank source code |
| — | `_dataset_id` | `ASTRO-RS-EVENT-v1.0.0` | Target dataset |
| — | `_record_type` | `chart` | Birth chart record |
| — | `_version` | `1` | First version |
| — | `_is_deleted` | `false` | Never deleted on import |
| Last Name + First Name | `_person.person_name_display` | Concatenate (or coded ID if First Name empty) | Handle "AIDS 11189" as identifier, not name |
| Last Name + First Name | `_person.is_public_figure` | `false` (default) | Not verified as public figure on import |
| — | `_person.gender` | Map M→male, F→female | Standardize |
| Day + Month + Year | `_birth.birth_date` | Construct ISO 8601: `YYYY-MM-DD` | Month abbreviation→number: Jan→01, etc. |
| — | `_birth.birth_date_accuracy` | `exact` | Day/month/year all present |
| Time | `_birth.birth_time` | Parse HH:MM → `HH:MM:SS` | Append :00 seconds |
| — | `_birth.birth_time_accuracy` | Derived from RR (see §3) | Map RR to accuracy tier |
| — | `_birth.birth_time_source` | `astrological_rectification` for RR=X, `unknown` for others | Source depends on RR |
| Place + Country | `_birth.birth_place` | Normalize: "City State, Country" | See normalization rules §4 |
| — | `_birth.birth_latitude` | Direct copy from Lat | Validate range [-90, 90] |
| — | `_birth.birth_longitude` | Direct copy from Lng | Validate range [-180, 180] |
| — | `_birth.timezone_offset_minutes` | Derive from longitude: `round(lng / 15) * 60` | Rough estimate; RF-TZ will refine |
| — | `_birth.country_code` | Map Country name → ISO 3166-1 alpha-2 | See mapping table §4 |
| — | `_source.primary_source.type` | `astro_databank` | New source type |
| — | `_source.primary_source.attribution` | "Astrodienst Astro-Databank" | Required attribution |
| — | `_source.verification_status` | Derived from RR (see §3) | Map RR to verification level |
| RR | `_confidence.overall_tier` | Derived from RR (see §3) | Map RR to confidence tier |
| — | `_confidence.field_confidence.birth_time.tier` | Derived from RR (see §3) | Per-field confidence |
| — | `_confidence.field_confidence.birth_time.rationale` | "Rodden Rating {RR}" | Source of confidence |
| — | `_privacy.record_privacy_tier` | `public` (all records) | Notable individuals from public database |
| — | `_privacy.contains_pii` | `false` | Public figures only |

### 2.2 Events Mapping

Events are stored in the `Events` field as pipe-separated strings. Each event becomes a separate event record linked to the chart record.

| Source Field | Target | Transformation |
|-------------|--------|----------------|
| Events (pipe-separated) | Multiple RS-EVENT records | Split on `|` or `;` delimiter |
| DocID | `chart_record_id` | Reference to parent chart record |
| Events text | `title` | Cleaned event text |
| Events text | `event_category` | Classified by keyword matching (see §5) |
| — | `event_date` | **NOT AVAILABLE** — Events have no dates |
| — | `event_date_accuracy` | `unknown` | No event dates in source |
| — | `event_type` | Inferred from category (see §5) |
| — | `source_type` | `astro_databank` | |
| — | `verification_status` | `single_source` | Only one source per event |

---

## 3. Rodden Rating (RR) Mapping

The Rodden Rating system classifies birth time accuracy. The mapping to AstroOS confidence and accuracy tiers:

| RR | Meaning | `_birth.birth_time_accuracy` | `_confidence.overall_tier` | `_source.verification_status` |
|----|---------|----------------------------|---------------------------|------------------------------|
| AA | Accurate — from birth record | `exact` | `verified` | `verified_single_source` |
| A | Accurate — from family record | `exact` | `verified` | `verified_single_source` |
| B | Biography — from published bio | `estimated_window_lt_1h` | `estimated_close` | `single_source` |
| C | Caution — no time or unreliable | `unknown` | `unknown` | `unverified` |
| D | Dirty — speculative | `unknown` | `unknown` | `unverified` |
| X | Rectified — astrological rectification | `rectified` | `rectified` | `rectified` |

**Confidence score mapping:**

| RR | Confidence Score |
|----|-----------------|
| AA | 0.95 |
| A | 0.90 |
| B | 0.60 |
| C | 0.10 |
| D | 0.05 |
| X | 0.50 |

---

## 4. Normalization Rules

### 4.1 Date Normalization

```
Input:  Day="14", Month="Mar", Year="1879"
Output: "1879-03-14"

Rules:
- Month mapping: Jan→01, Feb→02, Mar→03, Apr→04, May→05, Jun→06,
                 Jul→07, Aug→08, Sep→09, Oct→10, Nov→11, Dec→12
- Day zero-padding: always 2 digits
- Year: 4 digits; reject years < 1500 or > current_year
```

### 4.2 Time Normalization

```
Input:  Time="18:05"
Output: "18:05:00"

Rules:
- Append ":00" seconds
- Validate format HH:MM after parsing
- Hours: 0-23; Minutes: 0-59
- Reject invalid times (e.g., "25:00")
```

### 4.3 Place Name Normalization

```
Input:  Place="Ulm Germany", Country="Germany"
Output: birth_place="Ulm, Germany"

Rules:
- Remove leading/trailing whitespace
- Normalize multiple spaces to single space
- If Country is not already in Place, append ", {Country}"
- Title case for place names (preserve proper nouns)
- Remove special characters except hyphens and apostrophes
```

### 4.4 Country Name → ISO Code Mapping

| Country Name | ISO 3166-1 Alpha-2 |
|-------------|-------------------|
| USA | US |
| United States | US |
| United Kingdom | GB |
| England | GB |
| Scotland | GB |
| Wales | GB |
| France | FR |
| Germany | DE |
| Italy | IT |
| Spain | ES |
| Poland | PL |
| Russia | RU |
| China | CN |
| Japan | JP |
| India | IN |
| Brazil | BR |
| Australia | AU |
| Canada | CA |
| Mexico | MX |
| South Africa | ZA |
| Nigeria | NG |
| *Others* | Lookup from ISO 3166-1 database |

### 4.5 Gender Normalization

```
Input:  Gender="M" or Gender="F"
Output: gender="male" or gender="female"

Rules:
- M → male
- F → female
- Empty/unknown → null
- Reject values other than M/F
```

### 4.6 Coordinate Validation

```
Latitude:  -90.0 ≤ value ≤ 90.0
Longitude: -180.0 ≤ value ≤ 180.0

Rules:
- Reject out-of-range values
- Flag zero coordinates (0.0, 0.0) as suspicious
- Round to 4 decimal places
```

### 4.7 Name Normalization

```
Rules:
- Trim whitespace
- Title case (preserve proper nouns)
- If First Name is empty: use Last Name as display name
- If Last Name contains "AIDS" or similar study codes: flag as coded identifier, not real name
- Maximum 200 characters
```

---

## 5. Event Category Classification

Events are classified by keyword matching against the Verification Engine's known event categories:

| Category | Keywords (case-insensitive) |
|----------|---------------------------|
| marriage | marriage, married, wedding, engaged, divorce, divorced, spouse |
| career | career, job, work, promotion, fired, hired, business, company, founded, profession |
| education | school, university, college, degree, graduation, PhD, diploma |
| health | health, disease, illness, cancer, hospital, surgery, injury, sick, diagnosis, death, died |
| progeny | birth, child, children, baby, pregnancy, adopted |
| wealth | money, wealth, inheritance, lottery, fortune, financial, rich, poor, bankruptcy |
| longevity | death, died, age, lifespan, longevity |
| other | *(everything not matching above)* |

**Classification rules:**
1. Check each event text against keyword list
2. First matching category wins
3. If no match: classify as `other`
4. Record the original event text in `description` field
5. Create a short title from the event text (first 100 chars)

---

## 6. Import Validation Rules

### 6.1 Critical Rules (Blocking Import)

| Rule ID | Rule | Severity |
|---------|------|----------|
| VAL-001 | Birth date parseable as YYYY-MM-DD | CRITICAL |
| VAL-002 | Birth time parseable as HH:MM | CRITICAL |
| VAL-003 | Latitude in range [-90, 90] | CRITICAL |
| VAL-004 | Longitude in range [-180, 180] | CRITICAL |
| VAL-005 | RR value in {AA, A, B, C, D, X} | CRITICAL |
| VAL-006 | Gender value in {M, F} or empty | CRITICAL |
| VAL-007 | DocID is unique within dataset | CRITICAL |

### 6.2 High Rules (Flag for Review)

| Rule ID | Rule | Severity |
|---------|------|----------|
| VAL-010 | Birth year ≥ 1500 | HIGH |
| VAL-011 | Birth year ≤ current year | HIGH |
| VAL-012 | Country name maps to valid ISO code | HIGH |
| VAL-013 | Coordinates are non-zero | HIGH |
| VAL-014 | Place name is non-empty | HIGH |
| VAL-015 | RR=X records have rectification note | HIGH |

### 6.3 Medium Rules (Quality Flags)

| Rule ID | Rule | Severity |
|---------|------|----------|
| VAL-020 | Birth time matches known patterns (not all 00:00) | MEDIUM |
| VAL-021 | Gender is balanced (flag extreme skew) | MEDIUM |
| VAL-022 | Geographic distribution is reasonable | MEDIUM |
| VAL-023 | Temporal distribution is reasonable | MEDIUM |
| VAL-024 | No duplicate birth date + place combinations | MEDIUM |

---

## 7. Quality Acceptance Criteria

### 7.1 Dataset-Level Quality Gates

| Metric | Minimum | Target | Measurement |
|--------|---------|--------|-------------|
| Record completeness | ≥95% | 100% | Records with all required fields |
| Birth date completeness | 100% | 100% | All records have valid date |
| Birth time completeness | 100% | 100% | All records have time (even if low quality) |
| Coordinate completeness | ≥95% | 100% | Records with valid lat/lng |
| RR completeness | 100% | 100% | All records have RR value |
| Country code mapping | ≥90% | 100% | Successfully mapped to ISO code |
| Duplicate rate | ≤5% | ≤1% | DocID duplicates |
| Birth time high-quality (AA/A) | ≥20% | ≥30% | Records with AA or A rating |

### 7.2 Record-Level Quality Score

Each imported record receives a quality score based on field completeness and RR rating:

```
record_quality_score = (
    0.30 × (has_birth_date ? 1.0 : 0.0) +
    0.25 × (has_birth_time ? rr_confidence_score : 0.0) +
    0.20 × (has_coordinates ? 1.0 : 0.0) +
    0.15 × (has_country_code ? 1.0 : 0.0) +
    0.10 × (has_place_name ? 1.0 : 0.0)
)
```

Where `rr_confidence_score` is:
- AA: 1.0
- A: 0.9
- B: 0.6
- C: 0.1
- D: 0.05
- X: 0.5

### 7.3 Dataset Quality Score

```
dataset_quality_score = mean(all record quality scores)
```

| Score Range | Tier | Gate |
|-------------|------|------|
| ≥0.90 | Research Grade (A) | Required for M4 |
| ≥0.75 | Production Grade (B) | Required for M3 |
| ≥0.50 | Exploratory Grade (C) | Acceptable for candidacy |
| <0.50 | Rejected | Must not publish |

---

## 8. Import Verification Checklist

### Pre-Import Verification

| Step | Check | Owner | Status |
|------|-------|-------|--------|
| 1 | Source file exists and is readable | Engineering | ⏳ |
| 2 | Source schema matches expected columns | Engineering | ⏳ |
| 3 | File encoding is UTF-8 | Engineering | ⏳ |
| 4 | No duplicate DocIDs in source | Engineering | ⏳ |
| 5 | Column headers match specification (§1) | Engineering | ⏳ |

### Import-Time Validation

| Step | Check | Owner | Status |
|------|-------|-------|--------|
| 6 | All records pass VAL-001 to VAL-007 | Validation script | ⏳ |
| 7 | All records pass VAL-010 to VAL-015 | Validation script | ⏳ |
| 8 | Country name mapping success rate ≥90% | Validation script | ⏳ |
| 9 | Event category classification成功率 ≥80% | Validation script | ⏳ |
| 10 | Duplicate detection run | Validation script | ⏳ |

### Post-Import Verification

| Step | Check | Owner | Status |
|------|-------|-------|--------|
| 11 | Record count matches expected | RDO | ⏳ |
| 12 | Dataset quality score ≥0.75 (Tier B) | RDO | ⏳ |
| 13 | Quality report generated | RDO | ⏳ |
| 14 | Bias assessment documented | RDO | ⏳ |
| 15 | Metadata file complete | RDO | ⏳ |
| 16 | Checksum computed | RDO | ⏳ |
| 17 | Changelog initialized | RDO | ⏳ |
| 18 | Catalog entry created | RDO | ⏳ |
| 19 | Promotion to Candidacy or Stable | RDO | ⏳ |

### Handoff to Engineering Office

| Item | Status |
|------|--------|
| Canonical mapping spec (this document) | ✅ Complete |
| Validation rules (§6) | ✅ Complete |
| Normalization rules (§4) | ✅ Complete |
| Quality acceptance criteria (§7) | ✅ Complete |
| Import verification checklist (§8) | ✅ Complete |
| Target dataset schema | ✅ Defined in Phase 4 |
| Target metadata schema | ✅ Defined in Phase 3 |

---

## 9. Expected Import Statistics (Based on LOKPA Analysis)

| Metric | LOKPA Observed | AstroDatabank Expected | Notes |
|--------|---------------|----------------------|-------|
| Total records | 28,246 | ~30,000-40,000 | AstroDatabank is larger |
| Birth time present | 100% | 100% | All records have time |
| RR=AA (high quality) | 25.1% | ~25-30% | Birth certificate verified |
| RR=A (good quality) | 6.7% | ~7-10% | Family record |
| RR=B (biography) | 59.2% | ~50-60% | From published biography |
| RR=C/D (low quality) | 4.6% | ~5% | Unreliable times |
| RR=X (rectified) | 4.3% | ~4-5% | Astrological rectification |
| Events present | 14.4% | ~15-20% | Life events field |
| Records with names | 87% | ~90%+ | Better quality expected |
| Records with coordinates | 100% | 100% | Standard in AstroDatabank |

---

## 10. Integration Protocol with Engineering Office

### When ER-001 is Delivered

1. **RDO receives import pipeline output** (CSV/Parquet of imported records)
2. **RDO runs L1 validation** — schema compliance check
3. **RDO runs L2 validation** — quality scoring and bias assessment
4. **RDO generates Import Validation Report** — pass/fail with detailed metrics
5. **If pass:** Dataset promoted to Candidacy, then Stable after L3 audit
6. **If fail:** Return to Engineering with specific defects to fix

### Import Validation Report Template

```markdown
# Import Validation Report

## Summary
- Dataset: ASTRO-RS-EVENT-v1.0.0
- Import date: YYYY-MM-DD
- Source: AstroDatabank.xlsx via ER-001 pipeline
- Result: PASS / FAIL

## Metrics
- Total records: N
- Passed validation: N (XX%)
- Failed validation: N (XX%)
- Quality score: X.XX (Tier X)

## Validation Results
| Rule | Passed | Failed | Rate |
|------|--------|--------|------|
| VAL-001 | N | N | XX% |
| ... | ... | ... | ... |

## Quality Breakdown
- Birth time AA/A rate: XX%
- Event coverage: XX%
- Geographic coverage: XX countries
- Temporal coverage: YYYY-YYYY

## Recommendations
1. ...
2. ...

## Sign-off
- Reviewed by: Chief Dataset & Research Curator
- Date: YYYY-MM-DD
- Decision: ACCEPT / ACCEPT WITH RESTRICTIONS / REJECT
```
