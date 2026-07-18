---
name: DATASET_STATUS
description: "Current status of all AstroOS Research Dataset Repository artifacts — phases, datasets, engines, governance"
metadata: 
  node_type: memory
  type: reference
  domain: datasets
  status: active
  phase: status
  originSessionId: e78a75e5-611c-4c3f-99a8-68817dfe9484
---

# AstroOS Research Dataset Repository — STATUS

> **Status:** ACTIVE — reflects current state as of 2026-07-15
> **Owner:** Chief Dataset & Research Curator
> **Version:** 1.0

---

## 1. Phase Completion Status

| Phase | Title | Status | Artifact | Completed |
|-------|-------|--------|----------|-----------|
| Phase 1 | Dataset Audit | ✅ FROZEN | *(inline audit report)* | 2026-07-15 |
| Phase 2 | Dataset Taxonomy | ✅ FROZEN | `astrosos-dataset-taxonomy.md` | 2026-07-15 |
| Phase 3 | Dataset Standards | ✅ FROZEN | `astrosos-dataset-standards.md` | 2026-07-15 |
| Phase 4 | Record Standards | ✅ FROZEN | `astrosos-record-standards.md` | 2026-07-15 |
| Phase 5 | Dataset Quality | ✅ FROZEN | `astrosos-dataset-quality.md` | 2026-07-15 |
| Phase 6 | Standard Formats | ✅ FROZEN | `astrosos-standard-formats.md` | 2026-07-15 |
| Phase 7 | Research Support | ✅ FROZEN | `astrosos-research-support.md` | 2026-07-15 |
| — | Roadmap | ✅ ACTIVE | `DATASET_ROADMAP.md` | 2026-07-15 |
| — | Status | ✅ ACTIVE | `DATASET_STATUS.md` | 2026-07-15 |
| — | Index | ✅ ACTIVE | `DATASET_INDEX.md` | 2026-07-15 |
| — | RDO Overview | ✅ ACTIVE | `research-data-office-overview.md` | 2026-07-15 |

---

## 2. Dataset Build Status

### Reference Datasets (RF) — Phase A Complete

| Dataset | Status | Version | Quality Score | Tier | Notes |
|---------|--------|---------|---------------|------|-------|
| RF-SIGNS | ✅ STABLE | v1.0.0 | 0.97 | A | CSV + JSON + metadata published; direction NULL (RDO-DEP-001) |
| RF-NAK | ✅ STABLE | v1.0.0 | 0.80 | B | CSV published; deity/symbol/gana etc. NULL (RDO-DEP-002) |
| RF-PADA | ✅ STABLE | v1.0.0 | 1.00 | A | CSV published; mathematically verified |
| RF-PLANET | ✅ STABLE | v1.0.0 | 0.98 | A | CSV published; all 9 grahas from approved code constants |
| RF-HOUSE | ✅ STABLE | v1.0.0 | 0.95 | A | CSV published; from ontology registry + verification engine |
| RF-DASHA | ✅ CANDIDACY | v1.0.0 | 0.95 | A | CSV published; Kalachakra detailed table pending (RDO-DEP-003) |
| RF-KARAKA | ✅ STABLE | v1.0.0 | 0.95 | A | CSV + JSON published; naisargika karakas only |
| RF-EPHEM | ✅ CANDIDACY | v1.0.0 | 0.90 | A | Swiss Ephemeris files documented; full spec pending (RDO-DEP-004) |
| RF-AYAN | ⏳ CANDIDACY | v1.0.0 | 0.70 | B | 6 systems defined; exact values pending Knowledge Office (RDO-DEP-005) |
| RF-TZ | ⏳ PLACEHOLDER | v1.0.0 | 0.30 | D | Depends on IANA tzdata (RDO-DEP-006) + GeoNames (RDO-DEP-007) |

### Research Datasets (RS)

