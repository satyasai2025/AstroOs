# Standards Compliance Review — AstroDatabank Import

> **Purpose:** Verify that the AstroDatabank data schema can be fully mapped to the AstroOS Record Standards (Phase 4) and Dataset Standards (Phase 3).
> **Owner:** Chief Dataset & Research Curator
> **Date:** 2026-07-15

---

## 1. Record Envelope Coverage

### 1.1 Required Fields (Phase 4 §2.1)

| Envelope Field | AstroDatabank Source | Mapping Status | Gap |
|---------------|---------------------|----------------|-----|
| `_record_id` | DocID | ✅ Mapped | — |
| `_dataset_id` | — | ✅ Static | — |
| `_record_type` | — | ✅ Static | — |
| `_version` | — | ✅ Static | — |
| `_created_at` | — | ✅ Import timestamp | — |
| `_updated_at` | — | ✅ Import timestamp | — |
| `_is_deleted` | — | ✅ Static false | — |
| `_source.primary_source` | RR + attribution | ✅ Mapped | — |
| `_source.verification_status` | RR | ✅ Mapped | — |
| `_privacy.record_privacy_tier` | — | ✅ Static public | — |
| `_privacy.contains_pii` | — | ✅ Static false | — |

**Result: 11/11 required fields mapped. No gaps.**

### 1.2 Birth Sub-Schema (Phase 4 §3.1)

| Field | Source | Status | Gap |
|-------|--------|--------|-----|
| `birth_date` | Day + Month + Year | ✅ Mapped | — |
| `birth_date_accuracy` | — | ✅ Derived: always "exact" | — |
| `birth_time` | Time | ✅ Mapped | — |
| `birth_time_accuracy` | RR | ✅ Mapped via RR→accuracy table | — |
| `birth_time_source` | RR | ✅ Derived: rectification for X, unknown for others | — |
| `birth_timezone` | — | ⚠️ Not in source | Needs longitude-derived estimation |
| `timezone_offset_minutes` | — | ✅ Derived: lng/15*60 | Approximate |
| `birth_place` | Place + Country | ✅ Mapped with normalization | — |
| `birth_latitude` | Lat | ✅ Mapped | — |
| `birth_longitude` | Lng | ✅ Mapped | — |
| `birth_altitude_m` | — | ❌ Not in source | Missing — acceptable for import |
| `birth_place_accuracy` | — | ✅ Derived: "exact" (city+country) | — |
| `country_code` | Country | ✅ Mapped via lookup | — |
| `julian_day` | — | ⚠️ Computed | Will be computed post-import |
| `julian_day_source` | — | ✅ Computed | — |

**Result: 14/15 fields mapped. 1 gap (altitude) — acceptable. 2 fields computed post-import.**

### 1.3 Person Sub-Schema (Phase 4 §5.1)

| Field | Source | Status | Gap |
|-------|--------|--------|-----|
| `chart_record_id` | — | ✅ Self-referencing | — |
| `person_name_display` | Last Name + First Name | ✅ Mapped | — |
| `person_name_original_script` | — | ❌ Not in source | Not available |
| `gender` | Gender | ✅ Mapped | — |
| `nationality` | — | ❌ Not in source | Derived from country |
| `known_for` | — | ❌ Not in source | Not available |
| `occupations` | — | ❌ Not in source | Not available |
| `occupation_categories` | — | ❌ Not in source | Not available |
| `birth_name` | — | ⚠️ Same as display | — |
| `aliases` | — | ❌ Not in source | Not available |
| `is_public_figure` | — | ✅ Default false | — |
| `notability_score` | — | ❌ Not in source | Not available |
| `death_date` | — | ❌ Not in source | Not available |
| `death_date_accuracy` | — | ❌ Not in source | — |
| `death_place` | — | ❌ Not in source | Not available |
| `death_cause` | — | ❌ Not in source | Not available |
| `biography_summary` | — | ❌ Not in source | Not available |

**Result: 4/17 person fields mapped. 13 gaps — most are enrichment fields that can be populated in v1.1.0 from Wikipedia/Wikidata.**

### 1.4 Source Sub-Schema (Phase 4 §6.1)

| Field | Source | Status | Gap |
|-------|--------|--------|-----|
| `primary_source.type` | — | ✅ Static: "astro_databank" | — |
| `primary_source.uri` | — | ⚠️ Not available | URL unknown |
| `primary_source.attribution` | — | ✅ Static: "Astrodienst Astro-Databank" | — |
| `primary_source.license` | — | ⚠️ Unknown | License TBD |
| `verification_status` | RR | ✅ Mapped | — |
| `last_verified_at` | — | ✅ Import date | — |
| `field_sources` | — | ❌ Not per-field | All fields from same source |

**Result: 4/7 source fields mapped. License and URI pending legal review.**

### 1.5 Confidence Sub-Schema (Phase 4 §7.1)

