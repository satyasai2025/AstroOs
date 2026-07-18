---
name: astrosos-dataset-roadmap
description: "Authoritative implementation roadmap for the AstroOS Research Dataset Repository — dataset builds, milestones, dependencies, governance decisions"
metadata: 
  node_type: memory
  type: reference
  domain: datasets
  status: active
  phase: roadmap
  originSessionId: e78a75e5-611c-4c3f-99a8-68817dfe9484
---

# AstroOS Research Dataset Repository — ROADMAP

> **Status:** ACTIVE — authoritative implementation plan
> **Owner:** Chief Dataset & Research Curator
> **Version:** 1.0
> **Date:** 2026-07-15
> **Supersedes:** All prior informal planning

---

## 1. Build Phases

### Phase A — Foundation (Q3 2026) ✅ COMPLETE

**Goal:** Establish reference data, basic chart collection, and calculation benchmarks.
**Completed:** 2026-07-15

| Dataset | Status | Version |
|---------|--------|---------|
| RF-SIGNS | ✅ Stable | v1.0.0 |
| RF-NAK | ✅ Stable | v1.0.0 |
| RF-PADA | ✅ Stable | v1.0.0 |
| RF-PLANET | ✅ Stable | v1.0.0 |
| RF-HOUSE | ✅ Stable | v1.0.0 |
| RF-AYAN | ⏳ Candidacy | v1.0.0 |
| RF-DASHA | ⏳ Candidacy | v1.0.0 |
| RF-KARAKA | ✅ Stable | v1.0.0 |
| RF-TZ | ⏳ Placeholder | v1.0.0 |
| RF-EPHEM | ⏳ Candidacy | v1.0.0 |

---

### Phase B — Statistical Baselines (Q3 2026) ✅ COMPLETE

**Goal:** Generate large-scale synthetic data for base rates and null hypotheses.
**Completed:** 2026-07-15

| Dataset | Status | Version |
|---------|--------|---------|
| SY-RANDOM | ✅ Stable | v1.0.0 — 100K records |
| SY-NULL | ✅ Specification | v1.0.0 |
| SY-MONTE (1M) | ⏳ Next | Scoped from SY-RANDOM |
| BM-TRANSIT | ⏳ Next | Pending |

---

### Phase C — Public Chart Collection (Q3–Q4 2026)

**Goal:** Build the first real chart dataset from public sources.

| Dataset | Priority | Dependencies | Est. Effort |
|---------|----------|-------------|-------------|
| PB-WIKI (v0.1.0) — candidacy | P0 | None | Wikipedia extraction script |
| PB-WIKIDATA (v0.1.0) — candidacy | P1 | None | SPARQL query design |
| PB-EVENTS (v0.1.0) | P1 | PB-WIKI (chart refs) | Event extraction from biographies |
| RS-FLAT (v0.1.0) | P1 | PB-WIKI, SY-RANDOM | Computation pipeline |

**Gate:** PB-WIKI v1.0.0 Stable with ≥10K records.

---

### Phase D — Event Datasets (Q4 2026)

**Goal:** Create the event-chart linkage datasets essential for Verification Engine.

| Dataset | Priority | Dependencies | Est. Effort |
|---------|----------|-------------|-------------|
| RS-EVENT (v0.1.0) | P0 | PB-WIKI | Event extraction + chart linking |
| RS-MARRIAGE (v0.1.0) | P0 | RS-EVENT | Marriage subset curation |
| RS-CAREER (v0.1.0) | P0 | RS-EVENT | Career subset curation |
| RS-HEALTH (v0.1.0) | P1 | RS-EVENT | Health subset curation |
| RS-WEALTH (v0.1.0) | P1 | RS-EVENT | Wealth subset curation |
| RS-SPIRITUAL (v0.1.0) | P1 | RS-EVENT | Spiritual subset curation |

**Gate:** RS-EVENT v1.0.0 with ≥1,000 verified events, Tier A quality.

---

### Phase E — Full Benchmark Suite (Q4 2026–Q1 2027)

**Goal:** Complete all benchmark and test datasets.

| Dataset | Priority | Dependencies | Est. Effort |
|---------|----------|-------------|-------------|
| BM-BALA (v1.0.0) | P0 | RF-PLANET | 20+ Shadbala test cases |
| BM-ASTAK (v1.0.0) | P1 | RF-PLANET | 20+ Ashtakavarga test cases |
| BM-DIV (v1.0.0) | P1 | RF-PADA | 30+ divisional chart test cases |
| BM-PERF (v1.0.0) | P1 | None | Performance baseline script |
| VL-XPLATFORM (v0.1.0) | P1 | RF-* (all) | Cross-software comparison |
| VL-CHART (v0.1.0) | P1 | RF-* (all) | End-to-end chart validation |
| QT-REGRESSION (v0.1.0) | P1 | BM-* | Regression test suite |

**Gate:** All BM-* datasets Stable, integrated with CI pipeline.

---

### Phase F — AI Evaluation (Q1 2027)

**Goal:** Build AI evaluation infrastructure.

| Dataset | Priority | Dependencies | Est. Effort |
|---------|----------|-------------|-------------|
| AI-FACT (v0.1.0) | P0 | RF-* (all) | 200+ factual QA pairs |
| AI-INTERP (v0.1.0) | P0 | PB-WIKI, RS-FLAT | 50+ chart-interpretation pairs |
| AI-HALLUC (v0.1.0) | P1 | AI-FACT | 100+ hallucination test cases |
| AI-REPORT (v0.1.0) | P1 | AI-INTERP | 20+ full report benchmarks |
| AI-RULE (v0.1.0) | P1 | RF-KARAKA | Rule evaluation test cases |