| Dataset | Status | Version | Quality Score | Tier | Notes |
|---------|--------|---------|---------------|------|-------|
| RS-COHORT | ✅ STABLE | v1.0.0 | 1.0 | A | 49,964 records imported via dataset import framework; 16 fields; CC-BY-4.0 |
| RS-EVENT | 🟡 CANDIDACY | v0.1.0 | — | — | 60 seed events from 12 public figures |
| RS-MARRIAGE | 🟡 CANDIDACY | v0.1.0 | — | — | 3 marriage events from RS-EVENT |
| RS-CAREER | 🟡 CANDIDACY | v0.1.0 | — | — | 31 career events from RS-EVENT |
| RS-HEALTH | 🔴 NOT STARTED | — | — | — | Depends on RS-EVENT. A v0.1.0 (183 records) existed 2026-07-16–17 but was a filtered derivative of the fabricated RS-EVENT v1.0.0 tree — deleted 2026-07-17 as part of GD-RDO-001's closure; see governance/GD-RDO-001. |
| RS-WEALTH | 🔴 NOT STARTED | — | — | — | Depends on RS-EVENT. Same history as RS-HEALTH above — deleted fabricated v0.1.0 (44 of 183 rows had literal unfilled template placeholders). |
| RS-SPIRITUAL | 🔴 NOT STARTED | — | — | — | Depends on RS-EVENT. Same history as RS-HEALTH above — deleted fabricated v0.1.0. |
| RS-FLAT | 🔴 NOT STARTED | — | — | — | Pipeline spec complete; needs computation |

### Benchmark Datasets (BM)

| Dataset | Status | Version | Quality Score | Tier | Notes |
|---------|--------|---------|---------------|------|-------|
| BM-CALC | 🟡 CANDIDACY | v0.1.0 | — | — | 25 test cases covering planet positions, ascendant, houses, combustion |
| BM-ASPECT | 🟡 CANDIDACY | v0.1.0 | — | — | 25 test cases covering all aspect types |
| BM-DASHA | 🟡 CANDIDACY | v0.1.0 | — | — | 10 test cases covering Vimshottari/Yogini |
| BM-TRANSIT | 🟡 CANDIDACY | v0.1.0 | — | — | 20 test cases covering sign/house/aspect overlays |
| BM-BALA | 🟡 CANDIDACY | v0.1.0 | — | — | 17 test cases covering Sthana/Dig/Naisargika/Kendra/Trikona/Dusthana |
| BM-ASTAK | 🟡 CANDIDACY | v0.1.0 | — | — | 15 test cases covering Bhinna/Sarva/Bindu validation |
| BM-DIV | 🟡 CANDIDACY | v0.1.0 | — | — | 30 test cases covering D3/D4/D7/D9/D10/D12 + boundary cases |
| BM-PERF | 🔴 NOT STARTED | — | — | — | Needs performance baseline |

### Validation / QA / Test Datasets (VL, QT)

| Dataset | Status | Version | Notes |
|---------|--------|---------|-------|
| VL-XPLATFORM | 🔴 NOT STARTED | — | Needs cross-software comparison |
| VL-CHART | 🔴 NOT STARTED | — | Needs end-to-end chart validation |
| VL-CONSISTENCY | 🟡 CANDIDACY | v0.1.0 | 25 rules from Phase 5 §4 (15 universal + 10 astrological) |
| QT-REGRESSION | 🔴 NOT STARTED | — | Needs baseline engine output hashes |
| QT-EDGE | 🔴 NOT STARTED | — | Edge cases catalogued in system |
| QT-STRESS | 🔴 NOT STARTED | — | Needs generation script |
| QT-INTEGRATION | 🔴 NOT STARTED | — | Needs scenario definitions |

### AI Evaluation Datasets (AI)

