---
name: astrosos-dataset-taxonomy
description: "Complete dataset taxonomy for AstroOS Research Dataset Repository — 10 categories, 40+ dataset types, full metadata standards"
metadata: 
  node_type: memory
  type: reference
  domain: datasets
  status: draft
  phase: 2
  originSessionId: e78a75e5-611c-4c3f-99a8-68817dfe9484
---

# AstroOS Dataset Taxonomy — Phase 2

> **Status:** DRAFT — pending approval
> **Owner:** Chief Dataset & Research Curator
> **Version:** 1.0
> **Date:** 2026-07-15

---

## 1. Classification Framework

Every dataset in the AstroOS Research Dataset Repository is classified across five orthogonal axes:

| Axis | Values | Description |
|---|---|---|
| **Category** | Reference / Research / Benchmark / Validation / QA-Test / AI-Eval / Synthetic / Public / Licensed / User-Contributed | Functional role |
| **Privacy Tier** | Public / Anonymous / Pseudonymous / Private / Restricted | Data subject protection |
| **Confidence Tier** | Verified / Estimated / Rectified / Synthetic / Unknown | Birth data certainty |
| **Provenance Tier** | Primary / Derived / Curated / Generated / Contributed | Origin classification |
| **Lifecycle Stage** | Draft / Candidacy / Stable / Deprecated / Archived | Maturity |

---

## 2. Dataset ID Convention

Every dataset receives a permanent, unique identifier following this convention:

```
ASTRO-{CATEGORY}-{TYPE}-{VERSION}
```

Where:
- `ASTRO` — fixed prefix (AstroOS)
- `CATEGORY` — 2-letter category code
- `TYPE` — 4-6 letter type code
- `VERSION` — semver (v1.0.0, v1.1.0, v2.0.0)

**Category codes:**

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

**Example:** `ASTRO-RS-COHORT-v1.0.0` = Research dataset, Cohort type, version 1.0.0

---

## 3. Dataset Category Definitions

---

### 3.1 REFERENCE DATASETS (RF)

Immutable, authoritative data that underpins all astrological calculations and interpretations. These datasets change only when the underlying knowledge standard changes (extremely rare). They are the source of truth for the entire system.

#### 3.1.1 Ephemeris Data (RF-EPHEM)

| Field | Specification |
|---|---|
| **Purpose** | Provide planetary position calculation coefficients for all astrological computations |
| **Consumers** | EphemerisEngine, GrahaEngine, TransitEngine, ShadbalaEngine, AshtakavargaEngine, DashaEngine, HoroscopeEngine, ReportEngine, AIEngine |
| **Source** | Swiss Ephemeris (Astrodienst), JPL DE440/DE441, JPL Horizons |
| **Required Schema** | Binary `.se1` files (Swiss Ephemeris format) — three files per ephemeris set: `seas` (asteroids), `semo` (Moon), `sepl` (planets) |
| **Mandatory Metadata** | Ephemeris version, start/end date range, body count, frame of reference (ICRF/J2000), Nutation model, planetary theory (VSOP87/DE440), checksum, origin URL |
| **Quality Requirements** | 100% deterministic; must reproduce known planetary positions to ≤0.001° accuracy against IAE/NASA reference values |
| **Validation Rules** | Compare output positions against published JPL Horizons data for 100 reference dates spanning 1900–2100; daily positions for all 9 grahas must match within 0.001° |
| **Versioning Strategy** | Immutable per source version; new Swiss Ephemeris releases are new dataset versions with changelog documenting precision improvements |
| **Provenance** | Licensed from Astrodienst (Swiss Ephemeris); includes dual-license (commercial/private use, research/education free) |
| **Licensing Classification** | Licensed — Swiss Ephemeris dual license (free for research/education, commercial license required for production) |
| **Privacy Classification** | Public (no personal data) |
| **Update Lifecycle** | Annual review; new major version when JPL releases new DE (typically every 5-10 years); minor version when Swiss Ephemeris patches |

#### 3.1.2 Reference Sign Data (RF-SIGNS)

| Field | Specification |
|---|---|
| **Purpose** | Authoritative table of the 12 zodiac signs with all classical attributes |
| **Consumers** | All calculation engines, OntologyRegistry, KnowledgeEngine, ReportEngine, AIEngine |
| **Source** | Classical Jyotish texts (BPHS, Saravali, Jataka Tattva) |
| **Required Schema** | 12 rows: id, name, sanskrit_name, lord, element, modality, gender, direction, start_degree, end_degree |
| **Mandatory Metadata** | Source texts cited, sanskrit transliteration standard (IAST), version, last reviewed date |
| **Quality Requirements** | 100% complete (no nulls for required columns); attested in ≥2 classical sources |
| **Validation Rules** | All 12 present; lord assignment matches classical rulership table; degree ranges are continuous 0°–360°; element/modality/gender follow classical triplicities |
| **Versioning Strategy** | Immutable — version 1.0.0 only (classical knowledge does not change) |
| **Provenance** | Curated from classical Jyotish literature; cross-referenced across texts |
| **Licensing Classification** | Public (classical knowledge, no copyright) |
| **Privacy Classification** | Public (no personal data) |
| **Update Lifecycle** | Never (unless textual scholarship reveals a correction, which would warrant RF-SIGNS-v2.0.0 with a documented rationale) |

#### 3.1.3 Reference Nakshatra Data (RF-NAK)

| Field | Specification |
|---|---|
| **Purpose** | Authoritative table of the 27 nakshatras with all classical attributes |
| **Consumers** | All calculation engines, OntologyRegistry, KnowledgeEngine, ReportEngine, AIEngine |
| **Source** | Classical Jyotish texts (BPHS, Saravali, Jataka Parijata) |
| **Required Schema** | 27 rows: id, name, lord, number, start_degree, end_degree, deity, symbol, gana, nadi, varna, yoni, shakti |
| **Mandatory Metadata** | Source texts cited, transliteration standard, version, empty-field rationale (which fields are NULL and why) |
| **Quality Requirements** | All 27 present; lord sequence matches Vimshottari cycle; degree ranges continuous 0°–360°; deity/symbol/gana/nadi/varna/yoni/shakti filled only from verified classical sources |
| **Validation Rules** | 27 unique entries; lord sequence repeats the 9-planet Vimshottari cycle exactly 3 times; degree ranges are 13°20′ each |
| **Versioning Strategy** | Immutable — v1.0.0 for settled fields; fields left NULL may be populated in minor versions (v1.1.0, v1.2.0) as textual research fills gaps |
| **Provenance** | Curated from classical Jyotish literature |
| **Licensing Classification** | Public (classical knowledge) |
| **Privacy Classification** | Public (no personal data) |
| **Update Lifecycle** | Never for degree/lord fields; NULL fields may be updated when verified sources are found |

#### 3.1.4 Reference Pada Data (RF-PADA)

| Field | Specification |
|---|---|
| **Purpose** | Authoritative table of the 108 padas with navamsha mappings |
| **Consumers** | All calculation engines, DivisionalEngine, DashaEngine |
| **Source** | Derived mathematically from nakshatra boundaries and Navamsha division |
| **Required Schema** | 108 rows: id, nakshatra_id, pada_number, navamsha_rashi, start_degree, end_degree |
| **Mandatory Metadata** | Mathematical formula documented, cross-verification against divisional engine |
| **Quality Requirements** | All 108 present; degree ranges continuous 0°–360°; navamsha_rashi matches DivisionalEngine.D9 output for all 108 |
| **Validation Rules** | D9 navamsha calculation independently reproduced from pada boundaries (not just circular reference); degree width = 3°20′ each |
| **Versioning Strategy** | Immutable — v1.0.0 (mathematically determined, no subjective content) |
| **Provenance** | Derived from nakshatra boundaries by fixed mathematical formula |
| **Licensing Classification** | Public (mathematical derivation) |
| **Privacy Classification** | Public (no personal data) |
| **Update Lifecycle** | None |

#### 3.1.5 Reference Planet Data (RF-PLANET)

