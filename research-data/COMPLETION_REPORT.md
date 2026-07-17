# AstroOS Research Data Office — Overview

> **Status:** ACTIVE
> **Owner:** Chief Dataset & Research Curator
> **Version:** 1.0
> **Date:** 2026-07-15

---

## 1. Mission

The AstroOS Research Data Office (RDO) builds the world's highest-quality structured astrology research datasets. Every dataset is reproducible, well-documented, legally usable, versioned, privacy-aware, and research-grade.

The RDO does **not** modify AstroOS code, write software, redesign architecture, or change the Jyotish knowledge base. Its sole responsibility is datasets.

---

## 2. Architecture

### 2.1 Dataset Ecosystem

The RDO defines **51 dataset types** across **10 categories**:

```
                    ┌─────────────────────────────────────────────┐
                    │           ASTROOS DATASETS (51)             │
                    └─────────────────────────────────────────────┘

  REFERENCE (10)       RESEARCH (8)         BENCHMARK (8)        VALIDATION (3)
  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     ┌──────────────┐
  │ Signs        │    │ Cohorts      │    │ Calc Accuracy│     │ Cross-Platform│
  │ Nakshatras   │    │ Events       │    │ Aspect       │     │ End-to-End   │
  │ Padas        │    │ Marriage     │    │ Dasha        │     │ Consistency  │
  │ Planets      │    │ Career       │    │ Transit      │     └──────────────┘
  │ Houses       │    │ Health       │    │ Shadbala     │
  │ Karakas      │    │ Wealth       │    │ Ashtakavarga │     QA/TEST (4)
  │ Ayanamsa     │    │ Spiritual    │    │ Divisional   │     ┌──────────────┐
  │ Dashas       │    │ Flattened    │    │ Performance  │     │ Regression   │
  │ Timezones    │    └──────────────┘    └──────────────┘     │ Edge Cases   │
  │ Ephemeris    │                                              │ Stress       │
  └──────────────┘     AI EVAL (5)          SYNTHETIC (4)       │ Integration  │
                       ┌──────────────┐    ┌──────────────┐     └──────────────┘
                       │ Interpretation│   │ Random       │
                       │ Hallucination │   │ Controlled   │     PUBLIC (4)
                       │ Fact Accuracy │   │ Monte Carlo  │     ┌──────────────┐
                       │ Report Gen   │   │ Null Baseline│     │ Wikipedia    │
                       │ Rule Eval    │    └──────────────┘     │ Wikidata     │
                       └──────────────┘                         │ Events       │
                                                                │ Twins        │
  LICENSED (3)         USER-CONTRIBUTED (3)                     └──────────────┘
  ┌──────────────┐    ┌──────────────┐
  │ Swiss Eph.   │    │ User Charts  │
  │ Chart Vendor │    │ User Events  │
  │ Partner Data │    │ Community    │
  └──────────────┘    └──────────────┘
```

### 2.2 Engine Alignment

Every dataset is designed for specific consumers:

| Engine | Primary Datasets | Purpose |
|--------|-----------------|---------|
| **Verification Engine** | RS-EVENT, RS-MARRIAGE, RS-CAREER, RS-HEALTH | Rule↔event alignment |
| **Statistics Engine** | SY-RANDOM, SY-NULL, RS-COHORT, RS-FLAT | Distributions, significance |
| **Research Engine** | RS-COHORT, RS-FLAT, RF-* | Snapshot capture, comparison |
| **AI Engine** | AI-INTERP, AI-HALLUC, AI-FACT, AI-REPORT | LLM evaluation, training |
| **Benchmark Suite** | BM-*, QT-*, VL-* | Engine correctness, performance |
| **All Engines** | RF-* (reference data) | Foundational constants |

### 2.3 Quality Framework

| Tier | Score | Label | Use |
|------|-------|-------|-----|
| A | ≥0.90 | Research Grade | Published research, benchmarks, AI evaluation |
| B | 0.75–0.89 | Production Grade | Internal research, statistical analysis |
| C | 0.50–0.74 | Exploratory Grade | Exploratory analysis |
| D | 0.25–0.49 | Draft Grade | Internal review |
| F | <0.25 | Rejected | Do not use |

Quality scored across 6 dimensions: Completeness (0.25), Accuracy (0.25), Consistency (0.15), Coverage (0.15), Timeliness (0.10), Provenance (0.10).

---

## 3. Approved Artifacts

| Artifact | File | Status | Content |
|----------|------|--------|---------|
| **Phase 1** — Dataset Audit | *(inline)* | ✅ FROZEN | Survey of all existing AstroOS data assets |
| **Phase 2** — Dataset Taxonomy | `astrosos-dataset-taxonomy.md` | ✅ FROZEN | 10 categories, 51 types, cross-cutting framework |
| **Phase 3** — Dataset Standards | `astrosos-dataset-standards.md` | ✅ FROZEN | 7 standards: identity, metadata, quality, validation, docs, file structure, lifecycle |
| **Phase 4** — Record Standards | `astrosos-record-standards.md` | ✅ FROZEN | 13-component record envelope: identity, birth, person, source, confidence, privacy, research, computation, relationships |
| **Phase 5** — Dataset Quality | `astrosos-dataset-quality.md` | ✅ FROZEN | 6 systems: completeness, missing data, duplicates, consistency, bias, ethics |
| **Phase 6** — Standard Formats | `astrosos-standard-formats.md` | ✅ FROZEN | 6 formats: CSV, JSON, JSONL, Parquet, SQL, Research Export — unified schema |
| **Phase 7** — Research Support | `astrosos-research-support.md` | ✅ FROZEN | Engine↔dataset mapping, 15 cohorts, 10-study roadmap, ML specs |
| **Roadmap** | `astrosos-dataset-roadmap.md` | ✅ ACTIVE | 8 build phases (A–H), 7 milestones (M1–M7), governance decisions |
| **Status** | `astrosos-dataset-status.md` | ✅ ACTIVE | Current state of all artifacts and datasets |
| **Index** | `astrosos-dataset-index.md` | ✅ ACTIVE | Complete cross-reference of all artifacts |

