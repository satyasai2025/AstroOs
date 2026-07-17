---
name: astrosos-standard-formats
description: "Canonical data formats for the AstroOS Research Dataset Repository — unified schema with CSV, JSON, JSONL, Parquet, SQL, and research export mappings"
metadata: 
  node_type: memory
  type: reference
  domain: datasets
  status: draft
  phase: 6
  originSessionId: e78a75e5-611c-4c3f-99a8-68817dfe9484
---

# AstroOS Standard Formats — Phase 6

> **Status:** DRAFT — pending approval
> **Owner:** Chief Dataset & Research Curator
> **Version:** 1.0
> **Date:** 2026-07-15

---

## Table of Contents

1. [Unified Data Model](#1-unified-data-model)
2. [CSV Schema & Specification](#2-csv-schema--specification)
3. [JSON Schema & Specification](#3-json-schema--specification)
4. [JSONL Schema & Specification](#4-jsonl-schema--specification)
5. [Parquet Schema & Specification](#5-parquet-schema--specification)
6. [PostgreSQL Import Schema](#6-postgresql-import-schema)
7. [Research Export Format](#7-research-export-format)
8. [Cross-Format Consistency](#8-cross-format-consistency)

---

## 1. Unified Data Model

### 1.1 Conceptual Schema

Every record across every format is an instance of this unified data model:

```
Record
├── _record_id: String [PK]          # Permanent unique record ID
├── _dataset_id: String               # Source dataset ID
├── _record_type: Enum                # chart | event | person | relationship | synthetic | reference
├── _version: Integer                 # Record version
├── _created_at: DateTime             # When record was created in repo
├── _updated_at: DateTime             # When record was last modified
│
├── _person                           # Person metadata (see §1.1.1)
├── _birth                            # Birth data (see §1.1.2)
├── _source                           # Source tracking (see §1.1.3)
├── _confidence                       # Confidence annotations (see §1.1.4)
├── _privacy                          # Privacy metadata (see §1.1.5)
├── _research                         # Research annotations (see §1.1.6)
├── _computation                      # Computation metadata (see §1.1.7)
│
├── data                              # Domain-specific payload
├── data.event                        # For event-type records
├── data.planets[]                    # For chart-type records (computed)
├── data.houses[]                     # For chart-type records (computed)
└── data.{domain_specific}            # For reference/synthetic/other records
```

### 1.1.1 Person Sub-Schema

```
_person
├── chart_record_id: String?          # Link to associated chart record
├── person_name_display: String       # Display name (real or pseudonym)
├── person_name_original_script: String?
├── gender: String?
├── nationality: String[]?
├── known_for: String[]?
├── occupations: String[]?
├── occupation_categories: String[]?
├── birth_name: String?
├── aliases: String[]?
├── is_public_figure: Boolean         # True for public figures
├── notability_score: Float?          # 0.0–1.0
├── death_date: Date?
├── death_date_accuracy: Enum?
├── death_place: String?
├── death_cause: String?
├── biography_summary: String?
```

### 1.1.2 Birth Sub-Schema

```
_birth
├── birth_date: Date                  # ISO 8601 date
├── birth_date_accuracy: Enum         # exact | estimated_day | estimated_month | estimated_year | unknown
├── birth_time: Time?                 # HH:MM:SS in local time
├── birth_time_accuracy: Enum?        # exact | rounded | estimated_window_* | unknown | rectified | rectified_verified
├── birth_time_source: Enum?          # birth_certificate | medical_record | biography | wikipedia_infobox | etc.
├── birth_timezone: String?           # IANA timezone ID
├── timezone_offset_minutes: Int?     # Offset from UTC in minutes
├── timezone_source: String?          # Source of timezone assignment
├── timezone_verified: Boolean        # Was timezone manually verified?
├── birth_place: String?              # Place name (city, region, country)
├── birth_latitude: Decimal?          # WGS84, in degrees
├── birth_longitude: Decimal?         # WGS84, in degrees
├── birth_altitude_m: Decimal?        # Meters above sea level
├── birth_place_accuracy: Enum?       # exact | city_only | region_only | country_only | unknown
├── birth_place_source: String?       # How place was determined
├── country_code: String?             # ISO 3166-1 alpha-2
├── julian_day: Decimal?              # JD for the birth moment (UTC)
├── julian_day_source: String?        # How JD was computed
```

### 1.1.3 Source Sub-Schema

```
_source
├── primary_source: Object
│   ├── type: Enum                    # 14 source types (see Phase 4 §6.2)
│   ├── uri: String?                  # URL, DOI, or reference
│   ├── retrieved_at: DateTime?
│   ├── attribution: String?          # Citation text
│   ├── license: String?              # SPDX or custom
│   └── notes: String?
├── additional_sources: Object[]?
├── field_sources: Object?            # Per-field source mapping
│   ├── {field_name}: String          # Reference to source or label
│   └── ...
├── verification_status: Enum         # 7 levels (see Phase 4 §6.3)
├── last_verified_at: DateTime?
├── verified_by: String?
```

### 1.1.4 Confidence Sub-Schema

```
_confidence
├── overall_tier: Enum                # verified | estimated | rectified | synthetic | unknown
├── overall_notes: String?
├── overall_confidence_score: Float?  # 0.0–1.0
├── field_confidence: Object?         # Per-field confidence
│   ├── {field_name}: Object
│   │   ├── tier: Enum               # 8 levels (see Phase 4 §7.2)
│   │   ├── score: Float             # 0.0–1.0
│   │   └── rationale: String
│   └── ...
├── rectification: Object?            # Required if any field tier = rectified
│   ├── original_value: String?
│   ├── rectified_value: String
│   ├── method: String
│   ├── events_used: Object[]
│   ├── software: String?
│   ├── confidence: Float
│   ├── rectifier: String
│   └── rectified_at: DateTime
```

### 1.1.5 Privacy Sub-Schema

```
_privacy
├── record_privacy_tier: Enum         # public | anonymous | pseudonymous | private | restricted
├── contains_pii: Boolean
├── pii_fields: String[]
├── anonymization_applied: Boolean
├── anonymization_method: String?
├── consent_status: Enum              # not_applicable | obtained | implied | withdrawn | pending | not_obtained
├── consent_for_research: Boolean
├── consent_for_publication: Boolean
├── data_retention_limit: Date?
├── ethical_approval_ref: String?
└── privacy_notes: String?
```

### 1.1.6 Research Sub-Schema

```
_research
├── tags: String[]?                   # lowercase_snake_case, max 20
├── research_domains: String[]?
├── cohort_memberships: Object[]?
│   ├── cohort_id: String
│   ├── label: String
│   └── ...
├── flags: Object?
│   ├── has_verified_events: Boolean
│   ├── has_rectified_time: Boolean
│   ├── is_twin: Boolean
│   └── ...
├── notability_metrics: Object?
├── curator_notes: String?
```

### 1.1.7 Computation Sub-Schema

```
_computation
├── engine_version: String            # AstroOS engine version
├── computed_at: DateTime             # When computation ran
├── computation_params: Object
│   ├── ayanamsa: String
│   ├── house_system: String
│   ├── ephemeris: String
│   └── ...
├── engine_checksum: String?
├── input_checksum: String?
└── reproducibility_notes: String?
```

### 1.1.8 Domain Data Sub-Schema (chart-type)

For chart records with computed data:

```
data (chart-type record)
├── lagna: Object?
│   ├── longitude: Float
│   ├── sidereal_longitude: Float
│   ├── rashi: String
│   ├── rashi_degree: Float
│   ├── nakshatra: String
│   └── pada: Integer
├── planets: Object[]
│   ├── planet: String                # Graha name
│   ├── longitude: Float
│   ├── sidereal_longitude: Float
│   ├── rashi: String
│   ├── rashi_degree: Float
│   ├── house_number: Integer
│   ├── nakshatra: String?
│   ├── pada: Integer?
│   ├── is_retrograde: Boolean
│   ├── is_combust: Boolean
│   ├── dignity: String?
│   └── shadbala_score: Float?
├── houses: Object[]
│   ├── house_number: Integer
│   ├── rashi: String
│   ├── cusp_degree: Float
│   └── mid_degree: Float?
├── aspects: Object[]?
│   ├── from_planet: String
│   ├── to_planet: String
│   ├── aspect_type: String
│   ├── orb_degrees: Float
│   └── is_applying: Boolean
├── panchanga: Object?
├── divisional_placements: Object[]?
└── dashas: Object[]?
```

---

## 2. CSV Schema & Specification

### 2.1 CSV Format Rules

| Rule | Specification |
|------|---------------|
| Delimiter | Comma (`,`), never semicolon or tab |
| Header | First row, always lowercase_snake_case |
| String quoting | Double-quote all strings; escape `"` as `""` |
| Encoding | UTF-8 without BOM |
| Line endings | LF (Unix `\n`) |
| Null representation | Empty string for strings; `null` for numeric, date, boolean |
| Boolean format | `true` / `false` (lowercase) |
| Date format | ISO 8601: `2026-07-15` |
| DateTime format | ISO 8601 with T and Z: `2026-07-15T12:00:00Z` |
| Decimal format | Dot separator: `19.0760` |
| Thousands separator | Never |
| Trailing comma | Not allowed |
| Empty lines | Not allowed |
| Max row limit | 1,000,000 rows per file (split with `_partNN` suffix) |
| Row limit for research | Unlimited for Parquet; capped for CSV |

### 2.2 Universal CSV Column Specification

The following columns appear in EVERY CSV dataset. They map to the record envelope.

| # | Column | Type | Required | Description | Envelope Path |
|---|--------|------|----------|-------------|---------------|
| 1 | `_record_id` | String | Yes | Permanent record ID | `_record_id` |
| 2 | `_dataset_id` | String | Yes | Source dataset ID | `_dataset_id` |
| 3 | `_record_type` | String | Yes | Record type | `_record_type` |
| 4 | `_version` | Integer | Yes | Record version | `_version` |
| 5 | `_created_at` | DateTime | Yes | Record creation timestamp | `_created_at` |
| 6 | `_updated_at` | DateTime | Yes | Record modification timestamp | `_updated_at` |
| 7 | `_is_deleted` | Boolean | Yes | Soft-delete flag | `_is_deleted` |

### 2.3 Birth Data Columns

| # | Column | Type | Required | Envelope Path |
|---|--------|------|----------|---------------|
| 8 | `birth_date` | Date | Conditional | `_birth.birth_date` |
| 9 | `birth_date_accuracy` | String | Conditional | `_birth.birth_date_accuracy` |
| 10 | `birth_time` | String | Conditional | `_birth.birth_time` |
| 11 | `birth_time_accuracy` | String | Conditional | `_birth.birth_time_accuracy` |
| 12 | `birth_time_source` | String | Conditional | `_birth.birth_time_source` |
| 13 | `birth_timezone` | String | Conditional | `_birth.birth_timezone` |
| 14 | `timezone_offset_minutes` | Integer | Conditional | `_birth.timezone_offset_minutes` |
| 15 | `birth_place` | String | Conditional | `_birth.birth_place` |
| 16 | `birth_latitude` | Decimal | Conditional | `_birth.birth_latitude` |
| 17 | `birth_longitude` | Decimal | Conditional | `_birth.birth_longitude` |
| 18 | `birth_altitude_m` | Decimal | No | `_birth.birth_altitude_m` |
| 19 | `birth_place_accuracy` | String | Conditional | `_birth.birth_place_accuracy` |
| 20 | `country_code` | String | No | `_birth.country_code` |

### 2.4 Person Columns

| # | Column | Type | Required | Envelope Path |
|---|--------|------|----------|---------------|
| 21 | `person_name_display` | String | Conditional | `_person.person_name_display` |
| 22 | `gender` | String | No | `_person.gender` |
| 23 | `is_public_figure` | Boolean | Conditional | `_person.is_public_figure` |
| 24 | `occupation_categories` | String | No | `_person.occupation_categories` (pipe-joined) |
| 25 | `nationality` | String | No | `_person.nationality` (pipe-joined) |
| 26 | `death_date` | Date | No | `_person.death_date` |
| 27 | `death_place` | String | No | `_person.death_place` |

### 2.5 Source Columns

| # | Column | Type | Required | Envelope Path |
|---|--------|------|----------|---------------|
| 28 | `source_type` | String | Yes | `_source.primary_source.type` |
| 29 | `source_uri` | String | No | `_source.primary_source.uri` |
| 30 | `source_attribution` | String | No | `_source.primary_source.attribution` |
| 31 | `verification_status` | String | Yes | `_source.verification_status` |
| 32 | `last_verified_at` | DateTime | No | `_source.last_verified_at` |

### 2.6 Confidence Columns

| # | Column | Type | Required | Envelope Path |
|---|--------|------|----------|---------------|
| 33 | `confidence_overall_tier` | String | Yes | `_confidence.overall_tier` |
| 34 | `confidence_overall_score` | Decimal | No | `_confidence.overall_confidence_score` |
| 35 | `confidence_notes` | String | No | `_confidence.overall_notes` |

### 2.7 Privacy & Research Columns

| # | Column | Type | Required | Envelope Path |
|---|--------|------|----------|---------------|
| 36 | `privacy_tier` | String | Yes | `_privacy.record_privacy_tier` |
| 37 | `consent_status` | String | Conditional | `_privacy.consent_status` |
| 38 | `tags` | String | No | `_research.tags` (pipe-joined) |
| 39 | `research_domains` | String | No | `_research.research_domains` (pipe-joined) |
| 40 | `curator_notes` | String | No | `_research.curator_notes` |

### 2.8 Dataset-Specific Columns

Following the universal columns (1-40), each dataset appends its domain-specific columns. These are defined in the dataset's data dictionary.

**Example: PB-WIKI additions**

| # | Column | Type | Required | Description |
|---|--------|------|----------|-------------|
| 41 | `wikipedia_title` | String | Yes | Wikipedia article title |
| 42 | `wikidata_id` | String | Yes | Wikidata ID (Q identifier) |
| 43 | `occupations` | String | No | Pipe-joined list of occupations |
| 44 | `wikipedia_page_views` | Integer | No | Monthly page views |

**Example: RS-EVENT additions**

| # | Column | Type | Required | Description |
|---|--------|------|----------|-------------|
| 41 | `chart_record_id` | String | Yes | Chart record ID this event belongs to |
| 42 | `event_date` | Date | Yes | Event date |
| 43 | `event_date_accuracy` | String | Yes | Accuracy of event date |
| 44 | `event_type` | String | Yes | Event type classification |
| 45 | `event_category` | String | Yes | Event category |
| 46 | `title` | String | Yes | Event title |
| 47 | `description` | String | No | Event description |

### 2.9 Array Flattening in CSV

For array fields, the following flattening rules apply:

| Array Field | CSV Representation | Separator |
|-------------|-------------------|-----------|
| `occupations` | Single column with joined values | Pipe `\|` |
| `tags` | Single column with joined values | Pipe `\|` |
| `nationality` | Single column with joined values | Pipe `\|` |
| Multiple planets | One row per planet (repeating other fields) | Row expansion (see §2.10) |

### 2.10 Row Expansion for One-to-Many Data

When a record has one-to-many relationships (e.g., a chart has 9 planets), CSVs use row expansion:

**Method:** The parent record fields are repeated once per child row, with child-specific columns differentiating the rows.

```
_record_id, _dataset_id, ..., birth_date, planet_name, planet_longitude, planet_rashi, ...
ASTRO-REC-..., ..., 1990-01-15, sun, 120.4567, leo, ...
ASTRO-REC-..., ..., 1990-01-15, moon, 45.6789, taurus, ...
ASTRO-REC-..., ..., 1990-01-15, mars, 200.1234, libra, ...
```

**Row expansion is only used when:** The same dataset is also available in a non-expanded format (Parquet, JSON, JSONL). CSV is the interchange format; Parquet is the analysis format.

---

## 3. JSON Schema & Specification

### 3.1 JSON Format Rules

| Rule | Specification |
|------|---------------|
| Structure | Array of objects (list) for data files; single object for metadata |
| Field names | lowercase_snake_case (matching envelope paths exactly) |
| Encoding | UTF-8 without BOM |
| Null handling | `null` for missing/unknown (omit only for truly optional fields) |
| Date format | ISO 8601 string: `"2026-07-15"` |
| DateTime format | ISO 8601 with T and Z: `"2026-07-15T12:00:00Z"` |
| Indentation | 2 spaces |
| Trailing comma | Not allowed |
| File extension | `.json` |
| Array representation | Native JSON arrays |
| Boolean representation | `true` / `false` (JSON native) |

### 3.2 JSON Schema Reference

The JSON schema mirrors the envelope structure exactly:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://astrosos.local/datasets/schemas/record-v1.json",
  "title": "AstroOS Dataset Record",
  "type": "object",
  "required": [
    "_record_id", "_dataset_id", "_record_type", "_version",
    "_created_at", "_updated_at", "_is_deleted",
    "_source", "_privacy", "data"
  ],
  "properties": {
    "_record_id": {
      "type": "string",
      "pattern": "^ASTRO-REC-[A-Z]+-[0-9]{6}$"
    },
    "_dataset_id": {
      "type": "string",
      "pattern": "^ASTRO-[A-Z]{2}-[A-Z]+-v[0-9]+\\.[0-9]+\\.[0-9]+$"
    },
    "_record_type": {
      "type": "string",
      "enum": ["chart", "event", "person", "relationship", "synthetic", "reference"]
    },
    "_version": { "type": "integer", "minimum": 1 },
    "_created_at": { "type": "string", "format": "date-time" },
    "_updated_at": { "type": "string", "format": "date-time" },
    "_supersedes_record_id": { "type": "string" },
    "_superseded_by_record_id": { "type": "string" },
    "_is_deleted": { "type": "boolean", "default": false },

    "_person": { "$ref": "#/$defs/Person" },
    "_birth": { "$ref": "#/$defs/Birth" },
    "_source": { "$ref": "#/$defs/Source" },
    "_confidence": { "$ref": "#/$defs/Confidence" },
    "_privacy": { "$ref": "#/$defs/Privacy" },
    "_research": { "$ref": "#/$defs/Research" },
    "_computation": { "$ref": "#/$defs/Computation" },

    "data": {
      "type": "object",
      "properties": {
        "lagna": { "$ref": "#/$defs/Lagna" },
        "planets": {
          "type": "array",
          "items": { "$ref": "#/$defs/PlanetPosition" }
        },
        "houses": {
          "type": "array",
          "items": { "$ref": "#/$defs/House" }
        },
        "event": { "$ref": "#/$defs/Event" }
      }
    }
  },

  "$defs": {
    "Person": {
      "type": "object",
      "properties": {
        "chart_record_id": { "type": "string" },
        "person_name_display": { "type": "string" },
        "gender": { "type": "string" },
        "is_public_figure": { "type": "boolean" },
        "occupations": { "type": "array", "items": { "type": "string" } },
        "death_date": { "type": "string", "format": "date" }
      }
    },
    "Birth": {
      "type": "object",
      "properties": {
        "birth_date": { "type": "string", "format": "date" },
        "birth_date_accuracy": { "type": "string", "enum": ["exact", "estimated_day", "estimated_month", "estimated_year", "unknown"] },
        "birth_time": { "type": "string" },
        "birth_time_accuracy": { "type": "string" },
        "birth_timezone": { "type": "string" },
        "birth_latitude": { "type": "number" },
        "birth_longitude": { "type": "number" },
        "birth_place": { "type": "string" },
        "country_code": { "type": "string" }
      }
    },
    "Source": {
      "type": "object",
      "required": ["primary_source", "verification_status"],
      "properties": {
        "primary_source": {
          "type": "object",
          "required": ["type"],
          "properties": {
            "type": { "type": "string" },
            "uri": { "type": "string", "format": "uri" },
            "attribution": { "type": "string" },
            "license": { "type": "string" }
          }
        },
        "additional_sources": { "type": "array", "items": { "type": "object" } },
        "verification_status": { "type": "string" }
      }
    },
    "Confidence": {
      "type": "object",
      "properties": {
        "overall_tier": { "type": "string" },
        "overall_notes": { "type": "string" },
        "field_confidence": { "type": "object" }
      }
    },
    "Privacy": {
      "type": "object",
      "required": ["record_privacy_tier"],
      "properties": {
        "record_privacy_tier": { "type": "string", "enum": ["public", "anonymous", "pseudonymous", "private", "restricted"] },
        "contains_pii": { "type": "boolean" },
        "consent_status": { "type": "string" }
      }
    },
    "Research": {
      "type": "object",
      "properties": {
        "tags": { "type": "array", "items": { "type": "string" } },
        "research_domains": { "type": "array", "items": { "type": "string" } },
        "curator_notes": { "type": "string" }
      }
    },
    "Computation": {
      "type": "object",
      "properties": {
        "engine_version": { "type": "string" },
        "computed_at": { "type": "string", "format": "date-time" },
        "computation_params": { "type": "object" }
      }
    },
    "Lagna": {
      "type": "object",
      "properties": {
        "longitude": { "type": "number" },
        "rashi": { "type": "string" },
        "rashi_degree": { "type": "number" },
        "nakshatra": { "type": "string" },
        "pada": { "type": "integer" }
      }
    },
    "PlanetPosition": {
      "type": "object",
      "properties": {
        "planet": { "type": "string" },
        "sidereal_longitude": { "type": "number" },
        "rashi": { "type": "string" },
        "rashi_degree": { "type": "number" },
        "house_number": { "type": "integer" },
        "nakshatra": { "type": "string" },
        "pada": { "type": "integer" },
        "is_retrograde": { "type": "boolean" },
        "dignity": { "type": "string" }
      }
    },
    "House": {
      "type": "object",
      "properties": {
        "house_number": { "type": "integer" },
        "rashi": { "type": "string" },
        "cusp_degree": { "type": "number" }
      }
    },
    "Event": {
      "type": "object",
      "properties": {
        "event_type": { "type": "string" },
        "event_category": { "type": "string" },
        "event_date": { "type": "string", "format": "date" },
        "event_date_accuracy": { "type": "string" },
        "title": { "type": "string" },
        "description": { "type": "string" }
      }
    }
  }
}
```

### 3.3 Example JSON Record (chart-type)

```json
{
  "_record_id": "ASTRO-REC-WIKI-000042",
  "_dataset_id": "ASTRO-PB-WIKI-v1.0.0",
  "_record_type": "chart",
  "_version": 1,
  "_created_at": "2026-07-15T12:00:00Z",
  "_updated_at": "2026-07-15T12:00:00Z",
  "_is_deleted": false,

  "_person": {
    "chart_record_id": null,
    "person_name_display": "Ada Lovelace",
    "gender": "female",
    "is_public_figure": true,
    "occupations": ["mathematician", "writer"],
    "occupation_categories": ["science", "computing"],
    "death_date": "1852-11-27",
    "death_place": "Marylebone, London, UK"
  },

  "_birth": {
    "birth_date": "1815-12-10",
    "birth_date_accuracy": "exact",
    "birth_time": null,
    "birth_time_accuracy": "unknown",
    "birth_timezone": "Europe/London",
    "timezone_offset_minutes": 0,
    "birth_place": "London, England, UK",
    "birth_latitude": 51.5074,
    "birth_longitude": -0.1278,
    "country_code": "GB",
    "birth_place_accuracy": "exact"
  },

  "_source": {
    "primary_source": {
      "type": "wikipedia_infobox",
      "uri": "https://en.wikipedia.org/wiki/Ada_Lovelace",
      "attribution": "Wikipedia contributors, 'Ada Lovelace', Wikipedia, The Free Encyclopedia",
      "license": "CC-BY-SA-3.0"
    },
    "verification_status": "verified_multi_source",
    "last_verified_at": "2026-07-12T14:00:00Z"
  },

  "_confidence": {
    "overall_tier": "verified",
    "overall_confidence_score": 0.92,
    "field_confidence": {
      "birth_date": { "tier": "verified", "score": 1.0, "rationale": "Confirmed in Wikipedia, multiple biographies" },
      "birth_time": { "tier": "unknown", "score": 0.0, "rationale": "Birth time not recorded in any known source" },
      "birth_place": { "tier": "verified", "score": 1.0, "rationale": "Consistent across all sources" }
    }
  },

  "_privacy": {
    "record_privacy_tier": "public",
    "contains_pii": false,
    "consent_status": "not_applicable"
  },

  "_research": {
    "tags": ["computing", "19th_century", "mathematics", "female_pioneer"],
    "research_domains": ["career", "health", "longevity"],
    "curator_notes": "Birth time not recorded. Only date and place known."
  },

  "data": {
    "wikipedia_title": "Ada Lovelace",
    "wikidata_id": "Q7259",
    "occupations": ["mathematician", "writer"]
  }
}
```

---

## 4. JSONL Schema & Specification

### 4.1 JSONL Format Rules

| Rule | Specification |
|------|---------------|
| Structure | One JSON object per line (no outer array) |
| Schema | Identical to JSON schema (§3) — each line is a valid JSON record |
| Line encoding | UTF-8 |
| Line terminator | LF (Unix `\n`) |
| Trailing newline | Required after the last record |
| Max line length | No limit, but recommend <1 MB per line for practical parsing |
| Null handling | Same as JSON |
| File extension | `.jsonl` |
| Compression | `.jsonl.gz` for large files |

### 4.2 JSONL Example

```jsonl
{"_record_id":"ASTRO-REC-WIKI-000001","_dataset_id":"ASTRO-PB-WIKI-v1.0.0","_record_type":"chart","_version":1,"_birth":{"birth_date":"1815-12-10", ...}}
{"_record_id":"ASTRO-REC-WIKI-000002","_dataset_id":"ASTRO-PB-WIKI-v1.0.0","_record_type":"chart","_version":1,"_birth":{"birth_date":"1879-03-14", ...}}
```

### 4.3 When to Use JSONL vs JSON

| Characteristic | JSON | JSONL |
|---------------|------|-------|
| File size | Small to medium (<100K records) | Large (100K+) |
| Streaming | Requires full parse | Line-by-line streaming |
| Human readability | Formatted with indentation | Each line dense |
| Parallel processing | Cannot split | Can split by line boundaries |
| Append | Requires full rewrite | Append single line |
| Parsing in Python | `json.load(f)` | `for line in f: json.loads(line)` |
| Parsing in R | `jsonlite::fromJSON()` | `jsonlite::stream_in()` |

---

## 5. Parquet Schema & Specification

### 5.1 Parquet Format Rules

| Rule | Specification |
|------|---------------|
| Version | Parquet 2.6+ |
| Compression | ZSTD (default); Snappy (compatibility) |
| Row group size | 1,000,000 rows (default, adjustable per dataset) |
| Page size | 1 MB (default) |
| Column statistics | Enabled (min, max, null count) |
| Encoding | PLAIN (default); RLE_DICTIONARY for low-cardinality strings |
| Schema mode | Nested structs (see §5.2) |
| File extension | `.parquet` |
| Null representation | Native Parquet null |

### 5.2 Parquet Schema (Logical Types)

```
message RecordEnvelope {
  required binary _record_id (STRING);
  required binary _dataset_id (STRING);
  required binary _record_type (STRING);
  required int32 _version;
  required int64 _created_at (TIMESTAMP_MICROS, UTC);
  required int64 _updated_at (TIMESTAMP_MICROS, UTC);
  required boolean _is_deleted;

  optional group _person {
    optional binary chart_record_id (STRING);
    optional binary person_name_display (STRING);
    optional binary gender (STRING);
    optional boolean is_public_figure;
    optional binary death_date (STRING);
  }

  optional group _birth {
    optional binary birth_date (STRING);
    optional binary birth_date_accuracy (STRING);
    optional binary birth_time (STRING);
    optional binary birth_time_accuracy (STRING);
    optional binary birth_timezone (STRING);
    optional int32 timezone_offset_minutes;
    optional binary birth_place (STRING);
    optional double birth_latitude;
    optional double birth_longitude;
    optional double birth_altitude_m;
    optional binary country_code (STRING);
  }

  optional group _source {
    required binary primary_source_type (STRING);
    optional binary primary_source_uri (STRING);
    optional binary verification_status (STRING);
    optional int64 last_verified_at (TIMESTAMP_MICROS, UTC);
  }

  optional group _confidence {
    optional binary overall_tier (STRING);
    optional double overall_confidence_score;
    optional binary overall_notes (STRING);
  }

  required group _privacy {
    required binary record_privacy_tier (STRING);
    optional boolean contains_pii;
    optional binary consent_status (STRING);
  }

  optional group _research {
    repeated binary tags (STRING);
    repeated binary research_domains (STRING);
    optional binary curator_notes (STRING);
  }

  optional group _computation {
    optional binary engine_version (STRING);
    optional int64 computed_at (TIMESTAMP_MICROS, UTC);
    optional group computation_params {
      optional binary ayanamsa (STRING);
      optional binary house_system (STRING);
    }
  }

  optional group data {
    repeated group planets {
      optional binary planet (STRING);
      optional double sidereal_longitude;
      optional binary rashi (STRING);
      optional double rashi_degree;
      optional int32 house_number;
      optional binary nakshatra (STRING);
      optional binary dignity (STRING);
      optional boolean is_retrograde;
    }
    repeated group houses {
      optional int32 house_number;
      optional binary rashi (STRING);
      optional double cusp_degree;
    }
  }
}
```

### 5.3 Parquet Advantages for AstroOS Research

| Feature | Benefit |
|---------|---------|
| Columnar format | Fast aggregation on specific fields (e.g., average longitude across all records) without reading entire rows |
| Compression | ZSTD achieves 5-10× compression for astrological data (repeating enum values for rashi, nakshatra) |
| Schema enforcement | Type safety — rashi values are validated at write time |
| Nested structures | Natural representation of the record envelope without flattening |
| Predicate pushdown | Filter by birth year without reading full records |
| Cross-platform | Supported by Python (pandas/pyarrow), R, Julia, Spark |
| Statistics | Column min/max enables query optimization |

---

## 6. PostgreSQL Import Schema

### 6.1 Database Schema for Import

The PostgreSQL import schema mirrors the envelope structure using a combination of structured columns and JSONB for nested data:

```sql
-- Schemas
CREATE SCHEMA IF NOT EXISTS astrosos_import;
CREATE SCHEMA IF NOT EXISTS astrosos_datasets;

-- ============================================================
-- Import table: chart_records
-- Stores all chart-type and person-type records
-- ============================================================
CREATE TABLE astrosos_import.chart_records (
    -- Identity
    _record_id           TEXT PRIMARY KEY,
    _dataset_id          TEXT NOT NULL,
    _record_type         TEXT NOT NULL CHECK (_record_type IN ('chart', 'person', 'synthetic', 'reference')),
    _version             INTEGER NOT NULL DEFAULT 1,
    _created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    _updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    _is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,

    -- Birth data
    birth_date           DATE,
    birth_date_accuracy  TEXT,
    birth_time           TIME,
    birth_time_accuracy  TEXT,
    birth_time_source    TEXT,
    birth_timezone       TEXT,
    timezone_offset_minutes INTEGER,
    timezone_verified    BOOLEAN,
    birth_place          TEXT,
    birth_latitude       NUMERIC(9,6),
    birth_longitude      NUMERIC(9,6),
    birth_altitude_m     NUMERIC(7,2),
    birth_place_accuracy TEXT,
    country_code         CHAR(2),

    -- Person data
    person_name_display  TEXT,
    gender               TEXT,
    nationality          TEXT[],
    occupations          TEXT[],
    occupation_categories TEXT[],
    is_public_figure     BOOLEAN,
    notability_score     NUMERIC(3,2),
    death_date           DATE,
    death_place          TEXT,

    -- Source
    source_type          TEXT NOT NULL,
    source_uri           TEXT,
    source_attribution   TEXT,
    verification_status  TEXT NOT NULL,
    last_verified_at     TIMESTAMPTZ,

    -- Confidence
    confidence_tier      TEXT NOT NULL,
    confidence_score     NUMERIC(3,2),
    confidence_notes     TEXT,

    -- Privacy
    privacy_tier         TEXT NOT NULL,
    consent_status       TEXT,
    contains_pii         BOOLEAN NOT NULL DEFAULT FALSE,

    -- Research
    tags                 TEXT[],
    research_domains     TEXT[],
    curator_notes        TEXT,

    -- Computation
    engine_version       TEXT,
    computed_at          TIMESTAMPTZ,
    ayanamsa             TEXT,
    house_system         TEXT,

    -- Extension: full nested data preserved
    data_json            JSONB,
    birth_json           JSONB,
    source_json          JSONB,
    confidence_json      JSONB,
    privacy_json         JSONB,
    research_json        JSONB,

    -- Full text search
    fts_vector           TSVECTOR
);

-- Indexes
CREATE INDEX idx_chart_records_birth_date ON astrosos_import.chart_records (birth_date);
CREATE INDEX idx_chart_records_birth_place ON astrosos_import.chart_records (birth_place);
CREATE INDEX idx_chart_records_country ON astrosos_import.chart_records (country_code);
CREATE INDEX idx_chart_records_privacy ON astrosos_import.chart_records (privacy_tier);
CREATE INDEX idx_chart_records_confidence ON astrosos_import.chart_records (confidence_tier);
CREATE INDEX idx_chart_records_tags ON astrosos_import.chart_records USING GIN (tags);
CREATE INDEX idx_chart_records_fts ON astrosos_import.chart_records USING GIN (fts_vector);
CREATE INDEX idx_chart_records_data ON astrosos_import.chart_records USING GIN (data_json);

-- ============================================================
-- Import table: event_records
-- Stores all event-type records
-- ============================================================
CREATE TABLE astrosos_import.event_records (
    -- Identity
    _record_id           TEXT PRIMARY KEY,
    _dataset_id          TEXT NOT NULL,
    _record_type         TEXT NOT NULL DEFAULT 'event',
    _version             INTEGER NOT NULL DEFAULT 1,
    _created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    _updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    _is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,

    -- Link to chart
    chart_record_id      TEXT REFERENCES astrosos_import.chart_records(_record_id),

    -- Event data
    event_date           DATE NOT NULL,
    event_date_accuracy  TEXT NOT NULL,
    event_type           TEXT NOT NULL,
    event_category       TEXT NOT NULL,
    title                TEXT NOT NULL,
    description          TEXT,
    event_place          TEXT,
    event_latitude       NUMERIC(9,6),
    event_longitude      NUMERIC(9,6),

    -- Person data (denormalized)
    person_name_display  TEXT,
    is_public_figure     BOOLEAN,

    -- Source (same pattern as chart_records)
    source_type          TEXT NOT NULL,
    verification_status  TEXT NOT NULL,

    -- Confidence & Privacy
    confidence_tier      TEXT NOT NULL,
    privacy_tier         TEXT NOT NULL,

    -- Research
    tags                 TEXT[],

    -- Extension
    data_json            JSONB
);

-- Indexes
CREATE INDEX idx_event_records_chart ON astrosos_import.event_records (chart_record_id);
CREATE INDEX idx_event_records_date ON astrosos_import.event_records (event_date);
CREATE INDEX idx_event_records_type ON astrosos_import.event_records (event_type);
CREATE INDEX idx_event_records_privacy ON astrosos_import.event_records (privacy_tier);

-- ============================================================
-- Import table: twin_pairs
-- Stores relationship (twin) records
-- ============================================================
CREATE TABLE astrosos_import.twin_pairs (
    _record_id           TEXT PRIMARY KEY,
    _dataset_id          TEXT NOT NULL,
    twin_type            TEXT NOT NULL,
    twin_a_record_id     TEXT,
    twin_b_record_id     TEXT,
    birth_interval_minutes INTEGER,
    birth_order_a        INTEGER,
    birth_order_b        INTEGER,
    shared_birth_date    DATE,
    shared_birth_place   TEXT,
    data_json            JSONB
);
```

### 6.2 Import from CSV

```sql
-- Using psql \copy
\copy astrosos_import.chart_records (_record_id, _dataset_id, _record_type, _version, _created_at, _updated_at, _is_deleted, birth_date, birth_date_accuracy, birth_time, birth_time_accuracy, birth_timezone, timezone_offset_minutes, birth_place, birth_latitude, birth_longitude, country_code, person_name_display, gender, is_public_figure, occupations, nationality, source_type, source_uri, verification_status, last_verified_at, confidence_tier, confidence_score, confidence_notes, privacy_tier, contains_pii, tags, research_domains, curator_notes) FROM 'ASTRO-PB-WIKI-v1.0.0_CSV.csv' WITH (FORMAT CSV, HEADER true, NULL 'null', FORCE_NULL (birth_time, birth_timezone));
```

### 6.3 Import from Parquet via Python

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://user:pass@localhost/astrosos')
df = pd.read_parquet('ASTRO-PB-WIKI-v1.0.0_PARQUET.parquet')
df.to_sql('chart_records', engine, schema='astrosos_import', if_exists='append', method='multi')
```

---

## 7. Research Export Format

### 7.1 Purpose

The Research Export Format is designed specifically for the Statistics Engine and Research Engine. It prioritizes:
- Columnar access patterns (fast aggregation)
- Schema stability (backward-compatible changes only)
- Self-describing metadata (embedded in the file)
- Privacy-safe defaults (PII automatically excluded)

### 7.2 Export Format Selection

| Analysis Type | Recommended Format | Reason |
|---------------|-------------------|--------|
| Descriptive statistics | Parquet | Columnar, fast aggregation, nested structs |
| Contingency tables | Parquet | Fast group-by operations |
| Distribution analysis | Parquet | Column statistics pre-computed |
| ML training | Parquet | Direct input to pandas/torch/tensorflow |
| Ad-hoc exploration | CSV | Universal tool support |
| API response | JSON | Native web format |
| Streaming large data | JSONL | Line-by-line processing |
| R analysis | Parquet (via arrow) | Native R arrow::read_parquet() |

### 7.3 Research Export Schema

The research export schema is a **flattened subset** of the full envelope, optimized for statistical analysis:

```python
RESEARCH_EXPORT_FIELDS = [
    # Record identity
    "_record_id",
    "_dataset_id",
    "_record_type",
    "_version",

    # Birth data (flat)
    "birth_date",              # Date
    "birth_year",              # Derived (for cohort analysis)
    "birth_month",             # Derived (1-12)
    "birth_dow",               # Derived (day of week, 0=Mon)
    "birth_time",              # Time or null
    "birth_hour",              # Derived (hour of day, 0-23)
    "birth_time_accuracy",
    "birth_timezone",
    "timezone_offset_minutes",
    "birth_latitude",
    "birth_longitude",
    "birth_place",
    "country_code",

    # Computed chart features (when available)
    "lagna_rashi",
    "lagna_nakshatra",
    "lagna_pada",
    "sun_rashi",
    "moon_rashi",
    "moon_nakshatra",
    "moon_pada",
    "mars_rashi",
    "mercury_rashi",
    "jupiter_rashi",
    "venus_rashi",
    "saturn_rashi",
    "rahu_rashi",
    "ketu_rashi",

    # Event data (for event-type records)
    "event_date",
    "event_year",
    "event_type",
    "event_category",

    # Person metadata
    "gender",
    "is_public_figure",
    "occupation_categories",

    # Confidence & source
    "confidence_tier",
    "verification_status",
    "source_type",
    "privacy_tier",

    # Research
    "tags",                    # Pipe-joined for CSV, array for Parquet
    "research_domains",        # Pipe-joined for CSV, array for Parquet
]
```

### 7.4 Research Export Integrity Guarantees

| Guarantee | Description |
|-----------|-------------|
| **Deterministic** | Same input + same engine version → identical export |
| **Row-preserving** | No aggregation or sampling; each input row maps to exactly one output row |
| **Privacy-filtered** | PII fields excluded; anonymous exports checked for re-identification risk |
| **Version-stamped** | Export version recorded in metadata; breaking changes trigger major version |
| **Self-describing** | Metadata embedded as a separate `_METADATA_` row or sidecar file |
| **Compute-once** | Exports are cached; re-running confirms hash match |

### 7.5 Research Cohort Export (Special Case)

When a ResearchEngine study needs a cohort exported:

```python
# The StatisticsEngine gets:
# 1. A reference to the cohort definition
# 2. The flattened chart data for cohort members
# 3. Metadata about the export

cohort_export = {
    "export_id": "EXP-20260715-001",
    "cohort_id": "ASTRO-RS-COHORT-nobel-laureates-v1.0.0",
    "exported_at": "2026-07-15T12:00:00Z",
    "engine_version": "astrosos-engine-1.0.0",
    "record_count": 642,
    "fields": RESEARCH_EXPORT_FIELDS,
    "privacy_filter_applied": True,
    "checksum_sha256": "a1b2c3d4..."
}
```

---

## 8. Cross-Format Consistency

### 8.1 Schema Equivalence

All formats represent the **same conceptual schema**. The mapping is:

| Logical Element | CSV | JSON/JSONL | Parquet | PostgreSQL |
|-----------------|-----|------------|---------|------------|
| Scalar field | Column | Property | Primitive column | Column |
| Nested object | Prefix-flattened (`birth_date`) | Nested object | Nested struct | Column or JSONB |
| Array of scalars | Pipe-joined in single column | JSON array | Repeated column | ARRAY column |
| Array of objects | Row expansion | JSON array of objects | Repeated group | Separate table or JSONB |
| Null value | Empty string or `null` | `null` | Null | NULL |
| Metadata | Columns or separate file | Envelope wrapper | Top-level fields | Columns + JSONB |

### 8.2 Transformation Guarantees

```mermaid
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌────────────┐
│   CSV   │────▶│  JSON   │────▶│  JSONL   │────▶│  Parquet   │
└─────────┘     └─────────┘     └──────────┘     └────────────┘
     │              │                                │
     │              ▼                                │
     │         ┌──────────┐                          │
     └────────▶│ PostgreSQL │◀────────────────────────┘
               └──────────┘
```

- **CSV → JSON**: Lossless if pipe-joined arrays are split back
- **JSON → JSONL**: Lossless (line split is reversible)
- **JSONL → Parquet**: Lossy for deeply nested structures (flattened to repeated groups); JSONB backup preserves original
- **Parquet → PostgreSQL**: Lossy for repeated groups (stored as JSONB backup); structural columns for common queries
- **All formats → CSV**: Lossy (row expansion for one-to-many; pipe-joining for simple arrays)

### 8.3 Format Conversion Rules

| Source | Target | Conversion | Information Loss |
|--------|--------|------------|-----------------|
| CSV | JSON | Parse pipe-joined arrays; reconstruct envelope | None if parsed correctly |
| JSON | CSV | Flatten envelope; pipe-join arrays; row-expand one-to-many | Array structure (order preserved in pipe-join) |
| JSON | Parquet | Direct struct mapping | None |
| Parquet | JSON | Struct → nested object | None |
| JSONL | Parquet | Merge all lines into a single table | None |
| Any | SQL | Map to columnar + JSONB backup | None (JSONB preserves original structure) |
| Any | Research Export | Filter to export fields; flatten | Intentional (privacy + performance) |

### 8.4 Format Manifest

Every dataset version includes a `FORMATS.json` manifest:

```json
{
  "dataset_id": "ASTRO-PB-WIKI-v1.0.0",
  "formats": {
    "csv": {
      "file": "ASTRO-PB-WIKI-v1.0.0_CSV.csv.gz",
      "size_bytes": 2456789,
      "checksum_sha256": "a1b2c3d4e5...",
      "records": 15000,
      "fields": 44
    },
    "json": {
      "file": "ASTRO-PB-WIKI-v1.0.0_JSON.json.gz",
      "size_bytes": 5678901,
      "checksum_sha256": "f6g7h8i9...",
      "records": 15000
    },
    "jsonl": {
      "file": "ASTRO-PB-WIKI-v1.0.0_JSONL.jsonl.gz",
      "size_bytes": 5234567,
      "checksum_sha256": "j0k1l2m3...",
      "records": 15000
    },
    "parquet": {
      "file": "ASTRO-PB-WIKI-v1.0.0_PARQUET.parquet",
      "size_bytes": 1234567,
      "checksum_sha256": "n4o5p6q7...",
      "records": 15000,
      "row_groups": 2,
      "compression": "zstd"
    },
    "sql": {
      "file": "ASTRO-PB-WIKI-v1.0.0_SQL.sql.gz",
      "size_bytes": 3456789,
      "checksum_sha256": "r8s9t0u1..."
    }
  },
  "schema_version": "1.0",
  "generated_at": "2026-07-15T12:00:00Z"
}
```

---

*End of Phase 6: Standard Formats. Awaiting approval to proceed to Phase 7: Research Support.*