| Field | Specification |
|---|---|
| **Purpose** | Authoritative table of the 9 grahas (navagraha) with all classical attributes |
| **Consumers** | All calculation engines, OntologyRegistry, KnowledgeEngine, ShadbalaEngine, YogaEngine |
| **Source** | Classical Jyotish texts (BPHS, Saravali) |
| **Required Schema** | 9 rows: id, name, sanskrit_name, exaltation_degree, debilitation_degree, moolatrikona_sign, own_signs, friendly_signs, neutral_signs, enemy_signs, gender, guna, varna, gemstone, day_of_week, direction, dasha_years |
| **Mandatory Metadata** | Source texts cited, tradition noted (BPHS vs. alternate schools) |
| **Quality Requirements** | All 9 present; exaltation/debilitation degrees attested in ≥2 classical sources |
| **Validation Rules** | Moolatrikona positions verified against BPHS; friend/enemy relationships symmetric (if A is friendly to B, B is not enemy to A); dasha years sum = 120 |
| **Versioning Strategy** | Immutable for core attributes; optional fields may be versioned if new sources consulted |
| **Provenance** | Curated from classical Jyotish literature |
| **Licensing Classification** | Public (classical knowledge) |
| **Privacy Classification** | Public (no personal data) |
| **Update Lifecycle** | None for core attributes |

#### 3.1.6 Reference House Meanings (RF-HOUSE)

| Field | Specification |
|---|---|
| **Purpose** | Authoritative descriptions of the 12 bhavas (houses) with classical significations |
| **Consumers** | KnowledgeEngine, ReportEngine, AIEngine, RuleEngine |
| **Source** | Classical Jyotish texts (BPHS, Jataka Tattva, Saravali) |
| **Required Schema** | 12 rows: id, house_number, name, sanskrit_name, karakatvas (list), body_parts, natural_significations, classical_quotes |
| **Mandatory Metadata** | Source texts cited for each signification |
| **Quality Requirements** | All 12 present; significations traceable to classical verse |
| **Validation Rules** | Karakatva assignments cross-referenced with Karakatva reference data |
| **Versioning Strategy** | Stable; minor versions for additional classical references |
| **Provenance** | Curated from classical Jyotish literature |
| **Licensing Classification** | Public (classical knowledge) |
| **Privacy Classification** | Public (no personal data) |
| **Update Lifecycle** | Reviewed annually for additional source citations |

#### 3.1.7 Reference Karakatva Data (RF-KARAKA)

| Field | Specification |
|---|---|
| **Purpose** | Authoritative table of planetary and sign significators (karakatvas) |
| **Consumers** | RuleEngine, ReportEngine, AIEngine, KnowledgeEngine |
| **Source** | Classical Jyotish texts, BPHS chapter on karakatvas |
| **Required Schema** | Multi-row: subject, karaka_graha_1, karaka_graha_2, karaka_rashi, house_bhava |
| **Mandatory Metadata** | Source verse reference for each assignment |
| **Quality Requirements** | Complete coverage of known life domains; traceable to source |
| **Validation Rules** | No contradictory assignments; both natural (nitya) and chara (temporary) karakatvas documented |
| **Versioning Strategy** | Stable; minor versions for additional domains |
| **Provenance** | Curated from classical Jyotish literature |
| **Licensing Classification** | Public (classical knowledge) |
| **Privacy Classification** | Public (no personal data) |
| **Update Lifecycle** | Reviewed annually |

#### 3.1.8 Reference Ayanamsa Data (RF-AYAN)

| Field | Specification |
|---|---|
| **Purpose** | Authoritative ayanamsa values and precession formulae for all supported systems |
| **Consumers** | EphemerisEngine, all calculation engines |
| **Source** | Indian Astronomical Ephemeris (IAE), Newcomb precession formula, astronomical almanacs |
| **Required Schema** | Per-system: name, current_value_deg, precession_rate_deg_per_year, formula, epoch_date, reference_source |
| **Mandatory Metadata** | Formula derivation, epoch date, reference value source |
| **Quality Requirements** | Must reproduce IAE published ayanamsa values for 1900–2100 to ≤0.001° |
| **Validation Rules** | Spot-check Lahiri, KP, Raman, Yukteshwar, Fagan-Bradley, True Chitra against published tables at 10-year intervals 1900–2100 |
| **Versioning Strategy** | Annual update for drift; formula document immutable |
| **Provenance** | Derived from astronomical formulae |
| **Licensing Classification** | Public (astronomical formulae) |
| **Privacy Classification** | Public (no personal data) |
| **Update Lifecycle** | Annually (precession advances ~50″/year; ayanamsa values update) |

#### 3.1.9 Dasha Reference Table (RF-DASHA)

| Field | Specification |
|---|---|
| **Purpose** | Authoritative Dasha years, sequences, and rules for all supported Dasha systems |
| **Consumers** | DashaEngine, TimelineEngine, TransitEngine, ReportEngine |
| **Source** | Classical Jyotish texts (BPHS for Vimshottari, Ashtottari, Yogini; Saravali for Kalachakra) |
| **Required Schema** | Per system: dasha_type, lord_sequence, total_years, lord_years, activation_rules |
| **Mandatory Metadata** | Source text for each system, commentary tradition noted |
| **Quality Requirements** | Vimshottari sum = 120; Ashtottari sum = 108; all sequences attested in classical source |
| **Validation Rules** | Vimshottari: ketu=7, venus=20, sun=6, moon=10, mars=7, rahu=18, jupiter=16, saturn=19, mercury=17 (sum=120). All systems validated against published tables |
| **Versioning Strategy** | Immutable for classical systems |
| **Provenance** | Curated from classical Jyotish literature |
| **Licensing Classification** | Public (classical knowledge) |
| **Privacy Classification** | Public (no personal data) |
| **Update Lifecycle** | None |

#### 3.1.10 Timezone & Location Reference (RF-TZ)

| Field | Specification |
|---|---|
| **Purpose** | Historical timezone database and location geocoding for birth chart calculations |
| **Consumers** | EphemerisEngine, ChartService, BirthChart creation flow |
| **Source** | IANA Time Zone Database (tzdata), GeoNames, NaturalEarth |
| **Required Schema** | tzid, country_code, latitude, longitude, offset_standard, offset_dst, start_date, end_date (timezone transitions); location_name, country, lat, lng, timezone_id (locations) |
| **Mandatory Metadata** | tzdata version, data source, coverage date range |
| **Quality Requirements** | Covers all populated locations; historical timezone transitions recorded from 1800 onward; accuracy within 1 km for cities |
| **Validation Rules** | Spot-check 100 edge-case locations (regions with DST changes, war-time offsets, disputed territories); all IANA transitions present |
| **Versioning Strategy** | Updated with each IANA tzdata release (~quarterly) |
| **Provenance** | Derived from IANA tzdata (public domain), GeoNames (CC-BY) |
| **Licensing Classification** | Public (IANA tzdata is public domain); GeoNames data carries CC-BY attribution requirement |
| **Privacy Classification** | Public (geographic data only) |
| **Update Lifecycle** | Quarterly (aligned with IANA tzdata releases) |

---

### 3.2 RESEARCH DATASETS (RS)

Structured, queryable datasets designed for statistical analysis, hypothesis testing, and research studies. These are the primary data assets consumed by the Statistics Engine and Research Engine.

#### 3.2.1 Birth Chart Cohorts (RS-COHORT)

| Field | Specification |
|---|---|
| **Purpose** | Filtered collections of birth charts for statistical analysis, grouped by shared characteristics |
| **Consumers** | StatisticsEngine, ResearchEngine, ReportEngine, VerificationEngine, AIEngine |
| **Required Schema** | Cohort metadata (id, name, description, inclusion_criteria, exclusion_criteria, cohort_size, creation_date) + Chart references (chart_id, selection_reason, weight) |
| **Mandatory Metadata** | Inclusion/exclusion criteria, filter date range, cohort version, curator, filter parameters |
| **Quality Requirements** | Reproducible — same criteria must produce identical cohort on re-run; selection bias documented; cohort size ≥30 for statistical validity |
| **Validation Rules** | Random sample of cohort manually verified against criteria; reproducibility check by re-running filter |
| **Versioning Strategy** | Major version: criteria changes; minor version: data refresh without criteria change |
| **Provenance** | Curated from underlying chart database by filter criteria |
| **Licensing Classification** | Per-source (depends on constituent chart licenses) |
| **Privacy Classification** | Anonymous (no PII in cohort metadata; chart references by anonymous ID only) |
| **Update Lifecycle** | Static snapshots — cohorts are versioned once created; refreshed on demand |