---

## 4. Implementation Roadmap (Summary)

### 8 Build Phases, 7 Milestones

```
Q3 2026          Q4 2026          Q1 2027          Q2 2027
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│  A   │  B   │  C   │  D   │  E   │  F   │  G   │  H   │
│Found.│Stats │Public│Events│Bench │AI    │Spec. │ML    │
│Refs  │Base  │Charts│      │Suite │Eval  │Study │Data  │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘
   M1     M2     M3     M4     M5     M6     M7
```

| Milestone | Date | Key Deliverables |
|-----------|------|------------------|
| **M1** — Reference Baseline | 2026-08-15 | RF-* (8 datasets), BM-CALC/ASPECT/DASHA |
| **M2** — Stats Foundation | 2026-09-01 | SY-RANDOM 100K, SY-NULL, BM-TRANSIT |
| **M3** — First Real Charts | 2026-10-15 | PB-WIKI (≥10K), RS-FLAT v0.1, LOKPA decision |
| **M4** — Events Online | 2026-11-15 | RS-EVENT (≥1K), RS-MARRIAGE, RS-CAREER |
| **M5** — Full Benchmarks | 2027-01-15 | All BM-* & QT-* Stable, CI-integrated |
| **M6** — AI Evaluation | 2027-03-15 | AI-FACT, AI-INTERP, AI-HALLUC v1.0 |
| **M7** — Research Ready | 2027-06-15 | All core datasets Stable; 3+ studies published |

---

## 5. Governance Decisions Required

| ID | Decision | Description | Needed By | Recommended |
|----|----------|-------------|-----------|-------------|
| GD-001 | LOKPA data usage | License assessment for 28K-record CSV | Phase C (2026-10) | Evaluate as Public or Licensed |
| GD-002 | Public figure threshold | When is a person "public figure" for privacy | Phase C (2026-10) | Wikipedia notability as proxy |
| GD-003 | Ethics board formation | Who reviews dataset ethics | Phase C (2026-10) | Curator + Privacy + Legal |
| GD-004 | Cohort sharing policy | Can users share cohorts publicly | Phase D (2026-12) | Opt-in with privacy audit |
| GD-005 | AI training data policy | Can public datasets train AI models | Phase F (2027-03) | Yes with attribution |
| GD-006 | Commercial data budget | Budget for licensed chart data | Phase G (2027-03) | TBD — evaluate free first |

---

## 6. External Dependencies

| Dependency | Type | For | Status |
|------------|------|-----|--------|
| LOKPA_Persons_WithEvents.csv | License evaluation | PB incorporation | ⏳ PENDING |
| IANA tzdata | Data source | RF-TZ updates | ✅ ON TRACK |
| Swiss Ephemeris | Data source + License | RF-EPHEM | ✅ ON TRACK |
| JPL Horizons API | Reference data | BM-CALC | ✅ AVAILABLE |
| Wikipedia API | Data source | PB-WIKI | ✅ AVAILABLE |
| Wikidata SPARQL | Data source | PB-WIKIDATA | ✅ AVAILABLE |

---

## 7. Current State (as of 2026-07-15)

| Metric | Value |
|--------|-------|
| Phases completed | 7 of 7 (all FROZEN) |
| Dataset types defined | 51 |
| Dataset types SEEDED (data exists) | 3 (SIGNS, NAK, PADA) |
| Dataset types ready to build | 48 |
| Governance decisions open | 6 |
| External dependencies | 6 (5 ready, 1 pending) |

---

## 8. Next Immediate Actions

1. **Build RF-* seed datasets** — Package migration 0005 data (SIGNS, NAK, PADA) into canonical formats per Phase 6. Immediate priority.
2. **Build SY-RANDOM generator** — Create first synthetic dataset (100K records). Required for all statistical work.
3. **Build PB-WIKI extractor** — Wikipedia infobox extraction for first real chart collection. Foundation for all research datasets.
4. **Evaluate LOKPA file** — Legal license assessment of existing CSV. Could accelerate Phase C significantly.
5. **Set up repository infrastructure** — Directory layout, Git LFS, JSON schemas, validators.

---

## 9. Key Contacts

| Role | Responsibility |
|------|---------------|
| **Chief Dataset & Research Curator** | Overall RDO ownership, dataset design, quality standards |
| **Engineering Agent** | AstroOS code — provides computation pipeline for RS-FLAT |
| **Architecture Agent** | Future design — receives dataset requirements |
| **Knowledge Agent** | Jyotish knowledge base — reference data source |
| **QA Agent** | Benchmark specifications — coordinates with BM/QT datasets |
| **Legal/Privacy** *(not yet assigned)* | License evaluation, privacy review, ethical review |

---

*End of Research Data Office Overview. See ROADMAP.md for the authoritative implementation plan.*