**Gate:** AI-FACT v1.0.0 Stable with ≥85% factual coverage of system.

---

### Phase G — Specialized Research (Q1–Q2 2027)

**Goal:** Build domain-specific research datasets.

| Dataset | Priority | Dependencies | Est. Effort |
|---------|----------|-------------|-------------|
| PB-TWIN (v0.1.0) | P1 | PB-WIKI | Twin pair identification |
| SY-CONTROLLED (v0.1.0) | P1 | RF-* (all) | Controlled experiment design |
| ~~RS-COHORT (v0.1.0)~~ | P1 | PB-WIKI, RS-FLAT | ✅ Already Stable at v1.0.0 as of 2026-07-16 — see STATUS.md/INDEX.md. Left struck through here rather than removed, since this table's original P1 slot is what triggered the build. |
| LC-CHART assessment | P2 | Legal review | Evaluate commercial data options |

**Gate:** At least 3 domain-specific studies initiated.

---

### Phase H — ML Datasets (Q2–Q3 2027)

**Goal:** Prepare ML-ready datasets for future model training.

| Dataset | Priority | Dependencies | Est. Effort |
|---------|----------|-------------|-------------|
| RS-FLAT (v1.0.0) — 50K | P1 | PB-WIKI, SY-RANDOM, computation pipeline | Full feature computation |
| ML event prediction set | P2 | RS-EVENT, RS-FLAT | Feature engineering |
| ML rectification set | P2 | RS-EVENT (verified times) | Label construction |
| ML yoga detection set | P2 | SY-RANDOM, YogaEngine | Multi-label generation |

**Gate:** At least 1 ML pilot study completed.

---

## 2. External Dependencies

| Dependency | Required For | Status | Action Needed |
|------------|-------------|--------|---------------|
| **IANA tzdata release schedule** | RF-TZ updates | ON TRACK | Quarterly sync |
| **Swiss Ephemeris license** | RF-EPHEM distribution | ON TRACK | Annual review |
| **JPL Horizons API access** | BM-CALC reference values | AVAILABLE | Query script |
| **Wikipedia API rate limits** | PB-WIKI extraction | MANAGEABLE | Throttled extraction |
| **Wikidata SPARQL endpoint** | PB-WIKIDATA query | AVAILABLE | Query design |

---

## 3. Governance Decisions Required

| Decision | Context | Needed By | Recommended |
|----------|---------|-----------|-------------|
| **Public figure privacy threshold** | When does a person qualify as "public figure" for privacy tier | Phase C start | Wikipedia notability as proxy |
| **Ethics board formation** | Who reviews datasets for ethical concerns | Phase C start | Cross-functional team (Curator + Privacy + Legal) |
| **Cohort sharing policy** | Can users share cohorts publicly? | Phase D end | Opt-in with privacy audit |
| **AI training data policy** | Can public datasets be used for AI training? | Phase F start | Yes with attribution; user data opt-in only |
| **Commercial data budget** | Budget for licensed datasets | Phase G | TBD — evaluate free sources first |

---

## 4. Repository Infrastructure

| Need | Timeline | Notes |
|------|----------|-------|
| Dataset directory structure | Immediate | Per Phase 3 §9 layout |
| Git LFS setup | Phase A start | For Parquet and ephemeris files |
| Validation script framework | Phase A start | L1+L2 automated validators |
| CI integration (L1 validation) | Phase A end | Run on PR to datasets/ |
| JSON Schema registry | Phase A start | Schema for `_metadata.json` |
| Format conversion tooling | Phase A | CSV ↔ JSON ↔ Parquet scripts |
| DVC (Data Version Control) | Phase C | For large research datasets |

---

## 5. Release Milestones

| Milestone | Date | Deliverables | Status |
|-----------|------|-------------|--------|
| M1: Reference Baseline | 2026-08-15 | RF-* v1.0.0 (8 datasets), BM-CALC/ASPECT/DASHA v1.0.0 | ✅ COMPLETED 2026-07-15 |
| M2: Stats Foundation | 2026-09-01 | SY-RANDOM 100K, SY-NULL, BM-TRANSIT | ✅ COMPLETED 2026-07-15 |
| M3: First Real Charts | 2026-10-15 | PB-WIKI v1.0.0 (≥10K), RS-FLAT v0.1.0 | 🔄 IN PROGRESS |
| M4: Events Online | 2026-11-15 | RS-EVENT v1.0.0 (≥1K), RS-MARRIAGE, RS-CAREER | ⏳ PENDING |
| M5: Full Benchmarks | 2027-01-15 | All BM-* and QT-* Stable, CI-integrated | ⏳ PENDING |
| M6: AI Evaluation | 2027-03-15 | AI-FACT, AI-INTERP, AI-HALLUC v1.0.0 | ⏳ PENDING |
| M7: Research Ready | 2027-06-15 | All core datasets Stable; 3+ studies published | ⏳ PENDING |

---

## 6. Quality Gates

Every milestone requires:

- [ ] L1 schema validation passes on all new datasets
- [ ] L2 quality score ≥ 0.75 (Production Grade) for P0 datasets
- [ ] Quality report generated for each dataset
- [ ] Bias assessment documented
- [ ] Known limitations documented
- [ ] `_metadata.json` complete
- [ ] `changelog.md` initialized
- [ ] All datasets promoted to at least **Candidacy** stage

**Research Grade (≥0.90)** required for:
- Datasets used in published research
- Datasets used for AI Engine evaluation
- Datasets used for Verification Engine studies
- Datasets used for Benchmark Suite gold standards

---

## 7. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief Dataset & Research Curator | Initial authoritative roadmap |

---

*This ROADMAP is authoritative. All dataset build work shall proceed according to the phases and gates defined herein. Deviations require documented justification and approval.*
