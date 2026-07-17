---
name: astrosos-dataset-quality
description: "Complete dataset quality standards — completeness, missing data, duplicates, consistency, bias assessment, ethical review"
metadata: 
  node_type: memory
  type: reference
  domain: datasets
  status: draft
  phase: 5
  originSessionId: e78a75e5-611c-4c3f-99a8-68817dfe9484
---

# AstroOS Dataset Quality Standards — Phase 5

> **Status:** DRAFT — pending approval
> **Owner:** Chief Dataset & Research Curator
> **Version:** 1.0
> **Date:** 2026-07-15

---

## Table of Contents

1. [Completeness Standards](#1-completeness-standards)
2. [Missing Field Handling](#2-missing-field-handling)
3. [Duplicate Detection & Resolution](#3-duplicate-detection--resolution)
4. [Consistency Framework](#4-consistency-framework)
5. [Bias Assessment Framework](#5-bias-assessment-framework)
6. [Ethical Review Process](#6-ethical-review-process)
7. [Dataset-Specific Quality Specifications](#7-dataset-specific-quality-specifications)

---

## 1. Completeness Standards

### 1.1 Completeness Dimensions

Completeness is measured across four dimensions:

| Dimension | Definition | Measurement |
|-----------|------------|-------------|
| **Record Completeness** | What fraction of expected records are present? | `actual_records / expected_records` |
| **Field Completeness** | What fraction of fields are populated (non-null)? | `populated_fields / total_fields` |
| **Required Field Completeness** | What fraction of required fields are populated? | `populated_required_fields / total_required_fields` |
| **Coverage Completeness** | What fraction of the intended scope is covered? | `covered_scope_units / target_scope_units` |

### 1.2 Expected Records Determination

For each dataset type, the expected record count is determined differently:

| Dataset Type | Expected Records Determination |
|-------------|-------------------------------|
| **RF-SIGNS** | Fixed: exactly 12 (all zodiac signs) |
| **RF-NAK** | Fixed: exactly 27 (all nakshatras) |
| **RF-PADA** | Fixed: exactly 108 (all padas) |
| **RF-PLANET** | Fixed: exactly 9 (all grahas) |
| **RF-HOUSE** | Fixed: exactly 12 (all bhavas) |
| **RF-DASHA** | Fixed: per dasha system (e.g., Vimshottari = 9 lords) |
| **RF-AYAN** | Fixed: exactly 6 (supported ayanamsa systems) |
| **RF-KARAKA** | Variable: number of known karakatva subjects |
| **RF-TZ** | Defined by IANA tzdata release (deterministic set) |
| **RS-COHORT** | Defined by filter criteria at cohort creation time |
| **RS-EVENT** | Variable: number of identified/collected events |
| **RS-MARRIAGE** | Variable: number of identified/collected marriages |
| **RS-CAREER** | Variable: number of identified/collected careers |
| **RS-HEALTH** | Variable: number of identified/collected health events |
| **RS-WEALTH** | Variable: number of identified/collected wealth events |
| **RS-SPIRITUAL** | Variable: number of identified/collected spiritual events |
| **RS-FLAT** | Same as source chart count |
| **BM-*** | Defined by benchmark specification (intentional count) |
| **VL-*** | Defined by validation specification |
| **QT-*** | Defined by test specification |
| **AI-*** | Defined by evaluation specification |
| **SY-*** | Defined by generation parameters |
| **PB-WIKI** | Variable: number of Wikipedia articles meeting criteria |
| **PB-WIKIDATA** | Variable: number of Wikidata items meeting query criteria |
| **PB-EVENTS** | Variable: number of events collected from public sources |
| **PB-TWIN** | Variable: number of twin pairs identified |
| **LC-*** | Per agreement with data provider |
| **UC-*** | Variable: number of user submissions meeting criteria |

### 1.3 Completeness Thresholds by Dataset Tier

| Dataset Tier | Min Record Completeness | Min Field Completeness | Min Required Field Completeness |
|-------------|------------------------|----------------------|-------------------------------|
| Research Grade (A) | 100% | 95% | 100% |
| Production Grade (B) | ≥95% | 90% | 100% |
| Exploratory Grade (C) | ≥80% | 75% | 95% |
| Draft Grade (D) | ≥50% | 50% | 80% |
| Rejected (F) | <50% | <50% | <80% |

### 1.4 Fixed-Reference Datasets: Zero-Tolerance Rule

For datasets with a fixed, known set of expected records (RF-SIGNS, RF-NAK, RF-PADA, RF-PLANET, RF-HOUSE, RF-DASHA, RF-AYAN), **record completeness MUST be exactly 100%** before the dataset can leave Draft stage. Any missing record is a blocking defect.

---

## 2. Missing Field Handling

### 2.1 Null Value Classification

Every null value in a dataset is classified into one of these categories:

| Code | Category | Meaning | Example |
|------|----------|---------|---------|
| `NA` | Not Applicable | Field has no meaningful value for this record | `death_date` for a living person |
| `NP` | Not Yet Populated | Field has known value but not yet entered | `deity` field for a nakshatra awaiting textual verification |
| `NU` | Not Known | Value genuinely unknown and may never be known | `birth_time` for a historical figure with no record |
| `NE` | Not Expected | Field expected to be null for this record type | `spouse_name` for an unmarried person |
| `NI` | Not Included | Field intentionally excluded from this dataset version | Optional field not collected in v1.0, planned for v1.1 |
| `ND` | Not Determinable | Value could theoretically exist but cannot be determined | `exact_birth_time` for someone born before formal birth records |

### 2.2 Null Representation by Format

| Format | NA / NP / NU / NE / NI / ND |
|--------|------------------------------|
| CSV | Empty string for strings; `null` for numeric/dates |
| JSON | `null` |
| JSONL | `null` |
| Parquet | `null` (physical) |
| SQL | `NULL` |

### 2.3 Null Metadata

Every dataset must document its nulls in the quality report:

```json
{
  "null_analysis": {
    "total_null_cells": 142,
    "null_pct": 3.2,
    "per_field_nulls": {
      "birth_time": {
        "null_count": 85,
        "null_pct": 14.2,
        "classification": "NU",
        "rationale": "Birth times not recorded for historical figures prior to 1850"
      },
      "occupations": {
        "null_count": 12,
        "null_pct": 2.0,
        "classification": "NP",
        "rationale": "Pending biographical research"
      },
      "death_date": {
        "null_count": 8,
        "null_pct": 1.3,
        "classification": "NA",
        "rationale": "Living individuals"
      }
    },
    "acceptable_null_threshold": 0.15,
    "exceeds_threshold": false,
    "fields_exceeding_threshold": []
  }
}
```

### 2.4 Null Thresholds

| Dataset Tier | Max Acceptable Null Rate (per field) | Action if Exceeded |
|-------------|--------------------------------------|-------------------|
| Research Grade (A) | 5% | Document as known limitation; flag for future curation |
| Production Grade (B) | 15% | Document as known limitation |
| Exploratory Grade (C) | 30% | Acceptable; note in quality report |
| Draft Grade (D) | 50% | Acceptable for draft |
| Rejected (F) | >50% | Reject or return to draft |

**Exception:** Fields classified as `NA` (Not Applicable) are excluded from null rate calculations.

---

## 3. Duplicate Detection & Resolution

### 3.1 Duplicate Detection Strategy

Duplicate detection uses a **tiered approach** combining exact matching, fuzzy matching, and external reference matching:

#### Tier 1: Exact Key Matching

| Dataset Type | Dedup Key |
|-------------|-----------|
| RF-SIGNS | `name` (unique rashi name) |
| RF-NAK | `name` or `number` (unique nakshatra name/number) |
| RF-PADA | `(nakshatra_id, pada_number)` |
| RF-PLANET | `name` (unique graha name) |
| RF-HOUSE | `house_number` |
| RF-DASHA | `(dasha_type, lord, level)` |
| RF-AYAN | `name` (ayanamsa system) |
| RF-KARAKA | `(subject, graha, house_number)` |
| RF-TZ | `(tzid, start_date)` |
| RS-COHORT | `chart_id` within a cohort |
| RS-EVENT | `(chart_id, event_date, event_type, title)` |
| PB-WIKI | `wikidata_id` or `(wikipedia_title)` |
| PB-WIKIDATA | `wikidata_id` |
| PB-TWIN | `(twin_pair_id)` |
| UC-USER | `(user_id, birth_date, birth_place)` |

#### Tier 2: Fuzzy Matching

Applied after exact matching, using:

- **Date proximity**: Birth dates within 1 day with same place and name → flag as potential duplicate
- **Name similarity**: Levenshtein distance ≤ 2 for display names → flag
- **Location proximity**: Coordinates within 0.1° with same birth date → flag
- **Cross-dataset duplicate detection**: Same person appearing in PB-WIKI and PB-WIKIDATA

Fuzzy matching uses a weighted scoring model:

```json
{
  "fuzzy_match_score": 0.92,
  "scoring_breakdown": {
    "name_similarity": 0.95,
    "date_match": 1.0,
    "place_match": 0.9,
    "occupation_match": 0.8
  },
  "threshold": 0.85,
  "is_duplicate": true
}
```

#### Tier 3: External Reference Matching

Using external identifiers (Wikidata ID, Wikipedia title, DOI) to detect duplicates across collection methods.

### 3.2 Duplicate Resolution Protocol

```
┌───────────────────┐
│ Candidate         │
│ Duplicate Found   │
└─────────┬─────────┘
          │
┌─────────▼─────────┐
│ Automated check:  │
│ Exact match on    │── Yes ──→ Auto-merge: keep earliest record,
│ external ID?      │          set superseded_by on duplicate
└─────────┬─────────┘
          │ No
┌─────────▼─────────┐
│ Confidence score  │
│ ≥ 0.95?           │── Yes ──→ Auto-merge with confidence note
└─────────┬─────────┘
          │ No
┌─────────▼─────────┐
│ Confidence score  │
│ ≥ 0.75?           │── Yes ──→ Flag for curator review
└─────────┬─────────┘
          │ No
┌─────────▼─────────┐
│ Confidence score  │
│ < 0.75?           │── Yes ──→ Keep as separate records;
│                   │          add cross-reference note
└───────────────────┘
```

### 3.3 Duplicate Documentation

Every resolved duplicate is documented:

```json
{
  "duplicate_resolution": {
    "kept_record_id": "ASTRO-REC-WIKI-000042",
    "removed_record_ids": ["ASTRO-REC-WIKI-000156"],
    "resolution_method": "auto_merge_external_id",
    "matching_criteria": {
      "wikidata_id": "Q937",
      "exact_match": true
    },
    "resolution_date": "2026-07-15",
    "resolved_by": "Automated / Curator Name",
    "notes": "Duplicate entry from different Wikipedia extraction run. Wikidata ID match confirmed identity."
  }
}
```

### 3.4 Cross-Dataset Dedup

When the same person appears in multiple datasets (e.g., PB-WIKI and PB-TWIN), the records are linked via a cross-dataset person-level identity:

```json
{
  "cross_dataset_identity": {
    "person_id": "ASTRO-PERSON-000042",
    "records": [
      {"dataset_id": "ASTRO-PB-WIKI-v1.0.0", "record_id": "ASTRO-REC-WIKI-000042"},
      {"dataset_id": "ASTRO-PB-EVENTS-v1.0.0", "record_id": "ASTRO-REC-EVENT-000789"},
      {"dataset_id": "ASTRO-RS-COHORT-v2.1.0", "record_id": "ASTRO-REC-COHORT-000512"}
    ],
    "canonical_chart_record": "ASTRO-REC-WIKI-000042",
    "merge_status": "stable"
  }
}
```

---

## 4. Consistency Framework

### 4.1 Consistency Rule Categories

| Category | Definition | Examples |
|----------|------------|---------|
| **Syntactic** | Values conform to type/format constraints | All dates ISO 8601, all coordinates within ±180° |
| **Semantic** | Values are meaningful in context | Birth date ≤ today, death date ≥ birth date |
| **Relational** | Related values are mutually consistent | Latitude + longitude match country_code |
| **Temporal** | Chronological ordering is correct | Event dates are in sequence |
| **Astrological** | Astrological invariants hold | Planet.rashi matches planet.longitude → rashi; house numbers 1-12 |
| **Statistical** | Distributions are plausible | Not checking significance — just flagging impossible distributions (e.g., 100% same rashi) |

### 4.2 Universal Consistency Rules

These rules apply to ALL datasets:

| ID | Rule | Category | Severity |
|----|------|----------|----------|
| C-001 | Birth date ≤ current date | Semantic | Critical |
| C-002 | Birth date ≥ 1800-01-01 (unless historical dataset specifies otherwise) | Semantic | High |
| C-003 | Death date ≥ birth date (if both present) | Temporal | Critical |
| C-004 | Birth latitude ∈ [-90, 90] | Syntactic | Critical |
| C-005 | Birth longitude ∈ [-180, 180] | Syntactic | Critical |
| C-006 | Timezone offset ∈ [-720, +840] | Syntactic | High |
| C-007 | Event date ≥ birth date (for chart-related events) | Temporal | Critical |
| C-008 | Event date ≤ death date or current date (if both present) | Temporal | High |
| C-009 | Record timestamps: created_at ≤ updated_at | Temporal | Critical |
| C-010 | All enum fields contain values from the declared set | Syntactic | Critical |
| C-011 | No negative durations | Semantic | High |
| C-012 | Country code is valid ISO 3166-1 alpha-2 | Syntactic | Medium |
| C-013 | Sequence numbers are unique within dataset | Relational | Critical |
| C-014 | Record IDs are unique within dataset | Relational | Critical |
| C-015 | Cross-referenced record IDs exist in their target dataset | Relational | High |

### 4.3 Astrological Consistency Rules

For datasets containing computed astrological data:

| ID | Rule | Category | Severity |
|----|------|----------|----------|
| AC-001 | Planet longitude ∈ [0, 360) | Semantic | Critical |
| AC-002 | Planet latitude ∈ [-90, 90] | Semantic | Critical |
| AC-003 | Sidereal longitude = tropical longitude − ayanamsa value | Astrological | Critical |
| AC-004 | Planet rashi matches floor(sidereal_longitude / 30) | Astrological | Critical |
| AC-005 | Planet rashi_degree ∈ [0, 30) | Semantic | Critical |
| AC-006 | House number ∈ [1, 12] | Semantic | Critical |
| AC-007 | Nakshatra number ∈ [1, 27] | Semantic | Critical |
| AC-008 | Pada number ∈ [1, 4] | Semantic | Critical |
| AC-009 | Dasha end_date > dasha start_date | Temporal | Critical |
| AC-010 | Child dasha dates contained within parent dasha dates | Temporal | Critical |
| AC-011 | Dasha level ≥ 1 (integer) | Semantic | High |
| AC-012 | Shadbala score ∈ [0, 10] | Semantic | High |
| AC-013 | Ashtakavarga bindu count ∈ [1, 8] per house | Semantic | High |
| AC-014 | Dignity is consistent with planet position (e.g., exalted only in exaltation sign) | Astrological | Medium |

### 4.4 Cross-Dataset Consistency

When a person appears in multiple datasets:

| ID | Rule | Datasets | Severity |
|----|------|----------|----------|
| XC-001 | Same birth_date across datasets for same person | PB-WIKI, PB-EVENTS, RS-* | High |
| XC-002 | Same birth_place across datasets for same person | PB-WIKI, PB-EVENTS | High |
| XC-003 | Death_date consistent across datasets | PB-WIKI, PB-EVENTS, RS-EVENT | High |
| XC-004 | Twin birth_interval ≤ 1440 minutes | PB-TWIN | Medium |
| XC-005 | Twin birth_order consistent (1 < 2) | PB-TWIN | Medium |

### 4.5 Consistency Violation Handling

| Severity | Definition | Required Action |
|----------|------------|-----------------|
| **Critical** | Data integrity violation; affects usability | Blocking — must be resolved or record excluded before Stable |
| **High** | Likely data error; affects reliability | Must be resolved, documented, or accepted with justification |
| **Medium** | Possible error or edge case | Document in quality report; investigate |
| **Low** | Minor inconsistency; unlikely to affect analysis | Document if discovered; no blocking |

---

## 5. Bias Assessment Framework

### 5.1 Bias Dimensions

Every dataset is assessed for bias across these dimensions:

| Dimension | Definition | Examples |
|-----------|------------|----------|
| **Selection Bias** | Systematic exclusion of certain groups from the dataset | Over-representation of Western celebrities, under-representation of Asian figures |
| **Measurement Bias** | Systematic errors in how data was collected/recorded | Birth times rounded to nearest hour in self-reported data vs. precise on certificates |
| **Survivorship Bias** | Only surviving records are included; lost records may differ | Ancient charts vs. modern ones; Wikipedia only includes notable people |
| **Reporting Bias** | Some events are more likely to be reported/recorded than others | Marriages more likely recorded than divorces; achievements more than failures |
| **Temporal Bias** | Data distribution varies systematically over time | Better birth records after 1900, worse before 1800 |
| **Geographic Bias** | Geographic distribution does not match global population | Over-representation of Europe and North America |
| **Gender Bias** | Systematic gender imbalance | Historical under-representation of women in public records |
| **Cultural Bias** | Dominance of one cultural/tradition perspective | Vedic astrology data may over-represent Indian cultural practices |
| **Confirmation Bias** | Data collected to support a hypothesis, not representative | Research cohorts selected to test a specific astrological claim |
| **Publication Bias** | Positive results more likely published than negative | Event collections focused on events that "worked" astrologically |

### 5.2 Bias Assessment Methodology

Each dataset undergoes a structured bias assessment:

```json
{
  "bias_assessment": {
    "dataset_id": "ASTRO-PB-WIKI-v1.0.0",
    "assessed_by": "Curator Name",
    "assessed_at": "2026-07-15",
    "dimensions": [
      {
        "dimension": "selection_bias",
        "severity": "high",
        "description": "Dataset over-represents notable individuals (Wikipedia notability criteria). Birth time data available primarily for Western public figures post-1850.",
        "direction": "Western, notable, 20th-21st century over-representation",
        "mitigation": "Document bias; weight analyses by region/era when possible; combine with PB-WIKIDATA for broader coverage",
        "quantification": {
          "metric": "geographic_distribution",
          "value": {"north_america": "42%", "europe": "35%", "asia": "15%", "other": "8%"},
          "reference_distribution": "global_population",
          "deviation": "significant"
        }
      },
      {
        "dimension": "temporal_bias",
        "severity": "medium",
        "description": "Birth data density increases significantly after 1900. Pre-1800 records are rare and less reliable.",
        "mitigation": "Clearly document temporal coverage; separately analyze pre-1900 and post-1900 cohorts"
      }
    ],
    "overall_bias_risk": "medium",
    "recommendations": [
      "Use geographic weighting in statistical analyses",
      "Separate analyses by era (pre-1900, 1900-1950, post-1950)",
      "Combine with non-Western-sourced datasets for balance"
    ]
  }
}
```

### 5.3 Bias Quantification Metrics

| Metric | Description | Reference Distribution |
|--------|-------------|----------------------|
| Geographic distribution | Countries/regions represented | UN population statistics or global birth distribution |
| Temporal distribution | Birth years represented | Global historical birth estimates |
| Gender ratio | Male/female/other ratio | Global population statistics |
| Occupation distribution | ISCO category distribution | Global labor force statistics |
| Birth time hour distribution | Uniform (should be flat for unbiased sample) | Uniform distribution (null hypothesis) |
| Birth month distribution | Uniform (should be flat) | Known seasonal birth variation |
| Source type distribution | Mix of source types | Comparative across datasets |

### 5.4 Bias Reporting

Every dataset's quality report includes a bias statement:

```json
{
  "bias_statement": {
    "overall_assessment": "This dataset exhibits moderate selection bias toward Western, 20th-century public figures. Geographic and temporal biases are documented and quantifiable. Statistical analyses using this data should incorporate appropriate weighting or interpret results with these biases in mind.",
    "known_biases": [
      "Selection: Over-represents notable individuals (Wikipedia notability filter)",
      "Temporal: Under-represents pre-1900 births (scarce records)",
      "Geographic: Over-represents North America and Europe",
      "Gender: Moderate male skew (~65:35) due to historical notability patterns"
    ],
    "mitigations_applied": [
      "Geographic coverage documented in metadata",
      "Temporal coverage windows specified per cohort",
      "Gender balance noted; cohort-level filtering available"
    ],
    "residual_risk": "medium"
  }
}
```

### 5.5 Bias Acceptability by Dataset Tier

| Bias Severity | Research Grade (A) | Production Grade (B) | Exploratory Grade (C) |
|---------------|-------------------|---------------------|----------------------|
| None | Acceptable | Acceptable | Acceptable |
| Low | Acceptable | Acceptable | Acceptable |
| Medium | Acceptable with mitigations | Acceptable with documentation | Acceptable |
| High | Not acceptable (must mitigate) | Acceptable with strong caveats | Acceptable with documentation |
| Critical | Not acceptable | Not acceptable | Acceptable with documentation |

---

## 6. Ethical Review Process

### 6.1 Ethical Review Triggers

A formal ethical review is required when ANY of the following apply:

- Dataset contains **Private** or **Restricted** privacy-tier data
- Dataset includes data from **living individuals** without explicit consent
- Dataset includes **health/medical information** (RS-HEALTH)
- Dataset includes **data of minors** (<18 years old)
- Dataset was obtained through **research partnerships** with data-sharing agreements
- Dataset contains **sensitive personal data** (religion, caste, sexual orientation, political affiliation)
- Dataset is intended for **AI training** that could generate predictions about individuals
- Dataset is derived from **user-submitted data** (UC-*)

### 6.2 Ethical Review Board

The AstroOS dataset ethical review is conducted by:

- **Dataset Curator** — presents the dataset and its ethical considerations
- **Privacy Officer** — reviews privacy handling and compliance
- **Ethics Advisor** — assesses broader ethical implications
- **Legal Counsel** — reviews legal compliance (if required)

### 6.3 Ethical Review Checklist

```
DATASET ETHICAL REVIEW CHECKLIST
==================================

Dataset: ____________________  Version: ________  Reviewer: ________  Date: ________

A. DATA SUBJECT PROTECTION
[ ] Is all PII identified and handled appropriately?
[ ] Is the anonymization method documented and sufficient?
[ ] Is consent documented (where required)?
[ ] Are data subjects informed of how their data is used?
[ ] Is there a withdrawal mechanism for consent?

B. HARM & SENSITIVITY
[ ] Could this dataset cause harm to any group or individual?
[ ] Does the dataset perpetuate or amplify existing biases?
[ ] Does the dataset include predictions about individuals?
[ ] Are there cultural sensitivity considerations?
[ ] Could the dataset be used for discriminatory purposes?

C. LEGAL COMPLIANCE
[ ] Does the dataset comply with GDPR (if EU subjects)?
[ ] Does the dataset comply with CCPA (if California subjects)?
[ ] Does the dataset comply with HIPAA (if US health data)?
[ ] Is the licensing clear and legally valid?
[ ] Are data-sharing agreements in place (if partner data)?

D. TRANSPARENCY & ACCOUNTABILITY
[ ] Is the dataset's provenance fully documented?
[ ] Are known biases documented?
[ ] Are known limitations documented?
[ ] Is the intended use clearly stated?
[ ] Are prohibited uses clearly stated?
[ ] Is there a point of contact for ethical concerns?

E. FINAL DECISION
[ ] Approved — no ethical concerns
[ ] Approved with conditions: ______________________________
[ ] Returned for revisions: _______________________________
[ ] Rejected: _____________________________________________

Reviewer Signature: ______________  Date: ________
```

### 6.4 Ethical Use Restrictions

Datasets that pass ethical review may carry usage restrictions:

```json
{
  "ethical_restrictions": {
    "prohibited_uses": [
      "Individual profiling or prediction without consent",
      "Discrimination based on astrological attributes",
      "Use in automated decision-making affecting individuals without human oversight",
      "Re-identification of anonymized records"
    ],
    "required_attributions": [
      "Dataset source must be cited in all publications",
      "Anonymization method must be documented"
    ],
    "handling_requirements": [
      "Dataset must not be redistributed without privacy review",
      "AI models trained on this data must not expose individual training records"
    ]
  }
}
```

---

## 7. Dataset-Specific Quality Specifications

### 7.1 Reference Dataset Quality Specifications

| Dataset Type | Expected Records | Key Quality Metrics | Special Rules |
|-------------|-----------------|---------------------|---------------|
| RF-SIGNS | 12 | 100% completeness; 100% field population (required fields) | Zero-tolerance for missing records |
| RF-NAK | 27 | 100% completeness; NULL fields documented with rationale | Zero-tolerance for missing records |
| RF-PADA | 108 | 100% completeness; mathematical accuracy verified | Cross-validate with DivisionalEngine D9 |
| RF-PLANET | 9 | 100% completeness; 100% field population | Symmetry check on friend/enemy relationships |
| RF-HOUSE | 12 | 100% completeness | House numbers sequential 1-12 |
| RF-AYAN | 6 | 100% completeness; formula reproducibility | Spot-check against IAE at 10-year intervals |
| RF-DASHA | Per system | Dasha years sum to expected total | Vimshottari sum=120, Ashtottari sum=108 |
| RF-KARAKA | Variable | Completeness ≥90% | Cross-reference with classical texts |
| RF-TZ | Per release | 100% coverage of tzdata entries | Quarterly update aligned with IANA releases |

### 7.2 Research Dataset Quality Specifications

| Dataset Type | Min Completeness | Min Accuracy | Special Rules |
|-------------|-----------------|--------------|---------------|
| RS-COHORT | 95% | 95% | Reproducible criteria; selection bias documented |
| RS-EVENT | 80% | 90% (verified events) / 70% (estimated) | Event date accuracy must be documented per event |
| RS-MARRIAGE | 80% | 90% | Marriage date ≥ legal minimum age; chronological ordering |
| RS-CAREER | 80% | 85% | Occupation classification to ISCO standard |
| RS-HEALTH | 75% | 85% | ICD codes recommended; source type documented |
| RS-WEALTH | 75% | 80% | Wealth category methodology documented |
| RS-SPIRITUAL | 75% | 80% | Event type classification documented |

### 7.3 Benchmark Dataset Quality Specifications

| Dataset Type | Min Completeness | Min Accuracy | Special Rules |
|-------------|-----------------|--------------|---------------|
| BM-CALC | 100% | 100% (≤ tolerance) | Each case traceable to external reference |
| BM-ASPECT | 100% | 100% | Classical tradition documented for each case |
| BM-DASHA | 100% | 100% | Expected periods from verified reference |
| BM-TRANSIT | 100% | 100% | Reference values from external ephemeris |
| BM-BALA | 100% | 100% | Per-component scores validated |
| BM-ASTAK | 100% | 100% | Bindu counts verified |
| BM-DIV | 100% | 100% | All 16 division types covered |
| BM-PERF | 100% | — | Hardware documented; methodology reproducible |

### 7.4 Synthetic Dataset Quality Specifications

| Dataset Type | Min Records | Key Quality Metrics | Special Rules |
|-------------|-------------|---------------------|---------------|
| SY-RANDOM | 10,000 | Distribution uniformity (chi-squared p > 0.05); seeded reproducibility | Seed documented; distribution tests pass |
| SY-CONTROLLED | Per design | Controlled parameters identical; varied parameter differs only as intended | Design document required |
| SY-MONTE | 100,000 | Distribution stability at multiple sample sizes | Convergence check at 10k, 50k, 100k |
| SY-NULL | Per study | Marginal distributions preserved; astrological association destroyed | Randomization method documented |

### 7.5 Public Dataset Quality Specifications

| Dataset Type | Key Quality Metrics | Special Rules |
|-------------|---------------------|---------------|
| PB-WIKI | Wikipedia page exists; birth date in infobox; coordinates verified | ≥2 independent sources for birth date preferred |
| PB-WIKIDATA | Date precision ≥9 (year); property IDs documented | SPARQL query reproducible; results versioned |
| PB-EVENTS | Each event from verifiable public source; confidence documented | Source URL required; biographical sources preferred |
| PB-TWIN | Twin type documented; birth interval accuracy stated | Birth order recorded; twin source cited |

### 7.6 User-Contributed Dataset Quality Specifications

| Dataset Type | Key Quality Metrics | Special Rules |
|-------------|---------------------|---------------|
| UC-USER | Input validation; user-declared accuracy | Consent check; age verification; privacy filter |
| UC-EVENT | Event date valid; profanity/content filter | Opt-in for research; withdrawal mechanism |
| UC-COHORT | Cohort criteria documented; privacy audit pass | Only anonymous chart refs; reproducible |

---

## 8. Quality Summary by Dataset Tier

| Quality Dimension | Tier A (Research) | Tier B (Production) | Tier C (Exploratory) | Tier D (Draft) |
|-------------------|-------------------|---------------------|----------------------|----------------|
| Record Completeness | = 100% | ≥ 95% | ≥ 80% | ≥ 50% |
| Field Completeness | ≥ 95% | ≥ 90% | ≥ 75% | ≥ 50% |
| Required Field Completeness | = 100% | = 100% | ≥ 95% | ≥ 80% |
| Accuracy (sampled) | ≥ 99% | ≥ 95% | ≥ 85% | Not required |
| Consistency (critical rules) | 0 violations | 0 violations | ≤ 1 (documented) | Not required |
| Bias Assessment | Required + mitigations | Required + documented | Recommended | Not required |
| Ethical Review | If triggered | If triggered | If triggered | If triggered |
| Duplicates Resolved | 100% | 100% | Documented | Not required |
| Null Rate (per field) | ≤ 5% | ≤ 15% | ≤ 30% | ≤ 50% |
| Provenance Documentation | Full | Full | Major elements | Basic |

---

*End of Phase 5: Dataset Quality Standards. Awaiting approval to proceed to Phase 6: Standard Formats.*