#### 3.2.2 Life Event Datasets (RS-EVENT)

| Field | Specification |
|---|---|
| **Purpose** | Collections of known life events linked to birth charts for verification and correlation studies |
| **Consumers** | VerificationEngine, StatisticsEngine, ResearchEngine, AIEngine |
| **Required Schema** | chart_id, event_id, event_date, event_type (marriage/career/education/health/progeny/wealth/longevity/other), event_category, title, description, confidence (verified/estimated/uncertain), source, event_date_accuracy (exact_date/month/year/estimated), tags |
| **Mandatory Metadata** | Event type classification, confidence level, source citation, date accuracy |
| **Quality Requirements** | Each event traceable to a verifiable source; date accuracy explicitly documented (not assumed); verified events clearly distinguished from estimated ones |
| **Validation Rules** | Event date must not precede birth date; event type must map to known category or be tagged `other:custom_label`; confidence=verified requires source citation with verifiable reference |
| **Versioning Strategy** | Major version: schema or classification changes; minor version: additions/corrections; patch: metadata fixes |
| **Provenance** | Curated from biographical sources, public records, user submission, research studies |
| **Licensing Classification** | Per-source |
| **Privacy Classification** | Pseudonymous for public figures; Anonymous for private individuals |
| **Update Lifecycle** | Continuous — curated as sources are identified and verified |

#### 3.2.3 Marriage Datasets (RS-MARRIAGE)

| Field | Specification |
|---|---|
| **Purpose** | Specialized event dataset for marriage timing and spouse indicators research |
| **Consumers** | VerificationEngine, StatisticsEngine, ResearchEngine |
| **Required Schema** | chart_id, spouse_name (anonymous), marriage_date, marriage_date_accuracy, spouse_birth_date (optional), spouse_birth_details (optional), engagement_date (optional), divorce_date (optional), marriage_number, cultural_tradition, source |
| **Mandatory Metadata** | Arranged vs. love marriage (if known); cultural tradition (for timing rule variations); confidence level |
| **Quality Requirements** | Marriage date verified against public record or biographical source; ≥2 independent sources required for verified confidence |
| **Validation Rules** | Marriage date ≥ legal minimum age by country; marriage date ≤ death date; engagement ≤ marriage ≤ divorce (chronological order) |
| **Versioning Strategy** | Part of RS-EVENT lifecycle; versioned as sub-collection |
| **Provenance** | Curated from biographies, genealogical records, census data |
| **Licensing Classification** | Per-source |
| **Privacy Classification** | Anonymous — all identifying details removed except dates |
| **Update Lifecycle** | Continuous |

#### 3.2.4 Career Datasets (RS-CAREER)

| Field | Specification |
|---|---|
| **Purpose** | Specialized event dataset for career timing and professional achievement research |
| **Consumers** | VerificationEngine, StatisticsEngine, ResearchEngine |
| **Required Schema** | chart_id, occupation, industry, career_start_date, career_start_accuracy, significant_events (list of {date, event_type, description}), profession_category, income_level (optional), source |
| **Mandatory Metadata** | Occupation classification (ISCO standard or equivalent), event confidence per event |
| **Quality Requirements** | Profession verifiable from public or authoritative source; career milestones dated when possible |
| **Validation Rules** | Career start date ≥ education completion age (if both present); chronological order for milestones |
| **Versioning Strategy** | Part of RS-EVENT lifecycle |
| **Provenance** | Curated from biographical sources, public records |
| **Privacy Classification** | Pseudonymous for public figures; Anonymous for private individuals |
| **Update Lifecycle** | Continuous |

#### 3.2.5 Health Datasets (RS-HEALTH)

| Field | Specification |
|---|---|
| **Purpose** | Specialized event dataset for health, disease timing, and longevity research |
| **Consumers** | VerificationEngine, StatisticsEngine, ResearchEngine |
| **Required Schema** | chart_id, condition/disease, diagnosis_date, diagnosis_accuracy, severity, recovery_date (optional), chronic/acute, cause_of_death (optional), death_date (optional), source |
| **Mandatory Metadata** | Medical condition classification (ICD code recommended), diagnosis confidence, source type (medical record / family report / biographical) |
| **Quality Requirements** | Medical diagnoses from authoritative sources preferred; clearly flag self-reported or family-reported conditions |
| **Validation Rules** | Diagnosis date ≥ birth date; death date ≥ diagnosis date (if both present); age-appropriate conditions validated |
| **Versioning Strategy** | Part of RS-EVENT lifecycle |
| **Provenance** | Curated from biographies, medical records (with consent), obituaries |
| **Licensing Classification** | Per-source — medical data carries additional ethical restrictions |
| **Privacy Classification** | Anonymous — sensitive health data requires enhanced anonymization (HIPAA/GDPR considerations) |
| **Update Lifecycle** | Continuous |

#### 3.2.6 Wealth & Financial Datasets (RS-WEALTH)

| Field | Specification |
|---|---|
| **Purpose** | Specialized event dataset for wealth indicators, financial success, and prosperity research |
| **Consumers** | VerificationEngine, StatisticsEngine, ResearchEngine |
| **Required Schema** | chart_id, wealth_category (low/middle/high/very_high/ultra_high_net_worth), significant_financial_events (list of {date, event_type, amount_range, description}), primary_wealth_source, source |
| **Mandatory Metadata** | Wealth category definition methodology, date accuracy, source |
| **Quality Requirements** | Wealth classification based on verifiable data (income tax records, Forbes, public financial disclosures) |
| **Validation Rules** | Financial event dates chronological; wealth category consistent with documented events |
| **Versioning Strategy** | Part of RS-EVENT lifecycle |
| **Provenance** | Curated from public financial disclosures, Forbes lists, biographies |
| **Licensing Classification** | Per-source |
| **Privacy Classification** | Pseudonymous (wealth data of public figures); Anonymous for non-public figures |
| **Update Lifecycle** | Continuous |

#### 3.2.7 Spiritual & Progeny Datasets (RS-SPIRITUAL)

| Field | Specification |
|---|---|
| **Purpose** | Event datasets for spiritual milestones, children/birth, and progeny indicators |
| **Consumers** | VerificationEngine, StatisticsEngine, ResearchEngine |
| **Required Schema** | chart_id, event_type (spiritual_initiation, guru_meeting, enlightenment_experience, child_birth, adoption, etc.), event_date, event_accuracy, details, source |
| **Mandatory Metadata** | Event type classification, confidence, source |
| **Quality Requirements** | Spiritual events cross-referenced from biographical sources; progeny events from verified records |
| **Validation Rules** | Event dates chronological; parent age at child birth ≥ biological feasibility |
| **Versioning Strategy** | Part of RS-EVENT lifecycle |
| **Provenance** | Curated from biographies, spiritual lineage records, genealogical data |
| **Licensing Classification** | Per-source |
| **Privacy Classification** | Pseudonymous or Anonymous |
| **Update Lifecycle** | Continuous |

#### 3.2.8 Flattened Chart Records (RS-FLAT)

| Field | Specification |
|---|---|
| **Purpose** | Denormalized, flat chart records for bulk statistical analysis, ML training, and fast querying |
| **Consumers** | StatisticsEngine, AIEngine, ExportEngine, ReportEngine |
| **Required Schema** | Single flat record per chart containing: birth_metadata (date, time, place, lat, lng, tz) + 9× planet_positions (longitude, rashi, house, nakshatra, pada, dignity, retrograde, combust) + 12× house_cusps + lagna (rashi, degree) + moon_info + panchanga + 16× divisional_chart_placements + source_metadata |
| **Mandatory Metadata** | Calculation parameters (ayanamsa, house_system), engine version used, computation timestamp |
| **Quality Requirements** | All fields populated or explicitly null with rationale; engine version recorded for reproducibility |
| **Validation Rules** | Chandra (Moon) lagna consistent with Moon rashi; planetary longitudes 0°–360°; house numbers 1–12; divisional placements consistent with D1 positions via divisional formula |
| **Versioning Strategy** | Major: schema changes; Minor: new field additions; Schema version tracked per-record (different records may have been computed by different engine versions) |
| **Provenance** | Derived — computed from birth data through AstroOS calculation engines |
| **Licensing Classification** | Same as source birth data |
| **Privacy Classification** | Per-source (Public/Pseudonymous/Anonymous) |
| **Update Lifecycle** | Regenerated when calculation engine is updated or birth data corrected |

