---
name: astrosos-record-standards
description: "Complete per-record metadata standards for the AstroOS Research Dataset Repository — chart records, event records, source tracking, confidence, privacy, research annotations"
metadata: 
  node_type: memory
  type: reference
  domain: datasets
  status: draft
  phase: 4
  originSessionId: e78a75e5-611c-4c3f-99a8-68817dfe9484
---

# AstroOS Record Standards — Phase 4

> **Status:** DRAFT — pending approval
> **Owner:** Chief Dataset & Research Curator
> **Version:** 1.0
> **Date:** 2026-07-15

---

## Table of Contents

1. [Record Identity Convention](#1-record-identity-convention)
2. [Record Envelope Schema](#2-record-envelope-schema)
3. [Chart Record Schema](#3-chart-record-schema)
4. [Event Record Schema](#4-event-record-schema)
5. [Person Metadata](#5-person-metadata)
6. [Source Tracking](#6-source-tracking)
7. [Confidence Annotations](#7-confidence-annotations)
8. [Privacy & Consent Metadata](#8-privacy--consent-metadata)
9. [Research Annotations](#9-research-annotations)
10. [Relationship Records](#10-relationship-records)
11. [Computation Metadata](#11-computation-metadata)
12. [Format-Specific Mapping](#12-format-specific-mapping)

---

## 1. Record Identity Convention

### 1.1 Record ID

Every record in the AstroOS Research Dataset Repository receives a unique, stable identifier:

```
ASTRO-REC-{DATASET-TYPE}-{SEQUENCE}
```

| Segment | Description |
|---------|-------------|
| `ASTRO` | Fixed prefix |
| `REC` | Fixed: Record |
| `DATASET-TYPE` | The type code from the dataset this record belongs to (e.g., WIKI, TWIN, MARRIAGE) |
| `SEQUENCE` | Zero-padded 6-digit sequence number within the dataset |

**Examples:**
- `ASTRO-REC-SIGNS-000001` — Sign reference record 1
- `ASTRO-REC-WIKI-000042` — Wikipedia chart record 42
- `ASTRO-REC-EVENT-001234` — Event record 1,234
- `ASTRO-REC-TWIN-000007` — Twin pair record 7

### 1.2 Record ID Rules

- Record IDs are **stable** — once assigned, they never change
- A corrected record gets a **new** Record ID; the old ID is deprecated and cross-referenced via `supersedes_record_id`
- Record IDs are **dataset-independent** — the same Record ID used across dataset versions refers to the same real-world entity
- Sequence numbers are zero-padded to 6 digits for readability (max 999,999 records per type)

### 1.3 External ID Mapping

Where the source data provides its own identifiers, they are preserved as `external_ids`:

```json
{
  "external_ids": [
    {"system": "wikidata", "id": "Q42"},
    {"system": "wikipedia", "id": "Douglas_Adams"},
    {"system": "doi", "id": "10.1234/example"}
  ]
}
```

---

## 2. Record Envelope Schema

Every record, regardless of dataset type, is wrapped in a **record envelope** — a consistent outer structure that carries metadata separate from domain data.

### 2.1 JSON Envelope

```json
{
  "$schema": "https://astrosos.local/datasets/schemas/record-envelope-v1.json",

  "_record_id": "ASTRO-REC-WIKI-000042",
  "_dataset_id": "ASTRO-PB-WIKI-v1.0.0",
  "_record_type": "chart",
  "_version": 1,
  "_created_at": "2026-07-15T12:00:00Z",
  "_updated_at": "2026-07-15T12:00:00Z",

  "_person": { ... },
  "_birth": { ... },
  "_source": { ... },
  "_confidence": { ... },
  "_privacy": { ... },
  "_research": { ... },
  "_computation": { ... },

  "data": { ... }
}
```

**Fields prefixed with `_` are metadata** — they describe the record itself, not the astrological data.

### 2.2 Envelope Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_record_id` | String | **[R]** | Permanent record ID |
| `_dataset_id` | String | **[R]** | Dataset ID this record belongs to |
| `_record_type` | String | **[R]** | `chart` / `event` / `person` / `relationship` / `synthetic` / `reference` |
| `_version` | Integer | **[R]** | Record version number (starts at 1, increments on correction) |
| `_created_at` | DateTime | **[R]** | ISO 8601 — when this record was created in the repository |
| `_updated_at` | DateTime | **[R]** | ISO 8601 — when this record was last modified |
| `_supersedes_record_id` | String | **[C]** | Record ID this version supersedes (null if original) |
| `_superseded_by_record_id` | String | **[C]** | Record ID that supersedes this (null if current) |
| `_is_deleted` | Boolean | **[R]** | Soft-delete flag (true = record no longer valid but retained for provenance) |
| `_person` | Object | **[C]** | Person metadata (§5) — required for chart/event records |
| `_birth` | Object | **[C]** | Birth data (§3) — required for chart records |
| `_source` | Object | **[R]** | Source tracking (§6) |
| `_confidence` | Object | **[C]** | Confidence annotations (§7) — required for records with any estimated/rectified/unknown data |
| `_privacy` | Object | **[R]** | Privacy & consent metadata (§8) |
| `_research` | Object | **[O]** | Research annotations (§9) |
| `_computation` | Object | **[C]** | Computation metadata (§11) — required for computed/derived records |
| `data` | Object | **[R]** | Domain-specific payload |

---

## 3. Chart Record Schema

The `_birth` section of the envelope carries all birth-related metadata. The `data` section carries the domain-specific payload (calculated positions, raw input, etc.).

### 3.1 `_birth` Metadata Object

```json
{
  "_birth": {
    "birth_date": "1990-01-15",
    "birth_date_accuracy": "exact",
    "birth_time": "14:30:00",
    "birth_time_accuracy": "exact",
    "birth_time_source": "birth_certificate",
    "birth_timezone": "Asia/Kolkata",
    "timezone_offset_minutes": 330,
    "timezone_source": "IANA tzdata 2026a",
    "timezone_verified": true,
    "birth_place": "Mumbai, Maharashtra, India",
    "birth_latitude": 19.0760,
    "birth_longitude": 72.8777,
    "birth_altitude_m": 14.0,
    "birth_place_source": "Wikipedia infobox / birth certificate",
    "country_code": "IN",
    "julian_day": 2447892.5,
    "julian_day_source": "Computed from birth_date/birth_time/timezone"
  }
}
```

### 3.2 Birth Date Accuracy

| Value | Description |
|-------|-------------|
| `exact` | Precise date known (day, month, year confirmed) |
| `estimated_day` | Day is estimated within a known month/year |
| `estimated_month` | Month is estimated within a known year |
| `estimated_year` | Only year is known |
| `unknown` | No reliable date information |

### 3.3 Birth Time Accuracy

| Value | Description |
|-------|-------------|
| `exact` | Time recorded from authoritative source (birth certificate, medical record) |
| `rounded` | Time given in rounded form (e.g., "morning", "8 pm" = ±30 min implied) |
| `estimated_window_lt_1h` | Time known within <1 hour window (e.g., family recollection) |
| `estimated_window_1h_4h` | Time known within 1–4 hour window |
| `estimated_window_gt_4h` | Time known only to part of day (morning/afternoon/night) |
| `unknown` | No birth time available (time fields null/marked unknown) |
| `rectified` | Time obtained through astrological rectification (see rectification metadata) |
| `rectified_verified` | Rectified time subsequently confirmed by independent source |

### 3.4 Birth Time Source

| Value | Description |
|-------|-------------|
| `birth_certificate` | Official birth certificate or civil registry |
| `medical_record` | Hospital birth record |
| `family_bible` | Family-recorded birth time |
| `biography` | Published biographical source |
| `obituary` | Obituary notice |
| `interview` | Interview with subject or family |
| `astrological_rectification` | Determined through astrological rectification |
| `government_record` | Census, passport, or other government record |
| `wikipedia_infobox` | Wikipedia infobox (may or may not cite original) |
| `unknown` | Source of birth time cannot be determined |
| `self_reported` | Subject self-reported the time |
| `estimated` | Best estimate from available information |

### 3.5 Birth Place Accuracy

| Value | Description |
|-------|-------------|
| `exact` | Precise location known (city/town + coordinates verified) |
| `city_only` | City/town known; exact coordinates uncertain |
| `region_only` | Only region/state known |
| `country_only` | Only country known |
| `unknown` | No reliable location |

### 3.6 Common Chart `data` Domain Payloads

The `data` section contains domain-specific information depending on the dataset type:

**For PB-WIKI (Wikipedia chart):**
```json
{
  "data": {
    "wikipedia_title": "Albert Einstein",
    "wikipedia_url": "https://en.wikipedia.org/wiki/Albert_Einstein",
    "wikidata_id": "Q937",
    "occupations": ["physicist", "mathematician"],
    "occupation_categories": ["science", "academia"],
    "notability_metrics": {
      "page_views_monthly": 2500000,
      "article_quality": "GA"
    },
    "death_date": "1955-04-18",
    "death_place": "Princeton, New Jersey, USA",
    "biography_summary": "Theoretical physicist who developed the theory of relativity..."
  }
}
```

**For RF-SIGNS (Reference sign):**
```json
{
  "data": {
    "sign_number": 1,
    "name": "aries",
    "sanskrit_name": "Mesha",
    "lord": "mars",
    "element": "fire",
    "modality": "cardinal",
    "gender": "male",
    "direction": "east",
    "start_degree": 0.0,
    "end_degree": 30.0
  }
}
```

**For RS-FLAT (Flattened chart record):**
```json
{
  "data": {
    "lagna": { "rashi": "leo", "degree": 12.3456 },
    "planets": {
      "sun": { "longitude": 120.4567, "rashi": "leo", "house": 1, "nakshatra": "magha", "pada": 3, "dignity": "own", "retrograde": false, "combust": false },
      "moon": { "longitude": 45.6789, "rashi": "taurus", "house": 8, "nakshatra": "rohini", "pada": 2, "dignity": "friendly", "retrograde": false, "combust": false }
    },
    "houses": [
      { "number": 1, "rashi": "leo", "cusp_degree": 150.5 },
      { "number": 2, "rashi": "virgo", "cusp_degree": 180.3 }
    ]
  }
}
```

---

## 4. Event Record Schema

For event datasets (RS-EVENT, RS-MARRIAGE, RS-CAREER, RS-HEALTH, RS-WEALTH, RS-SPIRITUAL), the `_record_type` is `event` and the `data` section carries event-specific payload.

### 4.1 Event Record Structure

```json
{
  "_record_id": "ASTRO-REC-MARRIAGE-000123",
  "_dataset_id": "ASTRO-RS-MARRIAGE-v1.0.0",
  "_record_type": "event",
  "_version": 1,
  "_person": {
    "chart_record_id": "ASTRO-REC-WIKI-000042",
    "person_name_display": "Person X (anonymous)"
  },
  "_birth": { ... },
  "_source": { ... },
  "_confidence": { ... },
  "_privacy": { ... },
  "_research": { ... },
  "data": {
    "event": {
      "event_type": "marriage",
      "event_category": "life_milestone",
      "event_date": "2015-06-20",
      "event_date_accuracy": "exact",
      "event_time": null,
      "event_place": "Mumbai, India",
      "title": "Marriage to Spouse Y",
      "description": "Traditional Hindu wedding ceremony"
    },
    "event_relations": [
      {"relation_type": "involves", "target_record_id": "ASTRO-REC-WIKI-000099", "description": "Spouse"}
    ],
    "event_dates_derived": {
      "engagement_date": "2014-12-15",
      "engagement_date_accuracy": "exact",
      "divorce_date": null,
      "divorce_date_accuracy": null
    },
    "marriage": {
      "marriage_number": 1,
      "cultural_tradition": "Hindu",
      "arranged_love": "love",
      "spouse_name_display": "Spouse Y (anonymous)",
      "spouse_birth_date": "1988-03-22",
      "spouse_birth_date_accuracy": "exact",
      "children_count": 2
    }
  }
}
```

### 4.2 Event Type Classification

```json
{
  "event_type": "marriage",
  "event_category": "life_milestone"
}
```

**Primary event types:**

| Event Type | Category | Example |
|------------|----------|---------|
| `marriage` | life_milestone | Wedding date |
| `career_start` | career | First job, business founding |
| `career_milestone` | career | Promotion, award, major achievement |
| `career_change` | career | Job change, industry switch |
| `education_start` | education | School/university admission |
| `education_completion` | education | Graduation, degree completion |
| `health_onset` | health | Disease diagnosis, injury |
| `health_recovery` | health | Recovery, remission |
| `health_decline` | health | Major health deterioration |
| `progeny_birth` | progeny | Birth of child |
| `progeny_adoption` | progeny | Adoption of child |
| `financial_gain` | wealth | Major wealth increase |
| `financial_loss` | wealth | Major wealth decrease |
| `financial_milestone` | wealth | First million, IPO, etc. |
| `spiritual_initiation` | spiritual | Initiation by guru |
| `spiritual_experience` | spiritual | Major spiritual experience |
| `relocation` | life_milestone | Major geographic move |
| `legal` | life_milestone | Major legal event (lawsuit, inheritance) |
| `death` | life_milestone | Date of death |
| `other` | other | Custom event (with `custom_type` field) |

### 4.3 Event Date Accuracy

Same schema as birth date accuracy:

| Value | Description |
|-------|-------------|
| `exact` | Precise date confirmed |
| `estimated_day` | Day estimated within month |
| `estimated_month` | Month estimated within year |
| `estimated_year` | Only year known |
| `unknown` | Date range unknown, event known to have occurred |
| `before_date` | Event known to have occurred before a certain date |
| `after_date` | Event known to have occurred after a certain date |

### 4.4 Linking Events to Charts

Events link to charts via the `chart_record_id` field in `_person`:

```json
{
  "_person": {
    "chart_record_id": "ASTRO-REC-WIKI-000042"
  }
}
```

For events involving multiple people (marriage, partnerships), additional record references go in `data.event_relations`:

```json
{
  "data": {
    "event_relations": [
      {"relation_type": "involves", "target_record_id": "ASTRO-REC-WIKI-000099", "description": "Spouse"},
      {"relation_type": "witnessed_by", "target_record_id": "ASTRO-REC-WIKI-000150", "description": "Witness"}
    ]
  }
}
```

---

## 5. Person Metadata

The `_person` section carries metadata about the individual whose chart or event is recorded.

### 5.1 Person Metadata Object

```json
{
  "_person": {
    "chart_record_id": "ASTRO-REC-WIKI-000042",
    "person_name_display": "Albert Einstein",
    "person_name_original_script": "אלברט איינשטיין",
    "gender": "male",
    "nationality": ["German", "Swiss", "American"],
    "known_for": ["Theory of relativity", "E=mc²"],
    "occupations": ["physicist", "mathematician", "scientist"],
    "occupation_categories": ["science", "academia", "nobel_laureate"],
    "birth_name": "Albert Einstein",
    "aliases": [],
    "is_public_figure": true,
    "notability_score": 0.99,
    "death_date": "1955-04-18",
    "death_date_accuracy": "exact",
    "death_place": "Princeton, New Jersey, USA",
    "death_cause": "abdominal_aortic_aneurysm",
    "biography_summary": "Theoretical physicist who developed the theory of relativity, one of the two pillars of modern physics."
  }
}
```

### 5.2 Person Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chart_record_id` | String | **[C]** | Record ID of the associated chart (required for event records) |
| `person_name_display` | String | **[R]** | Display name (real name for public figures, pseudonym for anonymous) |
| `person_name_original_script` | String | **[O]** | Name in original script (e.g., Devanagari, Arabic, Cyrillic) |
| `gender` | String | **[O]** | Gender identity |
| `nationality` | [String] | **[O]** | Nationalities held during lifetime |
| `known_for` | [String] | **[O]** | What the person is known for (for public figures) |
| `occupations` | [String] | **[O]** | Occupations during lifetime |
| `occupation_categories` | [String] | **[O]** | Standardized occupation categories |
| `birth_name` | String | **[O]** | Birth name (if different from display name) |
| `aliases` | [String] | **[O]** | Pen names, stage names, religious names |
| `is_public_figure` | Boolean | **[R]** | Is this person a public figure? |
| `notability_score` | Float | **[O]** | 0.0–1.0 notability metric (Wikipedia page views, citations, etc.) |
| `death_date` | Date | **[O]** | Date of death |
| `death_date_accuracy` | String | **[O]** | Accuracy of death date |
| `death_place` | String | **[O]** | Place of death |
| `death_cause` | String | **[O]** | Cause of death (generalized) |
| `biography_summary` | String | **[O]** | One-paragraph biography |

### 5.3 Anonymized Person Record

For anonymous records, the person section is minimized:

```json
{
  "_person": {
    "chart_record_id": "ASTRO-REC-COHORT-000512",
    "person_name_display": "Anonymous-000512",
    "gender": null,
    "is_public_figure": false,
    "occupation_categories": ["healthcare"]
  }
}
```

---

## 6. Source Tracking

The `_source` section tracks where every piece of data came from — per-record and per-field.

### 6.1 Source Object

```json
{
  "_source": {
    "primary_source": {
      "type": "wikipedia_infobox",
      "uri": "https://en.wikipedia.org/wiki/Albert_Einstein",
      "retrieved_at": "2026-07-10T12:00:00Z",
      "attribution": "Wikipedia contributors, 'Albert Einstein', Wikipedia, The Free Encyclopedia",
      "license": "CC-BY-SA-3.0"
    },
    "additional_sources": [
      {
        "type": "biography",
        "uri": "doi:10.1234/einstein-bio",
        "attribution": "Isaacson, W. (2007). Einstein: His Life and Universe.",
        "license": "Copyright"
      },
      {
        "type": "birth_certificate",
        "uri": null,
        "attribution": "Civil registry, Ulm, Germany (cited in Isaacson 2007)",
        "notes": "Original certificate not directly accessed; cited in secondary source"
      }
    ],
    "field_sources": {
      "birth_date": "primary_source",
      "birth_time": "primary_source",
      "birth_place": "primary_source",
      "birth_latitude": "geocoded_from_place",
      "birth_longitude": "geocoded_from_place",
      "timezone": "inferred_from_place"
    },
    "verification_status": "verified_multi_source",
    "last_verified_at": "2026-07-12T14:00:00Z",
    "verified_by": "Curator Name"
  }
}
```

### 6.2 Source Types

| Type | Description |
|------|-------------|
| `wikipedia_infobox` | Wikipedia article infobox |
| `wikidata` | Wikidata SPARQL query result |
| `biography` | Published biographical book |
| `birth_certificate` | Official birth certificate / civil registry |
| `medical_record` | Hospital or medical record |
| `government_record` | Census, passport, other government record |
| `obituary` | Newspaper or online obituary |
| `interview` | Interview transcript or recording |
| `genealogical_record` | Family tree, genealogical database |
| `astrological_rectification` | Determined by astrological rectification |
| `cross_platform_validation` | Verified against other astrology software |
| `research_study` | Published academic research study |
| `commercial_database` | Licensed commercial data provider |
| `user_submission` | Submitted by platform user |
| `generated` | Artificially generated (synthetic) |
| `geocoded` | Coordinates derived from place name |
| `inferred` | Inferred from related data |
| `unknown` | Source cannot be determined |

### 6.3 Verification Status

| Status | Description |
|--------|-------------|
| `unverified` | No verification attempted |
| `single_source` | Information from a single source; not independently verified |
| `verified_single_source` | Single authoritative source (e.g., birth certificate) |
| `verified_multi_source` | ≥2 independent sources agree |
| `verified_cross_platform` | Verified against external astrology software |
| `contradicted` | Sources disagree; lowest confidence selected |
| `estimated` | No source; best estimate from available information |
| `rectified` | Determined through astrological rectification |

### 6.4 Field-Source Mapping

The `field_sources` object maps each field to its source:

```json
{
  "field_sources": {
    "birth_date": "primary_source",
    "birth_time": "primary_source",
    "birth_latitude": "geocoded_from_place",
    "birth_longitude": "geocoded_from_place",
    "birth_altitude": "estimated_from_location",
    "timezone": "inferred_from_coordinates"
  }
}
```

Values reference either a key in `additional_sources` or a descriptive label.

---

## 7. Confidence Annotations

The `_confidence` section documents the certainty of each data element. Every record has an **overall confidence tier** and **per-field confidence** where applicable.

### 7.1 Confidence Object

```json
{
  "_confidence": {
    "overall_tier": "verified",
    "overall_notes": "Birth date and place verified against 3 independent sources. Birth time from biography citing birth certificate.",
    "field_confidence": {
      "birth_date": {
        "tier": "verified",
        "rationale": "Confirmed in Wikipedia infobox, biography (Isaacson 2007), and Wikidata."
      },
      "birth_time": {
        "tier": "estimated",
        "rationale": "Biography states 'born in the early morning hours' without precise time. Estimated 02:00 ± 2 hours."
      },
      "birth_place": {
        "tier": "verified",
        "rationale": "Consistent across all sources."
      },
      "birth_latitude": {
        "tier": "verified",
        "rationale": "Geocoded from verified birthplace; coordinates cross-checked against GeoNames."
      },
      "timezone": {
        "tier": "verified",
        "rationale": "IANA tzdata confirms timezone for this location at this date."
      }
    },
    "overall_confidence_score": 0.85,
    "confidence_score_breakdown": {
      "birth_date": 1.0,
      "birth_time": 0.4,
      "birth_place": 1.0,
      "coordinates": 0.95,
      "timezone": 1.0
    }
  }
}
```

### 7.2 Confidence Tiers (Per-Field)

| Tier | Score | Meaning | Color |
|------|-------|---------|-------|
| `verified` | 1.0 | Confirmed by ≥2 independent reliable sources | Green |
| `verified_single` | 0.9 | From one authoritative source (birth certificate, government record) | Green |
| `estimated_close` | 0.6 | Estimated within narrow bounds (±30 min for time, ±5 km for location) | Yellow |
| `estimated_wide` | 0.3 | Estimated within wide bounds (±4 hours for time, ±50 km for location) | Yellow |
| `rectified` | 0.5 | Determined through astrological rectification | Orange |
| `rectified_verified` | 0.8 | Rectified and subsequently confirmed by independent source | Orange |
| `synthetic` | 0.0 | Artificially generated — no real individual | Blue |
| `unknown` | 0.0 | No basis to assess | Gray |

### 7.3 Rectification Metadata

For rectified birth times, additional metadata is required:

```json
{
  "birth_time": {
    "tier": "rectified",
    "original_value": "unknown",
    "rectified_value": "14:30:00",
    "rectification_method": "event_based",
    "rectification_events_used": [
      {"event_type": "marriage", "event_date": "2015-06-20", "weight": "high"},
      {"event_type": "career_start", "event_date": "2010-01-15", "weight": "medium"}
    ],
    "rectification_software": "AstroOS Rectification Engine v1.0",
    "rectification_confidence": 0.65,
    "rectifier": "Curator Name / Automated",
    "rectified_at": "2026-07-14T10:00:00Z"
  }
}
```

---

## 8. Privacy & Consent Metadata

The `_privacy` section documents per-record privacy handling.

### 8.1 Privacy Object

```json
{
  "_privacy": {
    "record_privacy_tier": "public",
    "contains_pii": false,
    "pii_fields": [],
    "anonymization_applied": false,
    "anonymization_method": null,
    "anonymization_date": null,
    "original_identifiers_removed_at": null,
    "consent_status": "not_applicable",
    "consent_obtained_at": null,
    "consent_for_research": true,
    "consent_for_publication": true,
    "consent_withdrawn_at": null,
    "data_retention_limit": null,
    "ethical_approval_ref": null,
    "privacy_notes": "Public figure; data sourced from public biographical sources."
  }
}
```

### 8.2 Privacy Tiers (Per-Record)

| Tier | Description |
|------|-------------|
| `public` | Public figure, data from public sources |
| `anonymous` | De-identified — all direct and quasi-identifiers removed |
| `pseudonymous` | Direct identifiers removed; stable pseudonym retained for research linkage |
| `private` | Identifiable personal data — access restricted |
| `restricted` | Legally protected data — special handling required |

### 8.3 Consent Status

| Status | Description |
|--------|-------------|
| `not_applicable` | Public data, no consent needed |
| `obtained` | Explicit consent obtained |
| `implied` | Consent implied by platform terms of service |
| `withdrawn` | Consent withdrawn; data scheduled for removal |
| `pending` | Consent requested but not yet obtained |
| `not_obtained` | No consent (data not used for research) |

---

## 9. Research Annotations

The `_research` section carries optional research-oriented metadata.

### 9.1 Research Object

```json
{
  "_research": {
    "tags": ["nobel_laureate", "physics", "20th_century", "leo_ascendant"],
    "research_domains": ["career", "wealth", "longevity"],
    "cohort_memberships": [
      {"cohort_id": "ASTRO-RS-COHORT-nobel-laureates-v1.0.0", "label": "Nobel Laureates"},
      {"cohort_id": "ASTRO-RS-COHORT-20th-century-scientists-v1.0.0", "label": "20th Century Scientists"}
    ],
    "flags": {
      "has_verified_events": true,
      "has_multiple_events": true,
      "has_rectified_time": false,
      "is_twin": false,
      "has_family_data": false
    },
    "notability_metrics": {
      "wikipedia_pageviews_monthly": 2500000,
      "wikipedia_article_quality": "GA",
      "google_scholar_citations": null,
      "forbes_rank": null
    },
    "curator_notes": "Birth time estimated from biographical description 'born in the early morning hours'. Not precise enough for research requiring exact time."
  }
}
```

### 9.2 Tag Convention

- lowercase_snake_case
- Max 20 tags per record
- Standardized prefixes for categorization:
  - `era_*` — historical era (era_20th_century, era_renaissance)
  - `rashi_*` — lagna rashi (rashi_leo, rashi_virgo)
  - `profession_*` — occupation (profession_scientist, profession_artist)
  - `event_*` — event types (event_marriage, event_career)
  - `quality_*` — data quality flags (quality_verified, quality_estimated)

---

## 10. Relationship Records

Some datasets (PB-TWIN, family studies) require linking records together.

### 10.1 Relationship Record Type

```json
{
  "_record_id": "ASTRO-REC-TWIN-000007",
  "_dataset_id": "ASTRO-PB-TWIN-v1.0.0",
  "_record_type": "relationship",
  "data": {
    "relationship_type": "twin_pair",
    "twin_type": "identical",
    "relationship": {
      "type": "twin",
      "subtype": "identical",
      "members": [
        {"record_id": "ASTRO-REC-TWIN-000007A", "label": "Twin A", "birth_order": 1},
        {"record_id": "ASTRO-REC-TWIN-000007B", "label": "Twin B", "birth_order": 2}
      ],
      "birth_interval_minutes": 12,
      "birth_interval_accuracy": "exact",
      "shared_birth_data": {
        "birth_date": "1990-06-15",
        "birth_place": "London, UK",
        "birth_latitude": 51.5074,
        "birth_longitude": -0.1278
      }
    },
    "known_differences": {
      "sexual_orientation": "Twin A: heterosexual, Twin B: homosexual",
      "career": "Twin A: lawyer, Twin B: artist",
      "health_conditions": "Twin A: asthma, Twin B: none"
    }
  }
}
```

### 10.2 Relationship Types

| Type | Description |
|------|-------------|
| `twin_pair` | Twin siblings |
| `parent_child` | Parent-child relationship |
| `siblings` | Non-twin siblings |
| `spouse` | Marital/partnership relationship |
| `family_group` | Multi-member family group |
| `professional_network` | Professional relationship (mentor/protégé, collaborators) |

---

## 11. Computation Metadata

For computed/derived records (RS-FLAT, any record with calculated planetary positions), the `_computation` section documents how the data was produced.

### 11.1 Computation Object

```json
{
  "_computation": {
    "engine_version": "astrosos-engine-1.0.0",
    "computed_at": "2026-07-15T12:00:00Z",
    "computation_params": {
      "ayanamsa": "lahiri",
      "house_system": "whole_sign",
      "ephemeris": "swiss_ephemeris_18"
    },
    "engine_checksum": "sha256:a1b2c3d4...",
    "input_checksum": "sha256:e5f6g7h8...",
    "reproducibility_notes": "Recomputing with same engine version and params produces identical results."
  }
}
```

### 11.2 Computation Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `engine_version` | String | **[R]** | Version identifier of the calculation engine |
| `computed_at` | DateTime | **[R]** | When computation was performed |
| `computation_params` | Object | **[R]** | All parameters used (ayanamsa, house system, ephemeris) |
| `engine_checksum` | String | **[O]** | Checksum of the engine binary (for reproducibility) |
| `input_checksum` | String | **[O]** | Checksum of the input birth data (for reproducibility) |
| `reproducibility_notes` | String | **[O]** | Notes on what is needed to reproduce the computation |

---

## 12. Format-Specific Mapping

### 12.1 Flattened CSV Mapping

For CSV files, the nested record envelope is flattened using dot notation:

| CSV Column | Envelope Path | Required |
|------------|--------------|----------|
| `_record_id` | `_record_id` | Yes |
| `_dataset_id` | `_dataset_id` | Yes |
| `_record_type` | `_record_type` | Yes |
| `_version` | `_version` | Yes |
| `birth_date` | `_birth.birth_date` | Conditional |
| `birth_time` | `_birth.birth_time` | Conditional |
| `birth_time_accuracy` | `_birth.birth_time_accuracy` | Conditional |
| `birth_place` | `_birth.birth_place` | Conditional |
| `birth_latitude` | `_birth.birth_latitude` | Conditional |
| `birth_longitude` | `_birth.birth_longitude` | Conditional |
| `timezone` | `_birth.birth_timezone` | Conditional |
| `person_name_display` | `_person.person_name_display` | Conditional |
| `gender` | `_person.gender` | No |
| `occupations` | `_person.occupations` | No |
| `source_type` | `_source.primary_source.type` | Yes |
| `source_uri` | `_source.primary_source.uri` | Yes |
| `verification_status` | `_source.verification_status` | Yes |
| `confidence_tier` | `_confidence.overall_tier` | Yes |
| `privacy_tier` | `_privacy.record_privacy_tier` | Yes |
| `tags` | `_research.tags` | No |
| ... | ... | ... |

### 12.2 Parquet Schema Mapping

For Parquet files, the envelope maps to nested struct columns:

```
message RecordEnvelope {
  required binary _record_id (STRING);
  required binary _dataset_id (STRING);
  required binary _record_type (STRING);
  required int32 _version;
  optional group _birth {
    optional binary birth_date (STRING);
    optional binary birth_time (STRING);
    optional binary birth_time_accuracy (STRING);
    optional binary birth_place (STRING);
    optional double birth_latitude;
    optional double birth_longitude;
    ...
  }
  optional group _source {
    required binary primary_source_type (STRING);
    optional binary primary_source_uri (STRING);
    ...
  }
  ...
}
```

### 12.3 JSONL Line Format

Each line in a JSONL file is a complete record envelope:

```jsonl
{"_record_id":"ASTRO-REC-WIKI-000001","_dataset_id":"ASTRO-PB-WIKI-v1.0.0","_record_type":"chart","_version":1,"_birth":{"birth_date":"1879-03-14",...},"_person":{...},"_source":{...},"_confidence":{...},"_privacy":{...},"_research":{...},"data":{...}}
{"_record_id":"ASTRO-REC-WIKI-000002",...}
```

---

## 13. Record Standards Summary

| Component | Section | Purpose | Applicable To |
|-----------|---------|---------|---------------|
| Record ID | §1 | Stable unique identifier per record | All records |
| Record Envelope | §2 | Consistent outer wrapper with metadata/data separation | All records |
| Chart Birth Data | §3 | Birth date/time/place/timezone with accuracy annotations | Chart records |
| Chart Birth Accuracy | §3.2–3.5 | Standardized accuracy classification for date, time, place | Chart records |
| Event Data | §4 | Event type, date, accuracy, linking to chart records | Event records |
| Event Type Taxonomy | §4.2 | 20 standardized event types across 8 categories | Event records |
| Person Metadata | §5 | Name, gender, occupations, notability, biography | Person-associated records |
| Anonymized Person | §5.3 | Minimal person record for anonymous data | Anonymous records |
| Source Tracking | §6 | Per-record and per-field source citations, 14 source types | All records |
| Verification Status | §6.3 | 7-level verification classification | All records |
| Field-Source Mapping | §6.4 | Map each field to its source | Conditional |
| Confidence Annotations | §7 | Per-field confidence tiers with rationale, scores, rectification metadata | All records with estimated/rectified data |
| Confidence Tiers | §7.2 | 8-level per-field confidence with numeric scores | Conditional |
| Rectification Metadata | §7.3 | Method, events used, confidence, rectifier attribution | Rectified records |
| Privacy & Consent | §8 | Per-record privacy tier, PII flags, consent status, retention limits | All records |
| Research Annotations | §9 | Tags, cohort memberships, flags, notability metrics, curator notes | Research-eligible records |
| Tag Convention | §9.2 | Standardized prefix taxonomy for tags | Research annotations |
| Relationship Records | §10 | Twin pairs, family groups, professional networks | Relationship datasets |
| Computation Metadata | §11 | Engine version, parameters, checksums, reproducibility notes | Computed/derived records |
| Format-Specific Mapping | §12 | CSV flat column mapping, Parquet schema, JSONL line format | All format exports |

---

*End of Phase 4: Record Standards. Awaiting approval to proceed to Phase 5: Dataset Quality.*
