---
name: astrosos-dataset-standards
description: "Complete data standards for the AstroOS Research Dataset Repository — metadata, quality scoring, validation, file structure, lifecycle, ethics"
metadata: 
  node_type: memory
  type: reference
  domain: datasets
  status: draft
  phase: 3
  originSessionId: e78a75e5-611c-4c3f-99a8-68817dfe9484
---

# AstroOS Dataset Standards — Phase 3

> **Status:** DRAFT — pending approval
> **Owner:** Chief Dataset & Research Curator
> **Version:** 1.0
> **Date:** 2026-07-15

---

## Table of Contents

1. [Dataset Identity Standards](#1-dataset-identity-standards)
2. [Common Metadata Standard](#2-common-metadata-standard)
3. [Quality Scoring Methodology](#3-quality-scoring-methodology)
4. [Validation Framework](#4-validation-framework)
5. [Documentation Templates](#5-documentation-templates)
6. [File Structure & Naming Standards](#6-file-structure--naming-standards)
7. [Dataset Lifecycle Procedures](#7-dataset-lifecycle-procedures)
8. [Ethical & Legal Standards](#8-ethical--legal-standards)
9. [Repository Directory Layout](#9-repository-directory-layout)

---

## 1. Dataset Identity Standards

### 1.1 Permanent Dataset ID

Every dataset receives exactly one permanent identifier:

```
ASTRO-{CATEGORY}-{TYPE}-{VERSION}
```

**Rules:**
- The ID is case-sensitive and always uppercase
- The ID is permanent for the dataset concept — version changes only the VERSION segment
- A dataset that changes category or type is a *new* dataset with a new ID (old ID is deprecated, never reused)
- Hyphens are the only separator character

### 1.2 Category Codes

| Code | Category |
|------|----------|
| RF | Reference |
| RS | Research |
| BM | Benchmark |
| VL | Validation |
| QT | QA/Test |
| AI | AI Evaluation |
| SY | Synthetic |
| PB | Public |
| LC | Licensed/Commercial |
| UC | User-Contributed |

### 1.3 Type Codes

| Category | Type Code | Type Name |
|----------|-----------|-----------|
| RF | EPHEM | Ephemeris Data |
| RF | SIGNS | Reference Sign Data |
| RF | NAK | Reference Nakshatra Data |
| RF | PADA | Reference Pada Data |
| RF | PLANET | Reference Planet Data |
| RF | HOUSE | Reference House Meanings |
| RF | KARAKA | Reference Karakatva Data |
| RF | AYAN | Reference Ayanamsa Data |
| RF | DASHA | Dasha Reference Table |
| RF | TZ | Timezone & Location Reference |
| RS | COHORT | Birth Chart Cohorts |
| RS | EVENT | Life Event Datasets |
| RS | MARRIAGE | Marriage Datasets |
| RS | CAREER | Career Datasets |
| RS | HEALTH | Health Datasets |
| RS | WEALTH | Wealth & Financial Datasets |
| RS | SPIRITUAL | Spiritual & Progeny Datasets |
| RS | FLAT | Flattened Chart Records |
| BM | CALC | Calculation Accuracy Benchmarks |
| BM | ASPECT | Aspect Detection Benchmarks |
| BM | DASHA | Dasha Calculation Benchmarks |
| BM | TRANSIT | Transit Benchmarks |
| BM | BALA | Shadbala Benchmarks |
| BM | ASTAK | Ashtakavarga Benchmarks |
| BM | DIV | Divisional Chart Benchmarks |
| BM | PERF | Performance Benchmarks |
| VL | XPLATFORM | Cross-Platform Validation |
| VL | CHART | End-to-End Chart Validation |
| VL | CONSISTENCY | Consistency Validation |
| QT | REGRESSION | Regression Test Charts |
| QT | EDGE | Edge Case Charts |
| QT | STRESS | Stress/Volume Test Data |
| QT | INTEGRATION | Integration Test Scenarios |
| AI | INTERP | Chart Interpretation Benchmarks |
| AI | HALLUC | Interpretation Hallucination Detection |
| AI | FACT | Factual Accuracy Tests |
| AI | REPORT | Report Generation Benchmarks |
| AI | RULE | Rule Evaluation Benchmarks |
| SY | RANDOM | Random Birth Cohorts |
| SY | CONTROLLED | Controlled Experiment Charts |
| SY | MONTE | Monte Carlo Reference Datasets |
| SY | NULL | Null Hypothesis Baselines |
| PB | WIKI | Wikipedia Birth Chart Collection |
| PB | WIKIDATA | Wikidata Filtered Charts |
| PB | EVENTS | Public Figure Event Collection |
| PB | TWIN | Known Twin Charts |
| LC | SWISS | Swiss Ephemeris Professional |
| LC | CHART | Licensed Birth Chart Collections |
| LC | PARTNER | Research Partner Data |
| UC | USER | User Birth Charts |
| UC | EVENT | User-Contributed Events |
| UC | COHORT | Community Research Cohorts |

### 1.4 Version String

Follows SemVer 2.0: `v{M}.{m}.{p}`

| Segment | Range | Bump Trigger |
|---------|-------|-------------|
| M (Major) | 0–∞ | Schema changes, incompatible format, irreproducible results |
| m (Minor) | 0–∞ | Additions (new records, new optional fields), backward-compatible |
| p (Patch) | 0–∞ | Corrections, metadata updates, no semantic data change |

**Convention for initial versions:**
- `v0.1.0` — Draft / Candidacy
- `v1.0.0` — First stable release
- `v0.x.x` — NEVER used in production research (prerelease only)

### 1.5 File Naming Convention

Every dataset file follows this naming convention:

```
{DATASET-ID}_{FORMAT}.{ext}
{DATASET-ID}_{FORMAT}_{PART}.{ext}     (for split files)
{DATASET-ID}_{FORMAT}_metadata.{ext}   (metadata file)
{DATASET-ID}_{FORMAT}_quality.{ext}    (quality report)
```

**Examples:**
- `ASTRO-RF-SIGNS-v1.0.0_CSV.csv`
- `ASTRO-RF-SIGNS-v1.0.0_CSV_metadata.json`
- `ASTRO-RF-SIGNS-v1.0.0_CSV_quality.json`
- `ASTRO-RS-COHORT-v2.1.0_PARQUET.parquet`
- `ASTRO-RS-COHORT-v2.1.0_PARQUET_part01.parquet`
- `ASTRO-RS-COHORT-v2.1.0_PARQUET_part02.parquet`

### 1.6 Dataset Directory Structure

```
datasets/
  {category-code}/
    {type-code}/
      {dataset-id}/
        {dataset-id}_{format}.{ext}
        {dataset-id}_{format}_metadata.json
        {dataset-id}_{format}_quality.json
        {dataset-id}_changelog.md
        {dataset-id}_catalog-entry.md
        {dataset-id}_data-dictionary.md
        {dataset-id}_schema.{format}
```

---

## 2. Common Metadata Standard

Every dataset MUST carry an `_metadata.json` file with the following fields. Fields marked **[R]** are required; **[O]** are optional but recommended; **[C]** are conditional.

### 2.1 Identity Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dataset_id` | String | **[R]** | Permanent dataset ID (ASTRO-{CATEGORY}-{TYPE}-v{X.Y.Z}) |
| `name` | String | **[R]** | Human-readable name (≤100 chars) |
| `description` | String | **[R]** | One-paragraph purpose and scope (≤500 chars) |
| `category` | String | **[R]** | From taxonomy: Reference/Research/Benchmark/Validation/QA-Test/AI-Eval/Synthetic/Public/Licensed/User-Contributed |
| `category_code` | String | **[R]** | Two-letter category code |
| `type` | String | **[R]** | Type name from taxonomy |
| `type_code` | String | **[R]** | Type code from taxonomy |
| `version` | String | **[R]** | Semantic version (e.g., "1.0.0") |
| `dataset_version` | String | **[R]** | Full versioned ID: "ASTRO-{CAT}-{TYPE}-v{M}.{m}.{p}" |
| `supersedes` | String | **[C]** | Dataset ID this version supersedes (null if first) |
| `superseded_by` | String | **[C]** | Dataset ID that supersedes this (null if current) |

### 2.2 Provenance Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provenance_tier` | String | **[R]** | Primary / Derived / Curated / Generated / Contributed |
| `source_description` | String | **[R]** | Free-text description of origin |
| `source_uris` | [String] | **[R]** | List of source URIs (URLs, DOIs, file paths) |
| `source_version` | String | **[O]** | Version of the source data (if applicable) |
| `collection_method` | String | **[R]** | How data was collected (API_extract / manual_curation / web_scrape / user_submission / generated / licensed / etc.) |
| `collection_date_start` | Date | **[O]** | When collection began (ISO 8601) |
| `collection_date_end` | Date | **[O]** | When collection ended (ISO 8601) |
| `curator` | String | **[R]** | Entity or role responsible for curation |
| `curator_contact` | String | **[O]** | Contact email or reference |
| `curator_notes` | String | **[O]** | Free-text notes from curator |

### 2.3 Quality Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quality_score` | Float | **[R]** | Overall quality score 0.0–1.0 (see §3) |
| `quality_score_breakdown` | Object | **[R]** | Per-dimension scores (completeness, accuracy, consistency, coverage, timeliness) |
| `validation_status` | String | **[R]** | Unvalidated / In-Review / Validated / Failed / Not-Applicable |
| `validation_date` | Date | **[C]** | Date of last validation (required if status = Validated/Failed) |
| `validation_report_ref` | String | **[C]** | Link to validation report (required if status = Validated/Failed) |
| `known_limitations` | [String] | **[R]** | Array of documented limitations (empty array = no known limitations documented) |
| `known_biases` | [String] | **[R]** | Array of documented biases (empty array = no known biases documented) |
| `completeness_pct` | Float | **[R]** | Percentage of expected records present (0.0–100.0) |
| `missing_fields` | [String] | **[R]** | List of fields that have null/missing values beyond acceptable threshold |
| `duplicate_count` | Integer | **[R]** | Number of duplicate records identified and resolved |
| `duplicate_pct` | Float | **[R]** | Percentage of duplicates (0.0–100.0) |

### 2.4 Legal & Ethical Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `license_id` | String | **[R]** | SPDX license identifier (e.g., "CC-BY-SA-4.0", "CC0-1.0", "LicenseRef-AstroOS-Internal") |
| `license_name` | String | **[R]** | Human-readable license name |
| `license_url` | String | **[C]** | URL to full license text (required for non-SPDX licenses) |
| `license_restrictions` | [String] | **[O]** | Notable restrictions (non-commercial, attribution required, etc.) |
| `privacy_tier` | String | **[R]** | Public / Anonymous / Pseudonymous / Private / Restricted |
| `privacy_notes` | String | **[O]** | Privacy handling procedures applied |
| `confidence_tier` | String | **[R]** | Verified / Estimated / Rectified / Synthetic / Unknown |
| `confidence_notes` | String | **[O]** | Confidence assessment methodology |
| `contains_pii` | Boolean | **[R]** | Does the dataset contain any personally identifiable information? |
| `pii_fields` | [String] | **[C]** | List of PII fields (required if contains_pii = true) |
| `anonymization_method` | String | **[C]** | Method used for anonymization (required if privacy_tier = Anonymous/Pseudonymous) |
| `anonymization_date` | Date | **[C]** | When anonymization was applied |
| `ethical_approval_ref` | String | **[O]** | Ethics board approval reference if applicable |
| `ethical_notes` | String | **[O]** | Any additional ethical considerations |
| `consent_obtained` | Boolean | **[C]** | Was consent obtained from data subjects? (required if privacy_tier = Private) |

### 2.5 Technical Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `format` | String | **[R]** | Primary distribution format (CSV / JSON / JSONL / Parquet / SQL / SE1 / etc.) |
| `formats_available` | [String] | **[R]** | All formats this dataset is available in |
| `record_count` | Integer | **[R]** | Number of records/rows |
| `field_count` | Integer | **[R]** | Number of fields/columns |
| `file_size_bytes` | Integer | **[R]** | Total size in bytes |
| `checksum_sha256` | String | **[R]** | SHA-256 hash of the primary data file |
| `checksum_algorithm` | String | **[R]** | Checksum algorithm used (default: "sha256") |
| `compression` | String | **[O]** | Compression algorithm if applicable (none / gzip / zstd / snappy) |
| `schema_ref` | String | **[R]** | Path or URL to the schema definition file |
| `data_dictionary_ref` | String | **[R]** | Path or URL to the data dictionary |
| `engine_version` | String | **[C]** | AstroOS engine version used for computation (required for derived/computed data) |
| `computation_params` | Object | **[C]** | Calculation parameters used (ayanamsa, house system, etc.) |

### 2.6 Lifecycle Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lifecycle_stage` | String | **[R]** | Draft / Candidacy / Stable / Deprecated / Archived |
| `created_at` | DateTime | **[R]** | ISO 8601 creation timestamp |
| `updated_at` | DateTime | **[R]** | ISO 8601 last modification timestamp |
| `published_at` | DateTime | **[C]** | When first promoted to Stable (required if lifecycle_stage ≥ Stable) |
| `deprecated_at` | DateTime | **[C]** | When deprecated (required if lifecycle_stage = Deprecated/Archived) |
| `archived_at` | DateTime | **[C]** | When archived (required if lifecycle_stage = Archived) |
| `maintainer` | String | **[R]** | Entity/role responsible for maintenance |
| `maintainer_email` | String | **[O]** | Contact for dataset issues |
| `review_date` | Date | **[R]** | Date of last review (for currency assessment) |
| `next_review_date` | Date | **[O]** | Recommended next review date |
| `changelog_ref` | String | **[R]** | Path to changelog file |

### 2.7 Classification Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tags` | [String] | **[O]** | Free-form tags for discovery (snake_case, ≤20 per dataset) |
| `research_domains` | [String] | **[O]** | Astrological research domains this supports |
| `intended_use` | String | **[R]** | Statement of intended use |
| `prohibited_uses` | [String] | **[O]** | Uses that are explicitly prohibited |
| `language` | String | **[O]** | Primary language of data content |
| `geographic_coverage` | String | **[O]** | Geographic scope (e.g., "global", "India", "USA") |
| `temporal_coverage` | Object | **[O]** | Temporal range: {start: Date, end: Date} |
| `dataset_git_ref` | String | **[O]** | Git commit/tag referencing this dataset version in the repository |

---

## 3. Quality Scoring Methodology

### 3.1 Overview

Every dataset receives a **quality score** — a float 0.0–1.0 — computed as a weighted average across six dimensions. The score is recalculated each time the dataset is validated or updated.

### 3.2 Quality Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Completeness** | 0.25 | Are all expected records and fields present? |
| **Accuracy** | 0.25 | Do values match ground truth / reference sources? |
| **Consistency** | 0.15 | Do values follow internal consistency rules? |
| **Coverage** | 0.15 | Does the dataset adequately cover the intended scope? |
| **Timeliness** | 0.10 | Is the data current relative to its domain? |
| **Provenance** | 0.10 | Is the origin well-documented and verifiable? |

### 3.3 Dimension Scoring Rubric

Each dimension is scored 0.0–1.0 using the following rubrics:

#### 3.3.1 Completeness (weight: 0.25)

| Score | Criteria |
|-------|----------|
| 1.00 | 100% of expected records present; no null values in required fields |
| 0.90 | 100% of records present; >95% of fields populated |
| 0.75 | 90–99% records present; 80–95% fields populated |
| 0.50 | 75–89% records present; 60–79% fields populated |
| 0.25 | 50–74% records present; 40–59% fields populated |
| 0.00 | <50% records present or <40% fields populated |

**Formula:** `completeness = (record_presence_ratio * 0.5) + (field_population_ratio * 0.5)`

#### 3.3.2 Accuracy (weight: 0.25)

| Score | Criteria |
|-------|----------|
| 1.00 | ≥99% of sampled values match ground truth; no systematic errors |
| 0.90 | 95–98.9% accuracy; minor random errors only |
| 0.75 | 85–94.9% accuracy; some systematic errors documented |
| 0.50 | 70–84.9% accuracy; significant errors identified |
| 0.25 | 50–69.9% accuracy; major errors present |
| 0.00 | <50% accuracy or ground truth not established |

**Determination:** Statistical sampling — for datasets >10K records, audit ≥385 random records (95% confidence, 5% margin); for smaller datasets, audit ≥30% of records.

#### 3.3.3 Consistency (weight: 0.15)

| Score | Criteria |
|-------|----------|
| 1.00 | All consistency rules pass; no contradictions found |
| 0.90 | All critical consistency rules pass; <5% non-critical violations |
| 0.75 | All critical rules pass; 5–15% non-critical violations |
| 0.50 | 1 critical rule violation found (documented as known limitation) |
| 0.25 | 2–3 critical rule violations found |
| 0.00 | >3 critical rule violations or schema violations |

**Consistency rules:** Defined per dataset type in the validation framework (§4). Examples: date fields chronological, degree fields in 0–360 range, house numbers 1–12.

#### 3.3.4 Coverage (weight: 0.15)

| Score | Criteria |
|-------|----------|
| 1.00 | Full intended scope covered with even distribution |
| 0.90 | >90% of scope covered; minor gaps documented |
| 0.75 | 75–90% of scope covered |
| 0.50 | 50–74% of scope covered |
| 0.25 | 25–49% of scope covered |
| 0.00 | <25% of scope covered |

**Scope definition:** Per dataset — e.g., "all 12 signs" for RF-SIGNS (coverage = 1.00 since all 12 are present), or "all countries with birth registries" for a geographic cohort.

#### 3.3.5 Timeliness (weight: 0.10)

| Score | Criteria |
|-------|----------|
| 1.00 | Dataset reviewed/updated within the last review cycle |
| 0.90 | Within 1.5× review cycle |
| 0.75 | Within 2× review cycle |
| 0.50 | Within 3× review cycle |
| 0.25 | Within 4× review cycle |
| 0.00 | >4× review cycle overdue, or date-sensitive dataset outdated |

**Review cycle:** Defined per dataset type in lifecycle standards. Examples: reference datasets (annual) = 1.00 if reviewed within 12 months, 0.50 if 24–36 months since review.

#### 3.3.6 Provenance (weight: 0.10)

| Score | Criteria |
|-------|----------|
| 1.00 | Full provenance trail: source, collection method, curation, version all documented |
| 0.90 | Provenance documented with minor gaps only |
| 0.75 | Major provenance elements present; some gaps in curation trail |
| 0.50 | Source known but collection/curation details incomplete |
| 0.25 | Source attribution present but unverifiable |
| 0.00 | No provenance documentation available |

### 3.4 Overall Quality Score

```
quality_score = Σ(dimension_score_i × weight_i)

Where weights_i = {completeness: 0.25, accuracy: 0.25, consistency: 0.15,
                    coverage: 0.15, timeliness: 0.10, provenance: 0.10}
```

### 3.5 Quality Tiers

| Score Range | Tier | Label | Recommended Use |
|-------------|------|-------|-----------------|
| 0.90–1.00 | A | Research Grade | Any research, publication, benchmark |
| 0.75–0.89 | B | Production Grade | Internal research, statistical analysis; note limitations in publications |
| 0.50–0.74 | C | Exploratory Grade | Exploratory analysis only; not for publication |
| 0.25–0.49 | D | Draft Grade | Internal review only; not for analysis |
| 0.00–0.24 | F | Rejected | Do not use |

### 3.6 Quality Report File

Every validated dataset produces a `_quality.json` file containing:

```json
{
  "dataset_id": "ASTRO-RF-SIGNS-v1.0.0",
  "quality_score": 0.97,
  "quality_tier": "A",
  "dimension_scores": {
    "completeness": 0.80,
    "accuracy": 1.00,
    "consistency": 1.00,
    "coverage": 1.00,
    "timeliness": 1.00,
    "provenance": 1.00
  },
  "validation_date": "2026-07-15",
  "validation_tool_version": "1.0.0",
  "sampling_method": "random_385_95pct_5pct",
  "sample_size": 12,
  "violations": [
    {
      "severity": "minor",
      "rule": "completeness.null_fields",
      "count": 14,
      "description": "Signs direction field is NULL for all 12 records (left NULL per seed migration notes)"
    }
  ],
  "known_limitations": [
    "Signs.direction field is NULL pending textual verification"
  ]
}
```

---

## 4. Validation Framework

### 4.1 Validation Levels

Every dataset passes through up to four levels of validation:

| Level | Name | Performed By | Scope | Mandatory For |
|-------|------|-------------|-------|---------------|
| L1 | Automated Schema | CI pipeline / script | Schema compliance, type checking, format validation | All datasets |
| L2 | Automated Quality | CI pipeline / script | Quality scoring, consistency rules, duplicate detection | Candidacy+ |
| L3 | Statistical Audit | Curator + automated | Statistical sampling, distribution checks, bias assessment | Stable+ |
| L4 | Peer Review | Second curator | Manual review of methodology, provenance, limitations | Research Grade |

### 4.2 Universal Validation Rules (ALL datasets)

These rules apply to every dataset regardless of type:

| Rule ID | Rule | Severity | Automation |
|---------|------|----------|------------|
| U-001 | Dataset ID follows `ASTRO-{CAT}-{TYPE}-v{M}.{m}.{p}` | Critical | Automated |
| U-002 | `_metadata.json` present and contains all required fields | Critical | Automated |
| U-003 | All required metadata fields populated (non-null for strings, non-zero for numeric) | Critical | Automated |
| U-004 | Data file checksum matches `checksum_sha256` in metadata | Critical | Automated |
| U-005 | Record count in metadata matches actual row count | Critical | Automated |
| U-006 | Field count in metadata matches actual column count | Critical | Automated |
| U-007 | No duplicate records across the dataset's unique key | High | Automated |
| U-008 | All date fields parse as valid ISO 8601 dates | High | Automated |
| U-009 | All numeric fields within declared min/max ranges | High | Automated |
| U-010 | All enum fields contain values from the declared set | High | Automated |
| U-011 | Changelog file present and populated | Medium | Automated |
| U-012 | Data dictionary present and covers all fields | Medium | Automated |
| U-013 | Confidence tier matches metadata and data annotations | Medium | Manual |
| U-014 | License restrictions are not violated by intended use | Critical | Manual |
| U-015 | Privacy tier is correctly assigned and PII is handled appropriately | Critical | Manual (L4) |

### 4.3 Type-Specific Validation Rules (per dataset type)

These are defined in each dataset type's schema specification. Examples:

**For RS-MARRIAGE:**
- M-001: `marriage_date ≥ legal_minimum_age_by_country(birth_date)` — High
- M-002: `engagement_date ≤ marriage_date ≤ divorce_date` (if all present) — High
- M-003: `marriage_date ≤ death_date` (if deceased) — Critical

**For BM-CALC:**
- C-001: `abs(actual_value - expected_value) ≤ tolerance` — Critical
- C-002: `tolerance ≤ 0.001°` for angular calculations — High
- C-003: Expected value source is a valid, published, external reference — High

**For AI-HALLUC:**
- H-001: AI output does not contain any assertion from `known_hallucination_patterns` — Critical
- H-002: All factual assertions in AI output match ground_truth assertions — Critical

### 4.4 Validation Workflow

```
┌──────────────┐
│  Dataset      │
│  Submitted    │
└──────┬───────┘
       │
┌──────▼───────┐
│  L1: Schema   │─── Fail ──→ Return to curator with error report
│  Validation   │
└──────┬───────┘
       │ Pass
┌──────▼───────┐
│  L2: Quality  │─── Fail ──→ Flag limitations, may still proceed
│  Assessment   │              with documented caveats
└──────┬───────┘
       │ Pass / Partial
┌──────▼───────┐
│  L3: Audit   │─── Fail ──→ Downgrade to exploratory / return
│  (sampling)  │
└──────┬───────┘
       │ Pass
┌──────▼───────┐
│  L4: Review  │─── Fail ──→ Return with reviewer comments
│  (research   │
│   grade)     │
└──────┬───────┘
       │ Pass
┌──────▼───────┐
│  PROMOTED TO │
│  STABLE      │
└──────────────┘
```

### 4.5 Validation Report Template

```json
{
  "validation_id": "VAL-{DATASET-ID}-{YYYYMMDD}-{SEQ}",
  "dataset_id": "ASTRO-RF-SIGNS-v1.0.0",
  "validation_levels": ["L1", "L2", "L3", "L4"],
  "overall_result": "PASS",
  "per_level_results": [
    {
      "level": "L1",
      "result": "PASS",
      "checks_passed": 8,
      "checks_failed": 0,
      "errors": []
    },
    {
      "level": "L2",
      "result": "PASS_WITH_NOTES",
      "checks_passed": 15,
      "checks_failed": 0,
      "warnings": [
        {
          "rule": "U-013",
          "severity": "minor",
          "detail": "Signs.direction field is NULL for all records. Documented in known_limitations."
        }
      ]
    }
  ],
  "validated_by": "Curator Name / System",
  "validated_at": "2026-07-15T12:00:00Z",
  "next_review_date": "2027-07-15"
}
```

---

## 5. Documentation Templates

### 5.1 Catalog Entry Template

Every dataset has a `_catalog-entry.md` — a human-readable markdown file for the dataset catalog.

```markdown
# {dataset_id}: {name}

**Category:** {category} ({category_code})
**Type:** {type} ({type_code})
**Version:** {version}
**Status:** {lifecycle_stage}
**Quality Score:** {score} ({tier})

## Description

{description}

## Intended Use

{intended_use}

## Prohibited Uses

{prohibited_uses}

## Quick Stats

| Attribute | Value |
|-----------|-------|
| Records | {record_count} |
| Fields | {field_count} |
| Format | {format} |
| Size | {file_size_bytes} bytes |
| License | {license_name} |
| Privacy | {privacy_tier} |
| Confidence | {confidence_tier} |
| Provenance | {provenance_tier} |

## Data Dictionary

See `_data-dictionary.md`

## Known Limitations

{known_limitations}

## Update Schedule

{update_lifecycle_description}

## License

{license_name} ({license_id}). See {license_url} for full terms.

## Attribution

If you use this dataset, please cite:

```
{curator} ({published_at}). {name} v{version}. AstroOS Research Dataset Repository.
{dataset_id}
```

## Changelog

See `_changelog.md`
```

### 5.2 Data Dictionary Template

```markdown
# Data Dictionary: {dataset_id}

## Field Definitions

| # | Field Name | Type | Required | Description | Constraints | Example | Source |
|---|------------|------|----------|-------------|-------------|---------|--------|
| 1 | field_name | String | Yes | Purpose of this field | max 100 chars | "example" | Original |
| 2 | birth_date | Date | Yes | Subject's date of birth | ISO 8601, ≤ today | "1990-01-15" | User input |
| ... | ... | ... | ... | ... | ... | ... | ... |

## Enum Values

### field_name

| Value | Description |
|-------|-------------|
| val_1 | Description 1 |
| val_2 | Description 2 |

## Relationships

- `chart_id` references `birth_charts.id`
- `event_type` uses the AstroOS event classification taxonomy
```

### 5.3 Changelog Template

```markdown
# Changelog: {dataset_id}

## v1.1.0 (2026-12-15)

### Added
- New field `alternative_name` for cross-cultural identification
- 15 additional charts covering Southeast Asian birth records

### Changed
- Updated timezone offsets for 3 entries (IANA tzdata 2026g update)

### Fixed
- Corrected birth longitude for entry ASTRO-RS-COHORT-0042 (typo in source)

## v1.0.0 (2026-07-15)

### Added
- Initial stable release
- 1,247 verified birth charts
- 12 fields per record
```

---

## 6. File Structure & Naming Standards

### 6.1 Repository Root

```
datasets/
├── INDEX.md                         # Dataset catalog index (auto-generated)
├── LICENSE                          # Repository-level license
├── CONTRIBUTING.md                  # Dataset contribution guide
├── PRIVACY.md                       # Privacy handling policy
├── CITATION.cff                     # Preferred citation format
├── templates/                       # Templates for new datasets
│   ├── catalog-entry-template.md
│   ├── data-dictionary-template.md
│   ├── changelog-template.md
│   ├── metadata-template.json
│   └── quality-report-template.json
└── {category-code}/                 # One directory per category
    └── {type-code}/                 # One directory per type
        └── {dataset-id}/            # One directory per dataset version
            ├── {dataset-id}_{FORMAT}.{ext}
            ├── {dataset-id}_{FORMAT}_metadata.json
            ├── {dataset-id}_{FORMAT}_quality.json
            ├── {dataset-id}_catalog-entry.md
            ├── {dataset-id}_data-dictionary.md
            └── {dataset-id}_changelog.md
```

### 6.2 Allowed Formats

| Format | Extension | Primary Use Case | Compression |
|--------|-----------|-----------------|-------------|
| CSV | `.csv` | Universal tabular data, research export | `.gz` |
| JSON | `.json` | Metadata, schemas, small datasets | — |
| JSONL | `.jsonl` | Streaming large datasets, event logs | `.gz` |
| Parquet | `.parquet` | Columnar analytics, large research datasets | Built-in |
| Arrow | `.arrow` | Zero-copy columnar, high-performance analysis | — |
| SQL | `.sql` | PostgreSQL import scripts | `.gz` |

### 6.3 Format-Specific Standards

#### CSV

- **Delimiter**: Comma (`,`)
- **Header**: First row, always lowercase_snake_case
- **Quoting**: Double-quote all strings; escape internal quotes as `""`
- **Encoding**: UTF-8 (BOM optional)
- **Line endings**: LF (Unix) — convert CRLF on entry
- **Null representation**: Empty string (for strings), explicit `null` (for other types)
- **Boolean representation**: `true` / `false` (lowercase)
- **Date representation**: ISO 8601 (`2026-07-15`)
- **DateTime representation**: ISO 8601 with T separator and timezone (`2026-07-15T12:00:00Z`)
- **Decimal representation**: Dot separator, no grouping separators
- **Trailing commas**: Not allowed
- **Row limit**: 1,000,000 rows per file (split with `_partNN` suffix)

#### JSON

- **Structure**: Array of objects (list) or single object (metadata)
- **Field names**: lowercase_snake_case
- **Encoding**: UTF-8
- **Date format**: ISO 8601 strings
- **Indentation**: 2 spaces
- **Null handling**: `null` for missing/unknown values (omit only if truly optional)
- **No comments** in JSON files (use `_notes` field if needed)
- **Validate against**: JSON Schema (separate `.schema.json` file)

#### JSONL

- **One JSON object per line** (no outer array)
- **Every line** independently parseable
- **Same field conventions** as JSON
- **Trailing newline** after last record
- **Use for**: Append-only logs, streaming data, large datasets

#### Parquet

- **Version**: Parquet 2.6+
- **Compression**: ZSTD (default), Snappy (for compatibility)
- **Schema**: Defined in `.schema.json` alongside the file
- **Row group size**: 1,000,000 rows (default)
- **Page size**: 1 MB (default)
- **Statistics**: Column statistics enabled (min, max, null count)
- **Encoding**: PLAIN (default), RLE_DICTIONARY for low-cardinality strings

#### SQL (PostgreSQL Import)

- **Format**: `CREATE TABLE` + `INSERT INTO ... VALUES` or `\copy` format
- **Schema-qualified**: `astrosos.{table_name}` schema
- **Transaction-wrapped**: `BEGIN; ... COMMIT;`
- **Idempotent**: `DROP TABLE IF EXISTS` or `CREATE TABLE IF NOT EXISTS`
- **Encoding**: UTF-8

### 6.4 Git & Version Control

- **Large datasets** (>10 MB): Track with Git LFS
- **Parquet files**: Always Git LFS
- **Binary ephemeris files**: Always Git LFS
- **Metadata files**: Standard git (not LFS)
- **Commit messages**: `datasets({type-code}): {change description}` — e.g., `datasets(rf-signs): add direction field, seed migration v1.1.0`
- **Tags**: Git tags follow dataset version: `datasets/{dataset-id}` — e.g., `datasets/ASTRO-RF-SIGNS-v1.0.0`

---

## 7. Dataset Lifecycle Procedures

### 7.1 Lifecycle Stage Definitions

| Stage | Description | Storage | Discoverable | Usable |
|-------|-------------|---------|-------------|--------|
| **Draft** | Initial specification; no data or incomplete data | Repository root under `drafts/` | No (not indexed) | No |
| **Candidacy** | Data collected; under quality review | `datasets/{cat}/{type}/{id}/` | Yes (indexed) | Yes, with caveats |
| **Stable** | Quality validated; ready for use | `datasets/{cat}/{type}/{id}/` | Yes (featured) | Yes, full confidence |
| **Deprecated** | Superseded or withdrawn; still accessible | Same location, marked in metadata | Yes (demoted) | Not recommended |
| **Archived** | Historical only; read-only | `datasets/archived/{cat}/{type}/{id}/` | Yes (archive index) | Read-only, reproducibility |

### 7.2 Promotion Criteria

#### Draft → Candidacy

- [ ] Dataset specification complete (ID, schema, metadata defined)
- [ ] At least 1 record collected (demonstrates feasibility)
- [ ] L1 schema validation passes
- [ ] `_metadata.json` populated
- [ ] Basic `_data-dictionary.md` written
- [ ] Source provenance documented

#### Candidacy → Stable

- [ ] L2 quality validation passes (score ≥ 0.75)
- [ ] L3 statistical audit complete (for research datasets)
- [ ] Duplicate detection and resolution complete
- [ ] All known limitations documented
- [ ] Full `_data-dictionary.md` with all fields defined
- [ ] `_changelog.md` started
- [ ] License and privacy classification finalized
- [ ] Checksum verified
- [ ] Quality report generated

#### Stable → Deprecated

- [ ] Superseding dataset version exists (newer version with same ID)
- [ ] OR dataset is withdrawn for cause (license violation, privacy issue, data quality failure)
- [ ] `superseded_by` field populated in metadata
- [ ] Deprecation notice added to catalog entry
- [ ] Users notified (if user-facing)

#### Deprecated → Archived

- [ ] 6 months in Deprecated (standard) or immediate (for cause)
- [ ] No unresolved issues requiring active access
- [ ] All data moved to `datasets/archived/` tree
- [ ] Archive checksum verified

### 7.3 Emergency Procedures

**Privacy breach detected:**
1. Dataset immediately moved to Restricted access
2. Metadata `privacy_tier` updated to Restricted
3. Catalog entry hidden from public index
4. Incident documented in changelog
5. Re-anonymization or permanent archival within 72 hours

**Critical data error discovered:**
1. Dataset deprecated immediately
2. Correction released as new patch version
3. Errata published in catalog entry
4. All known consumers notified

---

## 8. Ethical & Legal Standards

### 8.1 Privacy Handling

| Privacy Tier | Data Examples | Storage | Access | Export | Retention |
|-------------|---------------|---------|--------|--------|-----------|
| **Public** | Planetary positions, sign tables | Unencrypted | Anyone | Unlimited | Permanent |
| **Anonymous** | De-identified chart records | Unencrypted | Anyone | Unlimited | Permanent |
| **Pseudonymous** | Public figure charts with stable ID | Unencrypted | Research registry | Attribution required | Permanent |
| **Private** | User charts, user events | Encrypted at rest | Owner only | User consent required | Per user preference |
| **Restricted** | Medical data, partner data | Encrypted + HSM | Named individuals | DPA required | Per agreement |

### 8.2 Anonymization Standards

**Minimum requirements for Anonymous tier:**
- Remove direct identifiers (name, email, phone, address, government IDs)
- Remove quasi-identifiers or generalize to safe thresholds:
  - Birth date: Keep only year (if population >1M in that year's birth cohort)
  - Birth place: Keep only country or region (if population >100K)
  - Occupation: Generalize to 1-digit ISCO category
- Apply k-anonymity (k ≥ 5): Each combination of quasi-identifiers must match ≥5 individuals
- Verify l-diversity (l ≥ 3): Each equivalence class has ≥3 distinct values for sensitive attributes

### 8.3 Licensing Classification

| License | Usage | Redistribution | Commercial Use | Attribution |
|---------|-------|---------------|---------------|-------------|
| **CC0-1.0** | Unlimited | Unlimited | Yes | Not required (recommended) |
| **CC-BY-4.0** | Unlimited | With attribution | Yes | Required |
| **CC-BY-SA-4.0** | Unlimited | Share-alike + attribution | Yes | Required |
| **CC-BY-NC-4.0** | Research only | With attribution | No | Required |
| **ODC-By** | Unlimited | With attribution | Yes | Required |
| **LicenseRef-AstroOS-Internal** | Internal use only | Not permitted | N/A | Internal only |
| **LicenseRef-AstroOS-Research** | Research use only | With permission | No | Required |
| **LicenseRef-SwissEphemeris** | Per Swiss Ephemeris terms | Per license | Depends | Required |
| **LicenseRef-Partner-Agreement** | Per DPA | Per agreement | Per agreement | Per agreement |

### 8.4 Dataset Contribution Ethics

All contributed datasets must:
1. **Not** contain knowingly false or fabricated data (synthetic datasets are exempt but must be labeled)
2. **Not** violate any applicable privacy law (GDPR, CCPA, HIPAA, etc.)
3. **Not** include data of minors without appropriate consent
4. **Not** re-publish data from copyrighted sources without permission
5. **Not** include data obtained through deception or without consent
6. **Disclose** any conflicts of interest in dataset curation
7. **Document** any known selection biases
8. **Provide** provenance information to the best of the curator's knowledge

---

## 9. Repository Directory Layout

```
datasets/                                    # Root
├── INDEX.md                                 # Auto-generated catalog
├── LICENSE
├── CONTRIBUTING.md
├── PRIVACY.md
├── CITATION.cff
├── templates/                               # Reusable templates
│   ├── catalog-entry-template.md
│   ├── data-dictionary-template.md
│   ├── changelog-template.md
│   ├── metadata-template.json
│   └── quality-report-template.json
├── schemas/                                 # Shared schemas
│   └── astroos-dataset-schema.json          # JSON Schema for _metadata.json
├── rf/                                      # Reference
│   ├── signs/
│   │   └── ASTRO-RF-SIGNS-v1.0.0/
│   └── nakshatras/
│       └── ASTRO-RF-NAK-v1.0.0/
├── rs/                                      # Research
│   ├── cohort/
│   ├── event/
│   ├── marriage/
│   ├── career/
│   ├── health/
│   ├── wealth/
│   └── flat/
├── bm/                                      # Benchmark
├── vl/                                      # Validation
├── qt/                                      # QA/Test
├── ai/                                      # AI Evaluation
├── sy/                                      # Synthetic
├── pb/                                      # Public
├── lc/                                      # Licensed
├── uc/                                      # User-Contributed
├── drafts/                                  # Datasets in Draft stage
└── archived/                                # Datasets in Archived stage
    ├── rf/
    ├── rs/
    └── ...
```

---

*End of Phase 3: Dataset Standards. Awaiting approval to proceed to Phase 4: Record Standards.*