| Dataset | Status | Version | Notes |
|---------|--------|---------|-------|
| AI-INTERP | 🔴 NOT STARTED | — | Needs reference interpretations |
| AI-HALLUC | 🔴 NOT STARTED | — | Needs hallucination pattern catalog |
| AI-FACT | 🟡 CANDIDACY | v0.1.0 | 30 QA pairs covering dasha, dignity, houses, karaka, combustion |
| AI-REPORT | 🔴 NOT STARTED | — | Needs human-written reference reports |
| AI-RULE | 🔴 NOT STARTED | — | Needs rule evaluation test cases |

### Synthetic Datasets (SY)

| Dataset | Status | Version | Notes |
|---------|--------|---------|-------|
| SY-RANDOM | ✅ STABLE | v1.0.0 | 100K records, seed=42, 15.6 MB CSV, geographic+uniform distribution |
| SY-CONTROLLED | 🔴 NOT STARTED | — | Experiment design needed |
| SY-MONTE | 🔴 NOT STARTED | — | Scale target: 1M from SY-RANDOM |
| SY-NULL | ⏳ SPECIFICATION | v1.0.0 | Companion dataset spec published; per-study generation

### Public Datasets (PB)

| Dataset | Status | Version | Notes |
|---------|--------|---------|-------|
| PB-WIKI | 🟡 CANDIDACY | v0.1.0 | 30 records; extraction spec designed; target 10K+ |
| PB-WIKIDATA | 🟡 CANDIDACY | v0.1.0 | 10 records; SPARQL extraction spec complete; CC-0 |
| PB-EVENTS | 🟡 CANDIDACY | v0.1.0 | 20 verified events across 7 charts; all categories covered |
| PB-TWIN | 🔴 NOT STARTED | — | Twin pair identification needed |

### Licensed / User-Contributed (LC, UC)

| Dataset | Status | Version | Notes |
|---------|--------|---------|-------|
| LC-SWISS | 🟡 LICENSE EXISTS | — | Swiss Ephemeris already deployed |
| LC-CHART | 🔴 NOT STARTED | — | Needs commercial data evaluation |
| LC-PARTNER | 🔴 NOT STARTED | — | Needs partner agreements |
| UC-USER | 🔴 NOT STARTED | — | Platform feature (not dataset team) |
| UC-EVENT | 🔴 NOT STARTED | — | Platform feature (not dataset team) |
| UC-COHORT | 🔴 NOT STARTED | — | Platform feature (not dataset team) |

### Legend

| Status | Meaning |
|--------|---------|
| 🟢 SEEDED | Data exists in database; needs format packaging |
| 🟡 NOT STARTED | Design complete but no data collected |
| 🔴 NOT STARTED | No work begun |

---

## 3. Key Metrics

| Metric | Value |
|--------|-------|
| Phases complete | 7 of 7 |
| Active roadmap milestones | M1 ✅ M2 ✅ — M3–M7 pending |
| Dataset types defined | 51 |
| Dataset types RELEASED (Stable) | 8 (RF-SIGNS, RF-NAK, RF-PADA, RF-PLANET, RF-HOUSE, RF-KARAKA, SY-RANDOM, RS-COHORT) |
| Dataset types CANDIDACY | 20 (RF-DASHA, RF-EPHEM, RF-AYAN, PB-WIKI, PB-WIKIDATA, PB-EVENTS, SY-NULL, RS-FLAT, RS-EVENT, RS-MARRIAGE, RS-CAREER, BM-ASPECT, BM-DASHA, BM-BALA, BM-ASTAK, BM-DIV, VL-CONSISTENCY, BM-TRANSIT, BM-CALC, AI-FACT) |
| Dataset types PLACEHOLDER | 1 (RF-TZ) |
| Dataset types NOT STARTED | 23 |
| Candidate datasets evaluated | 0 |
| Milestones completed | M1, M2, M3 |
| Milestones in progress | M4 (Phase D) |
| Governance decisions pending | 5 (GD-002 through GD-006) |
| Governance decisions resolved | 1 (GD-RDO-001) |

---