---

### 3.3 BENCHMARK DATASETS (BM)

Standardized comparisons test datasets for measuring system performance, accuracy, and capabilities. Used to compare engine versions, track regressions, and validate correctness.

#### 3.3.1 Calculation Accuracy Benchmarks (BM-CALC)

| Field | Specification |
|---|---|
| **Purpose** | Reference calculation pairs (input → expected output) for validating engine accuracy |
| **Consumers** | All calculation engines, CI/CD pipeline, QA |
| **Required Schema** | benchmark_id, engine_name, engine_version, calculation_type, input_parameters, expected_output, tolerance, source_reference |
| **Mandatory Metadata** | Expected output source (published ephemeris page number, NASA reference, etc.), tolerance justification |
| **Quality Requirements** | Each test case traceable to an authoritative external source (not self-referential); tolerance values justified by source precision |
| **Validation Rules** | Engine output must match expected output within specified tolerance; tolerance must be ≤0.001° for angular calculations |
| **Versioning Strategy** | Major: new reference sources; Minor: additional test cases; Patch: tolerance adjustments |
| **Provenance** | Derived from authoritative ephemeris tables, IAE, NASA JPL Horizons |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Extended as new engine versions are released |

#### 3.3.2 Aspect Detection Benchmarks (BM-ASPECT)