| Field | Source | Status | Gap |
|-------|--------|--------|-----|
| `overall_tier` | RR | ✅ Mapped | — |
| `overall_notes` | — | ✅ Derived from RR | — |
| `overall_confidence_score` | RR | ✅ Mapped (0.05-0.95) | — |
| `field_confidence.birth_time` | RR | ✅ Mapped | — |
| `field_confidence.birth_date` | — | ✅ Always "verified" | — |
| `field_confidence.birth_place` | — | ✅ Always "verified" | — |

**Result: 6/6 confidence fields mapped. No gaps.**

### 1.6 Privacy Sub-Schema (Phase 4 §8.1)

| Field | Source | Status | Gap |
|-------|--------|--------|-----|
| `record_privacy_tier` | — | ✅ Static: "public" | — |
| `contains_pii` | — | ✅ Static: false | — |
| `pii_fields` | — | ✅ Static: [] | — |
| `consent_status` | — | ✅ Static: "not_applicable" | — |

**Result: 4/4 privacy fields mapped. No gaps.**

### 1.7 Research Sub-Schema (Phase 4 §9.1)

| Field | Source | Status | Gap |
|-------|--------|--------|-----|
| `tags` | Events, RR, Gender | ✅ Derived | — |
| `research_domains` | Events | ✅ Derived | — |
| `curator_notes` | — | ✅ Import notes | — |

**Result: 3/3 research fields mapped. No gaps.**

---

## 2. Dataset Standards Compliance

### 2.1 Common Metadata (Phase 3 §2)

| Field | Status | Notes |
|-------|--------|-------|
| `dataset_id` | ✅ Will be assigned | `ASTRO-RS-EVENT-v1.0.0` |
| `name` | ✅ Defined | "Life Event Datasets" |
| `description` | ✅ Defined | Per Phase 2 §3.2.2 |
| `category` | ✅ Defined | "Research" |
| `version` | ✅ Defined | "1.0.0" |
| `license_id` | ⚠️ Pending | License determination needed |
| `privacy_tier` | ✅ Defined | "public" |
| `confidence_tier` | ✅ Defined | Per-record based on RR |
| `quality_score` | ✅ Will be computed | Post-import scoring |

### 2.2 Quality Standards (Phase 5)

| Standard | Status | Notes |
|----------|--------|-------|
| Completeness measurement | ✅ Defined | Phase 5 §1 |
| Missing field handling | ✅ Defined | Phase 5 §2 |
| Duplicate detection | ✅ Defined | Phase 5 §3 |
| Consistency framework | ✅ Defined | Phase 5 §4 |
| Bias assessment | ✅ Defined | Phase 5 §5 |

---

## 3. Identified Gaps

### 3.1 Acceptable Gaps (v1.0.0)

| Gap | Impact | Resolution |
|-----|--------|------------|
| Birth altitude missing | Low — altitude rarely affects calculations | Accept; leave null |
| Person enrichment fields missing | Medium — limits research utility | Populate in v1.1.0 from Wikipedia |
| Timezone unknown | Low — offset derived from longitude | Accept; refine with RF-TZ |
| License unknown | High — affects redistribution | Resolve before publication |

### 3.2 Blocking Gaps (Must Resolve Before v1.0.0)

| Gap | Impact | Resolution |
|-----|--------|------------|
| License determination | Critical — cannot publish without license | Legal review required |
| URI/source documentation | Medium — provenance incomplete | Add source URL if available |

### 3.3 Future Enrichment (v1.1.0+)

| Gap | Impact | Resolution |
|-----|--------|------------|
| Occupation data | Medium — limits research | Cross-reference with Wikidata |
| Death dates | Medium — limits longevity studies | Cross-reference with Wikipedia |
| Biography summaries | Low — metadata only | Future enrichment |
| Public figure status | Low — default false | Cross-reference with Wikipedia notability |

---

## 4. Compliance Verdict

| Area | Compliance | Notes |
|------|-----------|-------|
| Record Envelope | ✅ **PASS** | All required fields mapped |
| Birth Data | ✅ **PASS** | 14/15 fields; 1 acceptable gap |
| Person Data | ⚠️ **PARTIAL** | 4/17; enrichment needed in v1.1.0 |
| Source Tracking | ✅ **PASS** | 4/7; license pending |
| Confidence | ✅ **PASS** | 6/6 fields mapped |
| Privacy | ✅ **PASS** | 4/4 fields mapped |
| Research | ✅ **PASS** | 3/3 fields mapped |
| Dataset Standards | ✅ **PASS** | All standards addressable |

### Overall Verdict: **CONDITIONALLY COMPLIANT**

The AstroDatabank data can be imported into the AstroOS Record Standards with the following conditions:
1. License must be resolved before publication
2. Person enrichment fields to be populated in v1.1.0
3. Altitude field acceptable as null
4. Timezone derived from longitude acceptable for v1.0.0