## 4. Open Governance Decisions

| ID | Decision | Context | Needed By | Status |
|----|----------|---------|-----------|--------|
| GD-002 | Public figure privacy threshold | When does person qualify as "public" | Phase C start | ⏳ PENDING |
| GD-003 | Ethics board composition | Who oversees dataset ethics | Phase C start | ⏳ PENDING |
| GD-004 | Community cohort sharing policy | User cohort visibility rules | Phase D end | ⏳ PENDING |
| GD-005 | AI training data policy | Can public datasets train AI models | Phase F start | ⏳ PENDING |
| GD-006 | Commercial data budget | Budget for licensed chart data | Phase G | ⏳ PENDING |
| **GD-RDO-001** | **RS-EVENT v1.0.0 data integrity** — `research-data/research/event/ASTRO-RS-EVENT-v1.0.0/` was template-generated (fixed seed, 44/1,098 rows with unfilled `{placeholder}` text) but self-labeled as `Curated`/`manual_curation`/`verified_multi_source`/`Stable`. Never referenced or endorsed by this office's own STATUS/INDEX/ROADMAP. See [governance/GD-RDO-001_RS_EVENT_DATA_INTEGRITY.md](governance/GD-RDO-001_RS_EVENT_DATA_INTEGRITY.md) for full evidence and closure record. | Disposition decided 2026-07-17: **deleted** — never committed to git, so removal has no history impact; not relabeled as synthetic because the fabricated events name real, identifiable historical figures. | Before RS-EVENT v1.0.0 is ever treated as real | 🟢 RESOLVED (2026-07-17) |

---

## 5. External Dependencies

| Dependency | Status | Owner | Notes |
|------------|--------|-------|-------|
| **ER-001: Dataset Import Framework** | ✅ COMPLETE | Engineering Office | Excel import pipeline — RS-COHORT v1.0.0 (49,964 records) delivered and validated |
| IANA tzdata | ON TRACK | External | Quarterly releases |
| Swiss Ephemeris | ON TRACK | External | Annual license renewal |
| JPL Horizons API | AVAILABLE | NASA/JPL | Public API, rate-limited |
| Wikipedia API | AVAILABLE | Wikimedia | Rate-limited, caching needed |
| Wikidata SPARQL | AVAILABLE | Wikimedia | Query limits apply |

---

## 6. Next Actions (Immediate — Phase D)

**Current Milestone:** M4 (Phase D — Event Datasets)
**Gate:** RS-EVENT v1.0.0 with ≥1,000 verified events, Tier A quality

**Current State:**
- RS-EVENT v0.1.0: 60 seed events (need 1,000+)
- RS-MARRIAGE v0.1.0: 3 events
- RS-CAREER v0.1.0: 31 events

**Immediate Actions:**
1. **Scale RS-EVENT to ≥1,000 events** — Expand seed dataset with more public biography events
2. **Create RS-HEALTH, RS-WEALTH, RS-SPIRITUAL** — Event subsets from expanded RS-EVENT
3. **Validate all event subsets** — Apply RDO quality standards
4. **Update management documents** — STATUS.md, INDEX.md
5. **Reassess M4 gate** — Verify ≥1,000 events, Tier A quality

**Process-integrity note (added 2026-07-17, see GD-RDO-001):** a template-generated file matching this exact gate's numeric target (1,098 events, self-claimed `verified_multi_source`/`Stable`) was found sitting in this directory and has been deleted — see `governance/GD-RDO-001_RS_EVENT_DATA_INTEGRITY.md` §6. Whatever satisfies "Scale RS-EVENT to ≥1,000 events" going forward must be individually source-traceable, not a bare count — a record count and a `verification_status` field alone are not sufficient evidence of real curation, as this incident demonstrated.

**External Dependencies:** None (RS-COHORT provides chart data for event linking)

---

*End of STATUS. See ROADMAP.md for the authoritative implementation plan.*