| Field | Specification |
|---|---|
| **Purpose** | Standardized test cases for aspect detection correctness |
| **Consumers** | AspectEngine, VerificationEngine |
| **Required Schema** | benchmark_id, planet_a, planet_b, position_a_deg, position_b_deg, ayanamsa_system, expected_aspect_type, expected_orb_deg, expected_applying_separating |
| **Mandatory Metadata** | Aspect definition reference (which classical tradition's rules are being tested) |
| **Quality Requirements** | Covers all aspect types (conjunction, opposition, trine, square, sextile, special graha); includes boundary cases (exact aspect, orb limit) |
| **Validation Rules** | Output aspect type matches expected; orb computed correctly; applying/separating determined correctly |
| **Versioning Strategy** | Extended per classical aspect system |
| **Provenance** | Derived from classical aspect definitions |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Extended as aspect systems are added |

#### 3.3.3 Dasha Calculation Benchmarks (BM-DASHA)

| Field | Specification |
|---|---|
| **Purpose** | Standardized test cases for Dasha timing accuracy |
| **Consumers** | DashaEngine, TimelineEngine |
| **Required Schema** | benchmark_id, dasha_type, birth_datetime_utc, moon_longitude, expected_mahadasha_lord, expected_mahadasha_start, expected_mahadasha_end, expected_antardasha_sequence |
| **Mandatory Metadata** | Dasha system source, expected values source |
| **Quality Requirements** | Covers all 9 lords, all balance dasha calculations, boundary cases (exact start/end dates) |
| **Validation Rules** | Mahadasha sequence matches Vimshottari lord order; antardasha sequence correct within each mahadasha; period lengths sum correctly |
| **Versioning Strategy** | Major: new dasha system; Minor: additional test cases |
| **Provenance** | Computed from reference birth data with known Dasha periods |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Extended as Dasha systems are added |

#### 3.3.4 Transit Benchmark (BM-TRANSIT)

| Field | Specification |
|---|---|
| **Purpose** | Standardized test cases for transit calculation accuracy |
| **Consumers** | TransitEngine, VerificationEngine |
| **Required Schema** | benchmark_id, natal_chart_params, transit_datetime_utc, planet, expected_transit_longitude, expected_transit_rashi, expected_natal_house_transited |
| **Mandatory Metadata** | Source for expected values |
| **Quality Requirements** | Covers all planets, all 12 rashis, retrograde periods, station points |
| **Validation Rules** | Transit longitude matches expected within tolerance; transit rashi correct; house overlay correct |
| **Versioning Strategy** | Extended per transit analysis feature |
| **Provenance** | Computed from reference charts at known transit dates |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Extended as transit features grow |

#### 3.3.5 Shadbala Benchmark (BM-BALA)

| Field | Specification |
|---|---|
| **Purpose** | Standardized test cases for Shadbala strength computation |
| **Consumers** | ShadbalaEngine |
| **Required Schema** | benchmark_id, chart_params, expected_shadbala_scores (per-planet, per-bala-component), expected_total_score |
| **Mandatory Metadata** | Shadbala formula reference (BPHS chapter and verse) |
| **Quality Requirements** | Covers all 6 bala components, all 9 planets, all rashis |
| **Validation Rules** | Per-component scores match formula; total = sum of components; score ranges within classical limits |
| **Versioning Strategy** | Extended per Shadbala refinement |
| **Provenance** | Computed from reference charts with manually verified scores |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Extended on engine refinements |

#### 3.3.6 Ashtakavarga Benchmark (BM-ASTAK)

| Field | Specification |
|---|---|
| **Purpose** | Standardized test cases for Ashtakavarga computation |
| **Consumers** | AshtakavargaEngine |
| **Required Schema** | benchmark_id, chart_params, expected_bhinnashtakavarga (per-planet), expected_samudaya_ashtakavarga, expected_total_ashtakavarga |
| **Mandatory Metadata** | Formula reference (BPHS chapter) |
| **Quality Requirements** | Covers all planets, all houses, boundary bindus |
| **Validation Rules** | Bindu counts within classical range (1-8 per house); totals sum correctly |
| **Versioning Strategy** | Extended per Ashtakavarga feature |
| **Provenance** | Computed from reference charts |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Extended on engine refinements |

#### 3.3.7 Divisional Chart Benchmark (BM-DIV)

| Field | Specification |
|---|---|
| **Purpose** | Standardized test cases for all 16 divisional chart calculations |
| **Consumers** | DivisionalEngine |
| **Required Schema** | benchmark_id, chart_params, divisional_type, expected_planet_placements (per-planet rashi + house for the divisional chart) |
| **Mandatory Metadata** | Formula reference for each divisional type |
| **Quality Requirements** | Covers all 16 division types; includes edge cases (exact boundaries, 0° Aries, 29°59' Pisces) |
| **Validation Rules** | Divisional placements consistent with D1 navamsha formula; house assignments correct for each division |
| **Versioning Strategy** | Major: new division type; Minor: additional test cases; Patch: corrections |
| **Provenance** | Computed from reference charts |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Extended on engine refinements |

#### 3.3.8 Performance Benchmarks (BM-PERF)

| Field | Specification |
|---|---|
| **Purpose** | Standardized performance test cases for measuring engine throughput and latency |
| **Consumers** | All engines, CI/CD pipeline, SRE |
| **Required Schema** | benchmark_id, engine_name, operation_type, input_data_ref, expected_max_latency_ms, expected_min_throughput_ops_per_sec |
| **Mandatory Metadata** | Hardware specification, measurement methodology, baseline version |
| **Quality Requirements** | Measured over ≥1000 iterations; median and p99 reported; hardware documented |
| **Validation Rules** | Latency ≤ expected_max_latency; throughput ≥ expected_min_throughput; no regression >10% vs. baseline |
| **Versioning Strategy** | Major: new hardware baseline; Minor: additional benchmarks |
| **Provenance** | Generated from controlled performance test runs |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Re-run on engine changes, CI/CD |

---

### 3.4 VALIDATION DATASETS (VL)

Used to validate that the system produces correct, consistent results across different contexts. Distinct from benchmarks in that they focus on correctness verification rather than comparison.

#### 3.4.1 Cross-Platform Validation (VL-XPLATFORM)

| Field | Specification |
|---|---|
| **Purpose** | Comparison results from external astrology software (Parashara's Light, Jagannatha Hora, Kala, etc.) for cross-validation |
| **Consumers** | VerificationEngine, QA, all calculation engines |
| **Required Schema** | test_id, chart_params, software_name, software_version, field_path, expected_value, tolerance |
| **Mandatory Metadata** | Target software name, version, settings used (ayanamsa, house system) |
| **Quality Requirements** | Differences between AstroOS and target software documented (not assumed same); tolerance levels explicitly stated |
| **Validation Rules** | AstroOS output within tolerance of target software; deviations documented with rationale |
| **Versioning Strategy** | Per target software version |
| **Provenance** | Computed using third-party astrology software |
| **Licensing Classification** | Internal (validation results owned by AstroOS project) |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Updated when target software releases new versions |

#### 3.4.2 End-to-End Chart Validation (VL-CHART)

| Field | Specification |
|---|---|
| **Purpose** | Complete chart calculations (birth chart → all outputs) as end-to-end validation cases |
| **Consumers** | All calculation engines, QA |
| **Required Schema** | chart_id, birth_data, expected_results (full set: planet_positions, rashis, houses, nakshatras, aspects, yogas, dashas, shadbala, ashtakavarga, divisional_positions) |
| **Mandatory Metadata** | Expected results source (published chart example, verified calculation, cross-checked with 2nd software), engine version used for expected values |
| **Quality Requirements** | Industry-standard example charts; results verified by ≥2 independent methods |
| **Validation Rules** | Every output field within tolerance; internal consistency checks (e.g., planet.rashi matches planet.longitude → rashi) |
| **Versioning Strategy** | Major: schema additions; Minor: new charts; Patch: corrections |
| **Provenance** | Multiple — sourced from textbooks, verified charts, cross-validation |
| **Licensing Classification** | Per-source (textbook charts often need attribution) |
| **Privacy Classification** | Public (example charts only) |
| **Update Lifecycle** | Extended as new example charts are identified |

#### 3.4.3 Consistency Validation (VL-CONSISTENCY)

| Field | Specification |
|---|---|
| **Purpose** | Internal consistency rules that every computed chart must satisfy |
| **Consumers** | All engines, CI pipeline |
| **Required Schema** | rule_id, description, validation_query, severity (error/warning), affected_components |
| **Mandatory Metadata** | Rationale for each consistency rule |
| **Quality Requirements** | Rules must be automatable; every rule has non-null expected output |
| **Validation Rules** | (meta-rules) Each consistency rule fires correctly on violations and does not fire on valid data |
| **Versioning Strategy** | Minor: new rules; Major: rule semantics change |
| **Provenance** | Derived from astrological invariants |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Extended as new invariants are identified |

---

### 3.5 QA/TEST DATASETS (QT)

Used for software quality assurance — regression testing, integration testing, stress testing, and edge case coverage.

#### 3.5.1 Regression Test Charts (QT-REGRESSION)

| Field | Specification |
|---|---|
| **Purpose** | Canonical set of charts that every engine release must produce identical results for |
| **Consumers** | CI/CD, all engines, QA |
| **Required Schema** | chart_id, birth_data, calculation_params, expected_hash (SHA-256 of engine output for each engine), last_verified_version |
| **Mandatory Metadata** | What each chart tests (specific planetary configurations, edge cases) |
| **Quality Requirements** | 100% reproducible; hash comparison ensures bit-exact consistency |
| **Validation Rules** | Engine output hash must match expected hash for same engine version; hash changes expected when engine intentionally changes |
| **Versioning Strategy** | Major: engine version incompatible; Minor: new regression charts |
| **Provenance** | Curated from real charts exhibiting specific test-worthy configurations |
| **Licensing Classification** | Internal |
| **Privacy Classification** | Anonymous |
| **Update Lifecycle** | Extended per engine milestone |

#### 3.5.2 Edge Case Charts (QT-EDGE)

| Field | Specification |
|---|---|
| **Purpose** | Charts at boundary conditions — exact 0° Aries, 29°59' boundaries, polar latitudes, birth date boundaries (Feb 29, 1800, etc.) |
| **Consumers** | All engines, CI/CD |
| **Required Schema** | chart_id, birth_data, edge_type, known_issues (expected failures or edge-case behavior), workaround_notes |
| **Mandatory Metadata** | Edge case classification, expected behavior (may be graceful error, not necessarily correct output) |
| **Quality Requirements** | Coverage of known boundary conditions for all calculation domains |
| **Validation Rules** | Engine does not crash; error states are handled gracefully with meaningful error messages |
| **Versioning Strategy** | Extended as new edge cases discovered; never removed |
| **Provenance** | Manually curated |
| **Licensing Classification** | Internal |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Continuous — add as edge cases are discovered in production |

#### 3.5.3 Stress/Volume Test Data (QT-STRESS)

| Field | Specification |
|---|---|
| **Purpose** | Large-volume chart datasets for performance and stability testing under load |
| **Consumers** | All engines, CI/CD, performance testing |
| **Required Schema** | Auto-generated: random_valid_birth_data, repeatable (seeded RNG), generation_metadata (count, seed, date_range, location_distribution) |
| **Mandatory Metadata** | Generation parameters, total count, date range |
| **Quality Requirements** | All birth data must be valid (realistic dates, achievable coordinates); seeded for reproducibility; distribution should approximate real demographic distribution |
| **Validation Rules** | All generated charts calculable (no crash); output within consistency rules |
| **Versioning Strategy** | Minor: new seed values or volumes |
| **Provenance** | Synthetic (computer-generated parameter combinations) |
| **Licensing Classification** | Internal |
| **Privacy Classification** | Public (no real persons involved) |
| **Update Lifecycle** | Extended per testing need |

#### 3.5.4 Integration Test Scenarios (QT-INTEGRATION)

| Field | Specification |
|---|---|
| **Purpose** | Multi-step test scenarios that exercise end-to-end workflows (chart create → dasha compute → event verify → report generate) |
| **Consumers** | All engines, integration test suite |
| **Required Schema** | scenario_id, description, steps (ordered list of {engine, input, expected_intermediate, preconditions}), expected_final_state |
| **Mandatory Metadata** | What user workflow this scenario represents |
| **Quality Requirements** | Each scenario represents a real user workflow; covers success path and at least one error path |
| **Validation Rules** | Each step produces expected intermediate; final state matches expectation; rollback/cleanup works |
| **Versioning Strategy** | Major: workflow changes; Minor: new scenarios |
| **Provenance** | Curated from use case analysis |
| **Licensing Classification** | Internal |
| **Privacy Classification** | Anonymous |
| **Update Lifecycle** | Extended per new feature/integration |

---

### 3.6 AI EVALUATION DATASETS (AI)

Designed specifically to evaluate, train, and benchmark AI models (LLMs used for interpretation, report generation, or analysis).

#### 3.6.1 Chart Interpretation Benchmarks (AI-INTERP)

| Field | Specification |
|---|---|
| **Purpose** | Standardized chart interpretation tasks to evaluate AI model quality |
| **Consumers** | AIEngine, ReportEngine, AI evaluation pipeline |
| **Required Schema** | prompt_id, chart_data_ref, prompt_template, reference_interpretation (human-written, authoritative), evaluation_criteria (factual_accuracy, completeness, classical_rigor, hallucination_check), scoring_rubric |
| **Mandatory Metadata** | Interpretation tradition (BPHS-based, KP-based, etc.), reference source, difficulty level |
| **Quality Requirements** | Reference interpretations written or reviewed by a qualified Jyotish scholar; evaluation criteria include hallucination detection |
| **Validation Rules** | AI output checked against reference for factual assertions; any claim not present in reference flagged as potential hallucination |
| **Versioning Strategy** | Major: new interpretation categories; Minor: additional test charts |
| **Provenance** | Reference interpretations: curated from classical texts; chart data: from public/verified sources |
| **Licensing Classification** | Research/Academic |
| **Privacy Classification** | Public charts only (no identifiable individuals for AI training) |
| **Update Lifecycle** | Extended as new AI capabilities are evaluated |

#### 3.6.2 Interpretation Hallucination Detection (AI-HALLUC)

| Field | Specification |
|---|---|
| **Purpose** | Targeted test cases designed to detect AI hallucination in astrological interpretations |
| **Consumers** | AIEngine, AI evaluation pipeline, QA |
| **Required Schema** | test_id, chart_data_ref, prompt, known_hallucination_patterns (list of claims AIs commonly fabricate), ground_truth_assertions, common_misconceptions_in_this_context |
| **Mandatory Metadata** | Source of truth for each assertion (classical text reference) |
| **Quality Requirements** | Covers known hallucination types (fabricated yogas, incorrect rulerships, impossible planetary combinations, invented textual references) |
| **Validation Rules** | AI output must not assert any claim from known_hallucination_patterns list; all factual assertions must match ground_truth |
| **Versioning Strategy** | Extended as new hallucination patterns are discovered |
| **Provenance** | Curated from known AI failure patterns in astrology |
| **Licensing Classification** | Research |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Continuous — extended as new hallucination types emerge |

#### 3.6.3 Factual Accuracy Tests (AI-FACT)

| Field | Specification |
|---|---|
| **Purpose** | Targeted factual questions about astrological principles, not chart-dependent |
| **Consumers** | AIEngine, AI evaluation pipeline |
| **Required Schema** | question_id, question, expected_answer, source_reference, difficulty, topic_area |
| **Mandatory Metadata** | Source reference for correct answer |
| **Quality Requirements** | Every question answerable from standard classical texts; no ambiguous/opinion questions |
| **Validation Rules** | Fact assertion must match expected answer; unsupported additions flagged as potential hallucination |
| **Versioning Strategy** | Extended per topic area |
| **Provenance** | Curated from classical Jyotish texts |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Extended as new topics are added |

#### 3.6.4 Report Generation Benchmarks (AI-REPORT)

| Field | Specification |
|---|---|
| **Purpose** | Standardized report generation tasks to evaluate AI report quality |
| **Consumers** | AIEngine, ReportEngine |
| **Required Schema** | report_id, chart_data_ref, report_type (full/birth_chart/summary/annual_transit/relationship/integration_params), human_written_reference, quality_criteria (structure, completeness, accuracy, readability, personalization) |
| **Mandatory Metadata** | Target audience level (beginner/intermediate/advanced), report length target |
| **Quality Requirements** | Reference reports written by human astrologers; evaluation criteria include factual accuracy and completeness |
| **Validation Rules** | All calculations in report match deterministic engine output; no invented interpretations; report structure follows specification |
| **Versioning Strategy** | Major: new report types; Minor: additional examples |
| **Provenance** | Human-written reference reports + calculated charts |
| **Licensing Classification** | Research |
| **Privacy Classification** | Anonymous |
| **Update Lifecycle** | Extended per report type |

#### 3.6.5 Rule Evaluation Benchmarks (AI-RULE)

| Field | Specification |
|---|---|
| **Purpose** | Test cases for AI-assisted rule evaluation and interpretation correctness |
| **Consumers** | AIEngine, RuleEngine, AI evaluation pipeline |
| **Required Schema** | test_id, chart_data_ref, rule_ref, expected_rule_evaluation, expected_interpretation_key_points |
| **Mandatory Metadata** | Rule source (text, verse), tradition |
| **Quality Requirements** | Covers all major rule categories (dignity, house lords, yoga, transit, compound) |
| **Validation Rules** | Rule evaluation correct per deterministic rule definition; interpretation consistent with classical meaning |
| **Versioning Strategy** | Extended per rule category |
| **Provenance** | Curated from classical texts + verified evaluations |
| **Licensing Classification** | Research |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Extended as rule engine grows |

---

### 3.7 SYNTHETIC DATASETS (SY)

Artificially generated chart datasets for controlled experiments, statistical baselines, and testing where real data is unavailable or inappropriate.

#### 3.7.1 Random Birth Cohorts (SY-RANDOM)

| Field | Specification |
|---|---|
| **Purpose** | Statistically random birth datasets for null hypothesis testing, distribution analysis, and Monte Carlo studies |
| **Consumers** | StatisticsEngine, ResearchEngine, AIEngine |
| **Required Schema** | cohort_id, generation_parameters (seed, count, date_range, geographic_distribution, time_distribution), chart_list, expected_uniform_distributions |
| **Mandatory Metadata** | Random seed (for reproducibility), distribution type (uniform/weighted/realistic), date range geographic bounds |
| **Quality Requirements** | Truely pseudorandom (seeded, reproducible); date/time/location distribution documented; ≥10,000 records for robust statistics |
| **Validation Rules** | Distribution tests (chi-squared) confirm expected uniform distribution of rashis, nakshatras, ascendants; no demographic bias introduced |
| **Versioning Strategy** | Per seed value — each seed is a version |
| **Provenance** | Generated (seeded pseudorandom algorithm) |
| **Licensing Classification** | Public (no real data) |
| **Privacy Classification** | Public (no real persons involved) |
| **Update Lifecycle** | Generated on demand for specific studies |

#### 3.7.2 Controlled Experiment Charts (SY-CONTROLLED)

| Field | Specification |
|---|---|
| **Purpose** | Purpose-built charts with specific planetary configurations for controlled experiments (isolating one variable) |
| **Consumers** | ResearchEngine, VerificationEngine, StatisticsEngine |
| **Required Schema** | experiment_id, controlled_parameters, varied_parameters, constant_parameters, chart_list, hypothesis |
| **Mandatory Metadata** | Which parameters are controlled (constant), which are varied, research hypothesis |
| **Quality Requirements** | Only the specified parameter varies between control and experiment groups; all other parameters held constant |
| **Validation Rules** | Verify controlled parameters are identical across groups; verify varied parameter differs only in expected ways |
| **Versioning Strategy** | Per experiment design |
| **Provenance** | Generated (constructed to meet experimental design specifications) |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Single-use per experiment; archived for reproducibility |

#### 3.7.3 Monte Carlo Reference Datasets (SY-MONTE)

| Field | Specification |
|---|---|
| **Purpose** | Large-scale random chart data for distribution analysis of astrological parameters (base rates) |
| **Consumers** | StatisticsEngine, ResearchEngine |
| **Required Schema** | run_id, seed, sample_size, date_range_start, date_range_end, geographic_distribution_params, computed_distributions (per-parameter histograms, moments), engine_version |
| **Mandatory Metadata** | Complete generation specifications for reproducibility |
| **Quality Requirements** | Sample size ≥100,000 for stable distribution estimates |
| **Validation Rules** | Distribution moments converge with increasing sample size (stability check at n=10k, 50k, 100k) |
| **Versioning Strategy** | Per run (seed + parameters = version) |
| **Provenance** | Generated |
| **Licensing Classification** | Public |
| **Privacy Classification** | Public |
| **Update Lifecycle** | Generated on demand |

#### 3.7.4 Null Hypothesis Baselines (SY-NULL)

| Field | Specification |
|---|---|
| **Purpose** | Control datasets designed to have no astrological significance (randomized placements, shuffled events) for testing statistical significance |
| **Consumers** | StatisticsEngine, ResearchEngine, VerificationEngine |
| **Required Schema** | baseline_id, original_dataset_ref (if derived), randomization_method, seed, resulting_distributions |
| **Mandatory Metadata** | Randomization method (label_shuffle, date_shuffle, time_randomization), methodological justification |
| **Quality Requirements** | Randomization destroys any real signal while preserving marginal distributions (e.g., same date distribution, same location distribution) |
| **Validation Rules** | Paired test shows original vs. shuffled differ only in astrological alignment (not marginals); p-value distribution uniform under null |
| **Versioning Strategy** | Per randomization seed |
| **Provenance** | Derived from real data by randomization |
| **Licensing Classification** | Same as source data (no PII exposure in shuffled form) |
| **Privacy Classification** | Same as source data |
| **Update Lifecycle** | Generated on demand |

---

### 3.8 PUBLIC DATASETS (PB)

Datasets sourced from publicly available data that are legally usable and redistributable.

#### 3.8.1 Wikipedia Birth Chart Collection (PB-WIKI)

| Field | Specification |
|---|---|
| **Purpose** | Birth data extracted from Wikipedia infoboxes for notable individuals |
| **Consumers** | ResearchEngine, StatisticsEngine, AIEngine, VerificationEngine |
| **Required Schema** | chart_id, wikipedia_title, wikipedia_url, birth_date, birth_date_accuracy, birth_place, birth_place_coordinates, timezone, profession, known_for, notability_metric (page_views, article_quality), source_extraction_date |
| **Mandatory Metadata** | Source URL, extraction date, birth time source method (infobox / body text / unknown) |
| **Quality Requirements** | Birth dates verified against at least 2 independent sources when possible; birth times flagged as missing/estimated/verified |
| **Validation Rules** | Birth date must exist in Wikipedia infobox; names cross-referenced with Wikidata; duplicate detection by Wikidata ID |
| **Versioning Strategy** | Major: extraction methodology change; Minor: updated extraction; Patch: individual corrections |
| **Provenance** | Extracted from Wikipedia (CC-BY-SA / GFDL licensed content) |
| **Licensing Classification** | Public — CC-BY-SA 3.0 (attribute Wikipedia) |
| **Privacy Classification** | Public (notable individuals; data from public sources) |
| **Update Lifecycle** | Quarterly re-extraction to capture new articles and corrections |

#### 3.8.2 Wikidata Filtered Charts (PB-WIKIDATA)

| Field | Specification |
|---|---|
| **Purpose** | Structured birth data from Wikidata query service with verified properties |
| **Consumers** | ResearchEngine, StatisticsEngine |
| **Required Schema** | chart_id, wikidata_id, label, birth_date, birth_date_precision (9=year, 10=decade, 11=century), birth_place, birth_place_coordinates, country, occupation (multiple), occupation_category, source_wikidata_version |
| **Mandatory Metadata** | Date precision level (P571 precision property), property IDs used |
| **Quality Requirements** | Only records with birth date precision ≥9 (year) included; occupations mapped to standardized categories |
| **Validation Rules** | Wikidata ID resolvable; birth date consistent across language editions; coordinate precision documented |
| **Versioning Strategy** | Per SPARQL query version |
| **Provenance** | Queried from Wikidata (CC-0 licensed structured data) |
| **Licensing Classification** | Public — CC-0 (Wikidata structured data) |
| **Privacy Classification** | Public (notable individuals) |
| **Update Lifecycle** | Quarterly re-query |

#### 3.8.3 Public Figure Event Collection (PB-EVENTS)

| Field | Specification |
|---|---|
| **Purpose** | Verified life events of public figures collected from published biographies |
| **Consumers** | VerificationEngine, StatisticsEngine, ResearchEngine |
| **Required Schema** | chart_id, event_date, event_type, event_detail, source_description, source_url, confidence, extractor_notes |
| **Mandatory Metadata** | Source URL/book reference, event date accuracy, confidence (verified from multiple sources vs. single source) |
| **Quality Requirements** | Events sourced from published, citable sources; each event traceable to a specific reference |
| **Validation Rules** | Event date ≥ birth date; event date ≤ death date (if deceased); chronological ordering |
| **Versioning Strategy** | Major: schema changes; Minor: new batches of events |
| **Provenance** | Extracted from biographies, obituaries, news archives |
| **Licensing Classification** | Per source — biographical facts are public; text extracts may carry copyright |
| **Privacy Classification** | Public (public figures) |
| **Update Lifecycle** | Continuous |

#### 3.8.4 Known Twin Charts (PB-TWIN)

| Field | Specification |
|---|---|
| **Purpose** | Birth charts of twins (identical and fraternal) for nature-vs-nurture and timing-sensitivity research |
| **Consumers** | ResearchEngine, StatisticsEngine, VerificationEngine |
| **Required Schema** | twin_pair_id, twin_type (identical/fraternal), birth_order, chart_A, chart_B, birth_interval_minutes, known_life_differences, source |
| **Mandatory Metadata** | Twin type, birth interval accuracy, source verification level |
| **Quality Requirements** | Birth times from verified medical records preferred; birth interval precise to minute when possible |
| **Validation Rules** | Birth dates must be same day (or consecutive for midnight cases); birth interval ≥0 minutes; birth order documented |
| **Versioning Strategy** | Extended as new twin pairs are identified |
| **Provenance** | Curated from medical studies, biographical data, twin registries |
| **Licensing Classification** | Per source |
| **Privacy Classification** | Anonymous (twin studies require enhanced privacy) |
| **Update Lifecycle** | Continuous |

---

### 3.9 LICENSED/COMMERCIAL DATASETS (LC)

Datasets obtained through commercial licenses, research agreements, or restricted-access sources.

#### 3.9.1 Swiss Ephemeris Professional (LC-SWISS)

| Field | Specification |
|---|---|
| **Purpose** | Licensed Swiss Ephemeris professional data files (higher precision, expanded body set) |
| **Consumers** | EphemerisEngine |
| **Required Schema** | Same as RF-EPHEM |
| **Mandatory Metadata** | License type, expiration date, license key reference (not the key itself), usage restrictions |
| **Quality Requirements** | Higher precision than free version; includes additional astronomical bodies |
| **Validation Rules** | Same as RF-EPHEM |
| **Versioning Strategy** | Per Swiss Ephemeris release |
| **Provenance** | Licensed from Astrodienst |
| **Licensing Classification** | Licensed — commercial use requires paid license |
| **Privacy Classification** | Public (no personal data) |
| **Update Lifecycle** | Per Swiss Ephemeris release cycle |

#### 3.9.2 Licensed Birth Chart Collections (LC-CHART)

| Field | Specification |
|---|---|
| **Purpose** | Birth chart datasets obtained through commercial data licenses or research agreements |
| **Consumers** | ResearchEngine, StatisticsEngine, AIEngine |
| **Required Schema** | Per source agreement (may be restricted) |
| **Mandatory Metadata** | License terms, data provenance, permitted uses, expiration, attribution requirements |
| **Quality Requirements** | Per license agreement |
| **Validation Rules** | Per license agreement |
| **Versioning Strategy** | Per source |
| **Provenance** | Licensed from data vendors, research institutions, or data collection agreements |
| **Licensing Classification** | Licensed — restricted use per agreement |
| **Privacy Classification** | Per agreement (typically Anonymous or Pseudonymous) |
| **Update Lifecycle** | Per license agreement |

#### 3.9.3 Research Partner Data (LC-PARTNER)

| Field | Specification |
|---|---|
| **Purpose** | Datasets shared by research partners under data-sharing agreements |
| **Consumers** | ResearchEngine, StatisticsEngine |
| **Required Schema** | Per partner agreement |
| **Mandatory Metadata** | Partner name, data-sharing agreement reference, permitted uses, restrictions, embargo period |
| **Quality Requirements** | Per agreement |
| **Validation Rules** | Per agreement |
| **Versioning Strategy** | Per partner release |
| **Provenance** | Provided by research partners |
| **Licensing Classification** | Restricted — per data-sharing agreement |
| **Privacy Classification** | Per agreement (typically Anonymous or Private) |
| **Update Lifecycle** | Per partner schedule |

---

### 3.10 USER-CONTRIBUTED DATASETS (UC)

Datasets created by end users through the platform — birth charts, events, and research contributions. These are the most privacy-sensitive category.

#### 3.10.1 User Birth Charts (UC-USER)

| Field | Specification |
|---|---|
| **Purpose** | Birth charts created by platform users for their own use |
| **Consumers** | User's own research, ReportEngine (per-user), AIEngine (per-user) |
| **Required Schema** | Per database schema (birth_charts table) with user_id ownership |
| **Mandatory Metadata** | Ownership info, creation timestamp, consent flags, data sharing preferences |
| **Quality Requirements** | User-provided data validated at input; birth time accuracy flagged (user-declared) |
| **Validation Rules** | Date/time range validation; location existence validation; timezone lookup validation; duplicate detection |
| **Versioning Strategy** | Per record (immutable after creation; corrections create new version with audit trail) |
| **Provenance** | User-submitted through platform UI/API |
| **Licensing Classification** | User-owned — AstroOS has usage license per terms of service |
| **Privacy Classification** | Private — user-owned data; access restricted to user and authorized researchers only with explicit consent |
| **Update Lifecycle** | User-managed; retained until user deletion or platform policy expiration |

#### 3.10.2 User-Contributed Events (UC-EVENT)

| Field | Specification |
|---|---|
| **Purpose** | Life events contributed by users for their own charts or for anonymized research |
| **Consumers** | VerificationEngine (per-user), StatisticsEngine (anonymous aggregates only) |
| **Required Schema** | chart_id, event_date, event_type, description, confidence (self-assessed), is_public (opt-in for research) |
| **Mandatory Metadata** | Ownership, consent status, contribution timestamp |
| **Quality Requirements** | User-reported (not independently verified); clearly labeled as such |
| **Validation Rules** | Event date consistent with birth date; duplicate detection; profanity/content moderation |
| **Versioning Strategy** | User-managed per record |
| **Provenance** | User-submitted |
| **Licensing Classification** | User-owned; research usage depends on explicit consent flag |
| **Privacy Classification** | Private by default; Anonymous (with explicit consent) when opted into research |
| **Update Lifecycle** | User-managed |

#### 3.10.3 Community Research Cohorts (UC-COHORT)

| Field | Specification |
|---|---|
| **Purpose** | Research cohorts defined and shared by the community of researchers using AstroOS |
| **Consumers** | ResearchEngine, StatisticsEngine |
| **Required Schema** | cohort_id, creator_id, shared_publicly, member_chart_refs (anonymous refs or user-specific refs), inclusion_criteria, description |
| **Mandatory Metadata** | Creator attribution, sharing scope, inclusion criteria, creation methodology |
| **Quality Requirements** | Cohort criteria must be documented and reproducible; shared cohorts must only reference anonymous chart IDs |
| **Validation Rules** | Reproducibility check; privacy audit (shared cohorts cannot expose user identities) |
| **Versioning Strategy** | Per cohort definition version |
| **Provenance** | User-curated |
| **Licensing Classification** | Per creator terms; platform standard terms for shared cohorts |
| **Privacy Classification** | Anonymous (shared cohorts must be fully de-identified) |
| **Update Lifecycle** | Creator-managed |

---

## 4. Cross-Cutting Concerns

### 4.1 Privacy Classification — Detail

| Tier | Definition | Examples | Requirements |
|---|---|---|---|
| **Public** | No personal data | Reference tables, synthetic data, benchmarks | None |
| **Anonymous** | Data about persons but all identifiers removed | Research cohorts without names/dates/locations | Irreversible de-identification; no re-identification risk |
| **Pseudonymous** | Direct identifiers removed but stable pseudonym used for linkage | Public figures with DOI-based IDs, event datasets | Mapping table stored separately, access-controlled |
| **Private** | Identifiable personal data | User accounts, user chart data | Encryption at rest; access control; user consent; GDPR compliance |
| **Restricted** | Legally protected data | Medical records, partner data with agreements | All of Private + audit logging; DPA required; no export without explicit authorization |

### 4.2 Confidence Classification — Detail

| Tier | Definition | Color Code | Data Requirements |
|---|---|---|---|
| **Verified** | Confirmed by ≥2 independent reliable sources | Green | Source citations required; verification date recorded |
| **Estimated** | Derived from known data with reasonable inference (e.g., birth time from known time of birth ± 1 hour family recollection) | Yellow | Estimation method documented; confidence interval recorded |
| **Rectified** | Adjusted from original data using astrological rectification methods | Orange | Rectification method documented; rectifier attribution; original data preserved alongside rectified |
| **Synthetic** | Artificially generated — does not represent any actual person | Blue | Generation method documented; seed/parameters recorded |
| **Unknown** | No basis to assess accuracy | Gray | Explicitly flagged; not used for any analysis without user awareness |

### 4.3 Dataset Lifecycle

```
┌──────────┐
│  DRAFT   │  Initial specification, no data collected
└────┬─────┘
     │
┌────▼──────┐
│ CANDIDACY │  Data collected, under review for quality
└────┬──────┘
     │
┌────▼────┐
│ STABLE  │  Quality approved, available for use
└────┬────┘
     │
┌────▼────────┐
│ DEPRECATED  │  Superseded or withdrawn; still accessible but not recommended
└────┬────────┘
     │
┌────▼──────┐
│ ARCHIVED  │  Historical only; read-only; preserved for reproducibility
└──────────┘
```

### 4.4 Versioning Convention

All datasets follow Semantic Versioning (SemVer 2.0):

| Bump | When | Example |
|------|------|---------|
| **MAJOR** | Schema changes, incompatible format changes, irreproducible changes | v1.0.0 → v2.0.0 |
| **MINOR** | Additions (new records, new fields), backward-compatible | v1.0.0 → v1.1.0 |
| **PATCH** | Corrections, metadata updates, no semantic change | v1.0.0 → v1.0.1 |

Each version is immutable once published. A dataset version is never overwritten — corrections always create a new version with a changelog entry.

### 4.5 Required Common Metadata

Every dataset, regardless of category, MUST define:

| Field | Description |
|---|---|
| `dataset_id` | Permanent unique ID (ASTRO-{CAT}-{TYPE}-v{X.Y.Z}) |
| `name` | Human-readable name |
| `description` | Purpose and scope |
| `category` | From taxonomy categories |
| `version` | Semantic version string |
| `created_at` | ISO 8601 timestamp |
| `updated_at` | ISO 8601 timestamp |
| `maintainer` | Responsible entity/role |
| `license` | SPDX license identifier or custom |
| `privacy_tier` | Public/Anonymous/Pseudonymous/Private/Restricted |
| `confidence_tier` | Verified/Estimated/Rectified/Synthetic/Unknown |
| `provenance_tier` | Primary/Derived/Curated/Generated/Contributed |
| `size` | Record count |
| `schema_ref` | Link to schema definition |
| `checksum` | SHA-256 hash of dataset file |
| `changelog` | Link to changelog |
| `validation_status` | Unvalidated/Validated/Failed |
| `quality_score` | 0.0–1.0 |
| `known_limitations` | Documented gaps and caveats |
| `ethical_notes` | Ethical considerations for this dataset |

---

## 5. Candidate Source Pre-Assessment

Pending final evaluation, the following known external sources are tentatively categorized:

| Source | Type | Category | Notes |
|---|---|---|---|
| LOKPA_Persons_WithEvents.csv | Birth charts + events | PB | 28,247 records; needs license evaluation |
| Swiss Ephemeris (existing) | Ephemeris data | RF-EPHEM | Already in use; dual-license |
| Wikipedia infobox data | Birth charts | PB-WIKI | CC-BY-SA; extraction needed |
| Wikidata SPARQL query | Birth data | PB-WIKIDATA | CC-0; structured; query needed |
| AstroDatabank | Birth charts | PB (or LC) | Public research data; verify license |
| Astro-Databank (Astrodienst) | Birth charts | LC-CHART | Commercial; verify license terms |
| JPL Horizons API | Ephemeris | RF-EPHEM | Public; API query needed |
| IANA tzdata | Timezones | RF-TZ | Public domain; quarterly updates |
| Classical Jyotish texts | Reference | RF-* | Public domain (ancient texts) |
| User submissions | Birth charts | UC-USER | Privacy-intensive; requires consent framework |

---

## 6. Taxonomy Summary

| Category | Code | # Types | Examples | Primary Consumers |
|---|---|---|---|---|
| Reference | RF | 10 | Ephemeris, Signs, Nakshatras, Padas, Planets, Houses, Karakas, Ayanamsa, Dashas, Timezones | All engines |
| Research | RS | 7 | Cohorts, Events, Marriage, Career, Health, Wealth, Flattened Charts | StatisticsEngine, ResearchEngine |
| Benchmark | BM | 8 | Calc Accuracy, Aspect, Dasha, Transit, Shadbala, Ashtakavarga, Divisional, Performance | CI/CD, QA, all engines |
| Validation | VL | 3 | Cross-Platform, End-to-End Charts, Consistency Rules | QA, VerificationEngine |
| QA/Test | QT | 4 | Regression, Edge Cases, Stress/Volume, Integration | CI/CD, QA |
| AI Evaluation | AI | 5 | Chart Interpretation, Hallucination Detection, Factual Accuracy, Report Gen, Rule Eval | AIEngine, AI Eval pipeline |
| Synthetic | SY | 4 | Random Cohorts, Controlled Experiments, Monte Carlo, Null Baselines | StatisticsEngine, ResearchEngine |
| Public | PB | 4 | Wikipedia, Wikidata, Public Figure Events, Twins | ResearchEngine, StatisticsEngine |
| Licensed | LC | 3 | Swiss Ephemeris Pro, Licensed Charts, Research Partner Data | EphemerisEngine, ResearchEngine |
| User-Contributed | UC | 3 | User Charts, User Events, Community Cohorts | User-facing, ResearchEngine (anonymous aggregate) |
| **TOTAL** | | **51** | | |

---

*End of Phase 2: Dataset Taxonomy. Awaiting approval to proceed to Phase 3: Dataset Standards.*
