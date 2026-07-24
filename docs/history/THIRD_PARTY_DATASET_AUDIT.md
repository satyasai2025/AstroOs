# Third-Party Branded Dataset Audit

> **Auditor:** Research Data Officer (Agent 5)
> **Date:** 2026-07-17
> **Scope:** All third-party branded dataset references in the AstroOS repository
> **Mission:** Identify unnecessary references to datasets no longer part of AstroOS
> **Status:** COMPLETE — awaiting approval before any modifications

---

## Executive Summary

The repository was searched for references to **AstroDatabank**, **LoKPā/Lokpa**, and any other external branded dataset names. Two primary candidates for cleanup were identified:

| Dataset | Status | Occurrences | Files | Action |
|---------|--------|-------------|-------|--------|
| **LOKPA** | Already rejected (GD-001) — not part of AstroOS | 23 | 7 | Remove all references |
| **AstroDatabank** | Source data imported as RS-COHORT; adapter/import pipeline exists | ~66 | 13 | Rename everything — no third-party attribution needed (the data is AstroOS's own curated collection, mislabeled) |

Additionally, ~20 other branded/external names were found (Swiss Ephemeris, JPL Horizons, ayanamsa systems, etc.) but these are **actively used** calculation dependencies — not candidates for removal.

---

## 1. LOKPA (`LOKPA_Persons_WithEvents.csv`)

### Status
- **Evaluated by:** Chief Dataset & Research Curator (2026-07-15)
- **Outcome:** **REJECTED** — governance decision GD-001 resolved as "Reject — do not use"
- **Reason:** 28,246-record CSV from unknown source; license could not be verified
- **File location:** `C:\Users\rkmau\Downloads\LOKPA_Persons_WithEvents.csv` (NOT in repo)

### All Occurrences (23 matches across 7 files)

All occurrences use the uppercase form **LOKPA** (never "LoKPā" with macron). No matches in Python source code, JSON, YAML, or config files — only in markdown documentation.

| # | File | Line(s) | Context | Classification | Risk |
|---|------|---------|---------|----------------|------|
| 1 | `research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md` | 380, 382, 384, 393 | Used as comparison metric ("Based on LOKPA Analysis") | **A. Documentation** | Low — comparative reference in AstroDatabank doc |
| 2 | `research-data/pipelines/candidate-datasets/LOKPA_Candidate_Evaluation_Report.md` | 3, 16–17, 307 | Full evaluation report recommending rejection | **A. Documentation** | Medium — entire file is about LOKPA |
| 3 | `research-data/RESEARCH_DATA_MIGRATION_REPORT.md` | 24, 67, 69–70 | Migration status notes referencing LOKPA evaluation | **A. Documentation** | Low |
| 4 | `research-data/governance/astrosos-dataset-taxonomy.md` | 1067 | Candidate source pre-assessment table entry | **A. Documentation** | Low |
| 5 | `research-data/ROADMAP.md` | 69, 73, 162, 175, 204 | Roadmap milestones mentioning LOKPA decision | **A. Documentation** | Low |
| 6 | `research-data/COMPLETION_REPORT.md` | 120, 132, 145, 172 | Completion report noting LOKPA decision | **A. Documentation** | Low |
| 7 | `research-data/STATUS.md` | 154, 158, 166, 180 | Status report: GD-001 resolved, LOKPA rejected | **A. Documentation** | Low |

### Recommended Action

**SAFE TO REMOVE** all LOKPA references. The dataset was evaluated and rejected. There is no license requirement to retain attribution. Documentation references are historical audit trails only.

| File | Recommended Action | Detail |
|------|-------------------|--------|
| `LOKPA_Candidate_Evaluation_Report.md` | **Remove entire file** | The only purpose of this file is to document the evaluation of a rejected dataset |
| `AstroDatabank_Canonical_Mapping.md` | **Remove LOKPA comparison section** (lines ~380–416) | The LOKPA comparison was used for scale estimation against AstroDatabank; replace with generic benchmarks |
| `astrosos-dataset-taxonomy.md` | **Remove LOKPA entry** from candidate sources table (line 1067) | Candidate no longer under consideration |
| `ROADMAP.md` | **Remove or rewrite** LOKPA roadmap items (lines 69, 73, 162, 175, 204) | GD-001 is resolved |
| `COMPLETION_REPORT.md` | **Remove** LOKPA dependency references (lines 120, 132, 145, 172) | Outdated dependency status |
| `STATUS.md` | **Remove** LOKPA from governance decisions and dependencies (lines 154, 158, 166, 180) | Already resolved |
| `RESEARCH_DATA_MIGRATION_REPORT.md` | **Remove** LOKPA mentions (lines 24, 67, 69–70) | Stale migration notes |

### Risk Assessment

| Factor | Rating | Notes |
|--------|--------|-------|
| Data loss | **None** | LOKPA source file was never in the repo; only documentation |
| License violation | **None** | No attribution required for rejected dataset |
| Historical record | **Low** | GD-001 resolution is already documented; removing stale doc refs is cleanup |
| Downstream impact | **None** | No code depends on LOKPA references |

---

## 2. AstroDatabank

### Status
- **Source data:** `AstroDatabank.xlsx` (57,466 records, 15 columns) — NOT in repo; referenced at `C:\Users\rkmau\Downloads\AstroDatabank.xlsx`
- **Import status:** ✅ COMPLETE — 49,964 records imported and validated as `ASTRO-RS-COHORT` dataset
- **License:** CC-BY-4.0 — however, the "AstroDatabank" name was a mislabel applied to what is actually the user's own curated data collection. No attribution to a third party is required.
- **Adapter code:** `apps/api/services/dataset_import/adapters/astrodatabank_adapter.py` — exists but source file not in repo
- **Runner:** `run_import.py` — exists but requires source file outside repo

### All Occurrences (~66 matches across 13 files)

#### A. Python Source Code (3 files, ~17 lines)

| # | File | Lines | Usage | Classification | Risk |
|---|------|-------|-------|----------------|------|
| 1 | `apps/api/services/dataset_import/__init__.py` | 10 | Comment: "AstroDatabank.xlsx is the first supported adapter" | **F. Comments** | Low |
| 2 | `apps/api/services/dataset_import/adapters/__init__.py` | 4, 6 | Import + export of `AstroDatabankAdapter` class | **C. Import pipeline** | Medium — active import code |
| 3 | `apps/api/services/dataset_import/adapters/astrodatabank_adapter.py` | 2, 4–5, 8, 26–27, 30, 37, 40, 122–123, 130, 152 | Full adapter class with column mappings, metadata, normalization | **C. Import pipeline** | Medium — code references external file not in repo |

#### B. Test Code (1 file, ~23 lines)

| # | File | Lines | Usage | Classification | Risk |
|---|------|-------|-------|----------------|------|
| 4 | `tests/unit/dataset_import/test_astrodatabank_pipeline.py` | 1, 7, 16–20, 33, 37, 40, 52, 56–63, 70–71, 77–78, 87, 96, 104, 110, 116 | Full pipeline integration test requiring `AstroDatabank.xlsx` at local path | **D. Test data** | High — tests skip if source file not present; source file is outside repo |

#### C. Runner Script (1 file, ~14 lines)

| # | File | Lines | Usage | Classification | Risk |
|---|------|-------|-------|----------------|------|
| 5 | `run_import.py` | 2, 14, 22–23 | Script to run import pipeline; references `C:\Users\rkmau\Downloads\AstroDatabank.xlsx` | **C. Import pipeline** | High — hardcoded external path; will fail on any other machine |

#### D. JSON Metadata (2 files, ~6 lines)

| # | File | Lines | Usage | Classification | Risk |
|---|------|-------|-------|----------------|------|
| 6 | `datasets/rs/cohort/ASTRO-RS-COHORT-v0.1.0/ASTRO-RS-COHORT-v0.1.0_CSV_metadata.json` | 3–4, 12 | Dataset name + source description | **E. Metadata** | Low — rename to remove mislabel; no third-party attribution needed |
| 7 | `research-data/research/cohort/ASTRO-RS-COHORT-v1.0.0/ASTRO-RS-COHORT-v1.0.0_CSV_metadata.json` | 3–4, 12 | Dataset name + source description | **E. Metadata** | Low — rename to remove mislabel; no third-party attribution needed |

#### E. Markdown Documentation (7 files, ~20 lines)

| # | File | Lines | Usage | Classification | Risk |
|---|------|-------|-------|----------------|------|
| 8 | `ENGINEERING_STATUS.md` | 24 | "AstroDatabank Adapter — ✅ Complete" | **A. Documentation** | Low |
| 9 | `ENGINEERING_INDEX.md` | 67, 76 | Index entry: "AstroDatabank Adapter" with file ref + 57,466 records | **A. Documentation** | Low |
| 10 | `FOUNDATION_RELEASE_REVIEW.md` | 65, 87, 100, 109 | Release review findings about AstroDatabank/RS-EVENT license gap | **A. Documentation** | Medium — references conditional compliance issue |
| 11 | `docs/dataset_import/ARCHITECTURE.md` | 41, 107, 110 | Architecture doc: adapter listing, integration tests, "First Dataset: AstroDatabank" | **A. Documentation** | Low |
| 12 | `research-data/governance/astrosos-dataset-taxonomy.md` | 1071 | Candidate source pre-assessment: "Public research data; verify license" | **A. Documentation** | Low |
| 13 | `research-data/STATUS.md` | 60, 179 | Status: "49,964 records imported from AstroDatabank"; ER-001 complete | **E. Metadata** | Low |
| 14 | `research-data/pipelines/import-framework/Standards_Compliance_Review.md` | 1, 3, 13, 79, 197 | Full compliance review document for AstroDatabank schema mapping | **A. Documentation** | Low |
| 15 | `research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md` | 1, 10, 14, 39, 57, 79, 382, 384, 393, 416 | Full mapping specification from AstroDatabank to AstroOS schema | **A. Documentation** | Low |

### Recommended Action

**FULL CLEANUP** — no attribution to AstroDatabank is needed. The "AstroDatabank" name was a mislabel applied to what is actually the user's own data collection. All references can be renamed or removed entirely.

| File | Recommended Action | Detail |
|------|-------------------|--------|
| `astrodatabank_adapter.py` | **Rename to generic adapter** or keep with updated docs | The adapter code is the first example of the import framework; could be renamed to `example_excel_adapter.py` with generic naming |
| `apps/api/services/dataset_import/adapters/__init__.py` | **Update exports** if adapter is renamed | Re-export new name |
| `apps/api/services/dataset_import/__init__.py` | **Update comment** to remove branded name | Use generic "Excel adapter" language |
| `test_astrodatabank_pipeline.py` | **Rewrite to use synthetic test data** | Tests currently require external file at hardcoded path; make self-contained with fixtures |
| `run_import.py` | **Update to use generic path or remove** | Hardcoded user-specific path will never work for others |
| Metadata JSON files | **Rename to "RS-COHORT Birth Chart Cohort"** and update `source_description` | No third-party attribution required; data is AstroOS's own curated collection |
| `FOUNDATION_RELEASE_REVIEW.md` | **Clarify or resolve** the RS-EVENT license gap reference | Conditional compliance note needs resolution before tagging |
| `ENGINEERING_STATUS.md` | **Rename** "AstroDatabank Adapter" to "Dataset Import Framework" | Internalize the reference |
| `ENGINEERING_INDEX.md` | **Update** adapter name ref + record count note | Internalize |
| `docs/dataset_import/ARCHITECTURE.md` | **Update** "First Dataset" language to generic | Internalize |
| `Standards_Compliance_Review.md` | **Rename** to `RS-COHORT_Standards_Compliance_Review.md` or keep as-is | Document is about the schema mapping, not the branded dataset |
| `AstroDatabank_Canonical_Mapping.md` | **Rename** to `RS-COHORT_Canonical_Mapping.md` with internal branding | Internalize |

### Risk Assessment

| Factor | Rating | Notes |
|--------|--------|-------|
| Data loss | **Low** | RS-COHORT data already imported and stable; source file not in repo |
| License violation | **None** | "AstroDatabank" was a mislabel — data is AstroOS's own curated collection; no third-party attribution required |
| Broken tests | **High** | `test_astrodatabank_pipeline.py` requires external source file at hardcoded path — already broken for anyone other than the original user |
| Broken runner | **High** | `run_import.py` references `C:\Users\rkmau\Downloads\AstroDatabank.xlsx` — broken on any other machine |
| Downstream impact | **Medium** | Renaming adapter class could break imports in other files; updating metadata could change reported source identity |

---

## 3. Astro-Databank (Astrodienst) — Commercial Variant

### Status
- **Not integrated.** Mentioned once in the dataset taxonomy pre-assessment as a potential commercial source.
- **File:** `research-data/governance/astrosos-dataset-taxonomy.md` line 1072
- **Entry:** `| Astro-Databank (Astrodienst) | Birth charts | LC-CHART | Commercial; verify license terms |`

### Recommended Action
**SAFE TO REMOVE** — this is a speculative source that was never pursued. Remove the entry from the candidate sources table.

---

## 4. Other Branded/External Names — Actively In Use (Excluded)

The following branded external names were found but are **actively used** components of AstroOS, not datasets "no longer part of" the system. They are listed here for completeness.

| Name | Type | Usage | Status |
|------|------|-------|--------|
| **Swiss Ephemeris** (Astrodienst) | Licensed ephemeris engine | Core calculation engine via `pyswisseph` | ✅ ACTIVE — production dependency |
| **JPL Horizons / DE440 / DE441** (NASA) | Reference ephemeris data | BM-CALC independent validation; RF-EPHEM source | ✅ ACTIVE — reference/validation |
| **Lahiri / Chitrapaksha** | Ayanamsa system | Default ayanamsa system across all engines | ✅ ACTIVE — core feature |
| **KP / Krishnamurti Paddhati** | Ayanamsa system + tradition | Supported ayanamsa system; knowledge catalogues | ✅ ACTIVE — core feature |
| **Raman / B.V. Raman** | Ayanamsa system + text sources | Supported ayanamsa system; 6 text source entries | ✅ ACTIVE — core feature |
| **Yukteshwar** | Ayanamsa system | Supported ayanamsa system | ✅ ACTIVE — core feature |
| **Fagan-Bradley** | Ayanamsa system | Supported ayanamsa system | ✅ ACTIVE — core feature |
| **True Chitra** | Ayanamsa system | Supported ayanamsa system | ✅ ACTIVE — core feature |
| **Jagannatha Hora / PyJHora** | Cross-validation software | VL-XPLATFORM benchmark reference | ✅ PLANNED — pending integration |
| **Parashara's Light / Kala** | Cross-validation software | VL-XPLATFORM candidate sources | ✅ REFERENCED — not integrated |
| **IANA tzdata** | Timezone database | RF-TZ data source; quarterly sync | ✅ ACTIVE — external dependency |
| **Wikipedia / Wikidata** (Wikimedia) | Public data sources | PB-WIKI, PB-WIKIDATA planned datasets | ✅ PLANNED — sources for public datasets |
| **IAE** (Indian Astronomical Ephemeris) | Reference values | Ayanamsa validation reference | ✅ ACTIVE — reference standard |
| **VSOP87** | Planetary theory | Underlying theory for Swiss Ephemeris | ✅ ACTIVE — upstream dependency |

---

## 5. Consolidated Cleanup Plan

### Phase 1: LOKPA References (Safe, No License Constraints)

| Priority | File | Action | Complexity |
|----------|------|--------|------------|
| P0 | `research-data/pipelines/candidate-datasets/LOKPA_Candidate_Evaluation_Report.md` | Delete entire file | Low |
| P0 | `research-data/STATUS.md` — LOKPA lines (154, 158, 166, 180) | Remove stale LOKPA entries | Low |
| P1 | `research-data/governance/astrosos-dataset-taxonomy.md` — LOKPA entry (1067) | Remove from candidate sources table | Low |
| P1 | `research-data/ROADMAP.md` — LOKPA milestones/lines (69, 73, 162, 175, 204) | Rewrite or remove | Low |
| P1 | `research-data/COMPLETION_REPORT.md` — LOKPA refs (120, 132, 145, 172) | Remove stale references | Low |
| P2 | `research-data/RESEARCH_DATA_MIGRATION_REPORT.md` — LOKPA refs (24, 67, 69-70) | Clean up migration notes | Low |
| P2 | `research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md` — LOKPA section (~380-416) | Remove LOKPA comparison section | Low |

### Phase 2: AstroDatabank References (Requires Careful Attribution)

| Priority | File | Action | Complexity | Notes |
|----------|------|--------|------------|-------|
| P0 | `tests/unit/dataset_import/test_astrodatabank_pipeline.py` | Rewrite tests with synthetic data | Medium | Tests broken without external file |
| P0 | `run_import.py` | Remove or refactor to use configurable path | Medium | Hardcoded user path; broken for others |
| P1 | Metadata JSON files (both v0.1.0 and v1.0.0) | Rename dataset, update `source_description` | Low | No third-party attribution needed — data is AstroOS's own collection |
| P1 | `astrodatabank_adapter.py` | Rename class and file to generic/synthetic name | Medium | Update all imports |
| P1 | `apps/api/services/dataset_import/adapters/__init__.py` | Update exports to match rename | Low | |
| P1 | `FOUNDATION_RELEASE_REVIEW.md` | Resolve or clarify the RS-EVENT license gap finding | High | Depends on governance decision |
| P2 | `ENGINEERING_STATUS.md` / `ENGINEERING_INDEX.md` | Update adapter name references | Low | |
| P2 | `docs/dataset_import/ARCHITECTURE.md` | Update "First Dataset" language | Low | |
| P2 | `AstroDatabank_Canonical_Mapping.md` | Rename file and internalize references | Medium | |
| P2 | `Standards_Compliance_Review.md` | Rename to reference RS-COHORT | Low | |

### Phase 3: Astro-Databank (Astrodienst) Entry

| Priority | File | Action | Complexity |
|----------|------|--------|------------|
| P2 | `research-data/governance/astrosos-dataset-taxonomy.md` line 1072 | Remove "Astro-Databank (Astrodienst)" speculation entry | Low |

---

## 6. Detailed Occurrence Registry

### 6.1 LOKPA — Full Inventory

```csv
File,Line,Form,Context,Classification
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,380,LOKPA,"## 9. Expected Import Statistics (Based on LOKPA Analysis)",A. Documentation
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,382,LOKPA,"| Metric | LOKPA Observed | AstroDatabank Expected | Notes |",A. Documentation
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,384,LOKPA,"| Total records | 28,246 | ~30,000-40,000 | AstroDatabank is larger |",A. Documentation
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,393,LOKPA,"| Records with coordinates | 100% | 100% | Standard in AstroDatabank |",A. Documentation
research-data/pipelines/candidate-datasets/LOKPA_Candidate_Evaluation_Report.md,3,LOKPA,"## LOKPA_Persons_WithEvents.csv",A. Documentation
research-data/pipelines/candidate-datasets/LOKPA_Candidate_Evaluation_Report.md,16,LOKPA,"| **Filename** | `LOKPA_Persons_WithEvents.csv` |",A. Documentation
research-data/pipelines/candidate-datasets/LOKPA_Candidate_Evaluation_Report.md,17,LOKPA,"| **Location** | `C:\Users\rkmau\Downloads\LOKPA_Persons_WithEvents.csv` |",A. Documentation
research-data/pipelines/candidate-datasets/LOKPA_Candidate_Evaluation_Report.md,307,LOKPA,"| **Candidate** | LOKPA_Persons_WithEvents.csv |",A. Documentation
research-data/RESEARCH_DATA_MIGRATION_REPORT.md,24,LOKPA,"`pipelines/` ... LOKPA candidate evaluation",A. Documentation
research-data/RESEARCH_DATA_MIGRATION_REPORT.md,67,LOKPA,"LOKPA licensing, public-figure privacy threshold...",A. Documentation
research-data/RESEARCH_DATA_MIGRATION_REPORT.md,69,LOKPA,"- **1 external dependency pending**: `LOKPA_Persons_WithEvents.csv`...",A. Documentation
research-data/RESEARCH_DATA_MIGRATION_REPORT.md,70,LOKPA,"evaluation (see `...LOKPA_Candidate_Evaluation_Report.md`).",A. Documentation
research-data/governance/astrosos-dataset-taxonomy.md,1067,LOKPA,"| LOKPA_Persons_WithEvents.csv...| 28,247 records; needs license evaluation |",A. Documentation
research-data/ROADMAP.md,69,LOKPA,"| **LOKPA candidate assessment** | P0 | License review |...|",A. Documentation
research-data/ROADMAP.md,73,LOKPA,"**External dependency:** License evaluation of LOKPA_Persons_WithEvents.csv...",A. Documentation
research-data/ROADMAP.md,162,LOKPA,"| **LOKPA file license assessment** | PB incorporation | PENDING |...|",A. Documentation
research-data/ROADMAP.md,175,LOKPA,"| **LOKPA data usage terms** | 28K-record CSV needs license evaluation...|",A. Documentation
research-data/ROADMAP.md,204,LOKPA,"| M3: ...LOKPA decision | 🔄 IN PROGRESS |",A. Documentation
research-data/COMPLETION_REPORT.md,120,LOKPA,"| **M3** — First Real Charts |...LOKPA decision |",A. Documentation
research-data/COMPLETION_REPORT.md,132,LOKPA,"| GD-001 | LOKPA data usage | License assessment for 28K-record CSV...|",A. Documentation
research-data/COMPLETION_REPORT.md,145,LOKPA,"| LOKPA_Persons_WithEvents.csv | License evaluation | PB incorporation | ⏳ PENDING |",A. Documentation
research-data/COMPLETION_REPORT.md,172,LOKPA,"4. **Evaluate LOKPA file** — Legal license assessment...|",A. Documentation
research-data/STATUS.md,154,LOKPA,"| Candidate datasets evaluated | 1 (LOKPA — recommendation: REJECT) |",A. Documentation
research-data/STATUS.md,158,LOKPA,"| Governance decisions resolved | 1 (GD-001: LOKPA rejected) |",A. Documentation
research-data/STATUS.md,166,LOKPA,"| GD-001 | LOKPA_Persons_WithEvents.csv usage terms |...✅ RESOLVED — Reject |",A. Documentation
research-data/STATUS.md,180,LOKPA,"| LOKPA file license | ✅ RESOLVED | Legal | Rejected — do not use |",A. Documentation
```

### 6.2 AstroDatabank — Full Inventory

```csv
File,Line(s),Form,Context,Classification
apps/api/services/dataset_import/__init__.py,10,AstroDatabank.xlsx,Comment: first supported adapter,F. Comments
apps/api/services/dataset_import/adapters/__init__.py,4,astrodatabank_adapter,Import statement,C. Import pipeline
apps/api/services/dataset_import/adapters/__init__.py,6,AstroDatabankAdapter,Export in __all__,C. Import pipeline
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,2,AstroDatabank,Docstring: module description,C. Import pipeline
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,4,AstroDatabank.xlsx,Docstring: adapter description,C. Import pipeline
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,5,AstroDatabank-specific,Docstring: column mappings,C. Import pipeline
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,8,AstroDatabank.xlsx,Docstring: source reference,C. Import pipeline
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,26,AstroDatabankAdapter,Class definition,C. Import pipeline
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,27,AstroDatabank,Class docstring,C. Import pipeline
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,30,AstroDatabank Birth Chart Cohort,DATASET_NAME constant,C. Import pipeline
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,37,AstroDatabank,get_adapter_name() return value,C. Import pipeline
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,40,AstroDatabank,"get_column_mappings() docstring",C. Import pipeline
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,122,AstroDatabank Birth Chart Cohort,Metadata: dataset name,E. Metadata
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,123,AstroDatabank database,Metadata: description,E. Metadata
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,130,AstroDatabank birth chart database,Metadata: source_description,E. Metadata
apps/api/services/dataset_import/adapters/astrodatabank_adapter.py,152,AstroDatabank,get_normalization_rules() docstring,C. Import pipeline
tests/unit/dataset_import/test_astrodatabank_pipeline.py,1,AstroDatabank,Module docstring,D. Test data
tests/unit/dataset_import/test_astrodatabank_pipeline.py,7,AstroDatabankAdapter,Import statement,D. Test data
tests/unit/dataset_import/test_astrodatabank_pipeline.py,16-20,AstroDatabank.xlsx,Fixture path; skips if not found,D. Test data
tests/unit/dataset_import/test_astrodatabank_pipeline.py,33,AstroDatabankAdapter,Fixture: adapter instance,D. Test data
tests/unit/dataset_import/test_astrodatabank_pipeline.py,37,40,astrodatabank_file,Config references fixture,D. Test data
tests/unit/dataset_import/test_astrodatabank_pipeline.py,52,AstroDatabankAdapter,Config: source_metadata,D. Test data
tests/unit/dataset_import/test_astrodatabank_pipeline.py,56-78,AstroDatabankAdapter,Test class + 4 test methods,D. Test data
tests/unit/dataset_import/test_astrodatabank_pipeline.py,87-116,AstroDatabankAdapter,5 integration pipeline tests,D. Test data
run_import.py,2,AstroDatabank,Module docstring,C. Import pipeline
run_import.py,14,AstroDatabankAdapter,Import statement,C. Import pipeline
run_import.py,22-23,AstroDatabankAdapter + AstroDatabank.xlsx,Main function references,C. Import pipeline
ENGINEERING_STATUS.md,24,AstroDatabank Adapter,Status entry: ✅ Complete,A. Documentation
ENGINEERING_INDEX.md,67,AstroDatabank Adapter,Index entry with file reference,A. Documentation
ENGINEERING_INDEX.md,76,AstroDatabank.xlsx,Source record count reference,A. Documentation
FOUNDATION_RELEASE_REVIEW.md,65,AstroDatabank/RS-EVENT,Release review finding (long line),A. Documentation
FOUNDATION_RELEASE_REVIEW.md,87,AstroDatabank/RS-EVENT license gap,Medium-High severity finding,A. Documentation
FOUNDATION_RELEASE_REVIEW.md,100,AstroDatabank RS-EVENT,Self-rated conditional compliance,A. Documentation
FOUNDATION_RELEASE_REVIEW.md,109,AstroDatabank license gap,Recommended resolution step,A. Documentation
docs/dataset_import/ARCHITECTURE.md,41,astrodatabank_adapter.py,Architecture diagram listing,A. Documentation
docs/dataset_import/ARCHITECTURE.md,107,AstroDatabank.xlsx,Integration test references,A. Documentation
docs/dataset_import/ARCHITECTURE.md,110,AstroDatabank,"## First Dataset: AstroDatabank",A. Documentation
research-data/governance/astrosos-dataset-taxonomy.md,1071,AstroDatabank,Candidate source pre-assessment table,A. Documentation
research-data/STATUS.md,60,AstroDatabank,"RS-COHORT: 49,964 records imported from AstroDatabank",E. Metadata
research-data/STATUS.md,179,AstroDatabank.xlsx,ER-001 completion reference,A. Documentation
research-data/pipelines/import-framework/Standards_Compliance_Review.md,1,AstroDatabank Import,"# Standards Compliance Review — AstroDatabank Import",A. Documentation
research-data/pipelines/import-framework/Standards_Compliance_Review.md,3,AstroDatabank data schema,Purpose paragraph,A. Documentation
research-data/pipelines/import-framework/Standards_Compliance_Review.md,13,AstroDatabank Source,Envelope field mapping table,A. Documentation
research-data/pipelines/import-framework/Standards_Compliance_Review.md,79,astro_databank,Static type string in primary_source.type mapping,A. Documentation
research-data/pipelines/import-framework/Standards_Compliance_Review.md,197,AstroDatabank data,Conclusion paragraph,A. Documentation
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,1,AstroDatabank,File title,A. Documentation
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,10,AstroDatabank.xlsx,Source schema section,A. Documentation
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,14,AstroDatabank record,DocID field description,A. Documentation
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,39,AstroDatabank source code,DocID→_record_id mapping prefix,A. Documentation
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,57,astro_databank,source type assignment,A. Documentation
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,79,astro_databank,source_type field,A. Documentation
research-data/pipelines/import-framework/AstroDatabank_Canonical_Mapping.md,416,AstroDatabank.xlsx via ER-001,Variant specification reference,A. Documentation
datasets/rs/cohort/ASTRO-RS-COHORT-v0.1.0/*_metadata.json,3-4,12,AstroDatabank Birth Chart Cohort; AstroDatabank database,Dataset name + source description,E. Metadata
research-data/research/cohort/ASTRO-RS-COHORT-v1.0.0/*_metadata.json,3-4,12,AstroDatabank Birth Chart Cohort; AstroDatabank database,Dataset name + source description,E. Metadata
```

---

## 7. Methodology

### 7.1 Search Parameters
- **Tools:** `Grep` (ripgrep), `Glob`, `Read`
- **Case sensitivity:** Case-insensitive search for all patterns
- **Scope:** Entire repository (all file types)
- **Patterns searched:**
  - `AstroDatabank`, `astrodatabank`, `astro_databank`
  - `LOKPA`, `Lokpa`, `lokpa`, `LoKPā` (with macron)
  - `swiss ephemeris`, `swisseph`, `swe_`
  - `JPL Horizons`, `JPL DE`, `DE440`, `DE441`
  - `Jagannatha Hora`, `JHora`, `PyJHora`
  - `Parashara.?s Light`, `Kala software`
  - `NASA`, `IAE`, `VSOP87`
  - File names containing `dataset`

### 7.2 Classification Categories
| Code | Category | Definition |
|------|----------|------------|
| A | Documentation | Markdown docs, architecture descriptions, status reports |
| B | Dataset | Actual data files (CSV, JSON, Parquet) |
| C | Import pipeline | Adapter code, runner scripts, mappings |
| D | Test data | Test files that depend on external data |
| E | Metadata | JSON metadata files describing datasets |
| F | Comments | Inline code comments referencing branded names |

### 7.3 Risk Ratings
| Rating | Definition |
|--------|------------|
| **None** | No impact from removal |
| **Low** | Cosmetic — changes documentation only |
| **Medium** | Functional impact — requires coordinated changes across files |
| **High** | Structural — changes may break tests, imports, or violate license terms |

---

## 8. Recommendations

### Immediate Actions (Wait for Approval)
1. **Delete** `research-data/pipelines/candidate-datasets/LOKPA_Candidate_Evaluation_Report.md` — entire file is about a rejected dataset
2. **Remove LOKPA references** from STATUS.md, ROADMAP.md, COMPLETION_REPORT.md, RESEARCH_DATA_MIGRATION_REPORT.md, astrosos-dataset-taxonomy.md, and AstroDatabank_Canonical_Mapping.md
3. **Fix broken test** `test_astrodatabank_pipeline.py` — rewrite with synthetic data fixtures
4. **Fix broken runner** `run_import.py` — remove hardcoded user path or make configurable
5. **Rename adapter files** to remove "AstroDatabank" branding — keep as generic examples of the import framework
6. **Update dataset metadata** — rename "AstroDatabank Birth Chart Cohort" → "RS-COHORT Birth Chart Cohort"; the name was a mislabel, data is AstroOS's own collection
7. **Remove** "Astro-Databank (Astrodienst)" entry from taxonomy candidate sources

### Items Requiring Governance Decision
8. **RS-EVENT license gap** in `FOUNDATION_RELEASE_REVIEW.md` — tagged as "conditionally compliant" but not yet resolved

### Items to Leave Unchanged
- All other branded external names (Swiss Ephemeris, JPL Horizons, ayanamsa systems, etc.) — these are active dependencies

---

*End of audit. No files have been modified. Awaiting approval before proceeding with any changes.*
