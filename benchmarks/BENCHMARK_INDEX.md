# AstroOS Benchmark Office — INDEX

> **Status:** ACTIVE
> **Owner:** Chief QA & Benchmark Architect (Agent 4)
> **Version:** 1.0
> **Date:** 2026-07-15

---

## 1. Core Governance Artifacts

| # | Artifact | Phase | File | Status |
|---|----------|-------|------|--------|
| 1 | Benchmark Audit Report | 1 | *(inline)* | ✅ FROZEN |
| 2 | Benchmark Implementation Roadmap | — | [BENCHMARK_ROADMAP.md](BENCHMARK_ROADMAP.md) | ✅ ACTIVE |
| 3 | Benchmark Status Report | — | [BENCHMARK_STATUS.md](BENCHMARK_STATUS.md) | ✅ ACTIVE |
| 4 | Benchmark Index (this file) | — | [BENCHMARK_INDEX.md](BENCHMARK_INDEX.md) | ✅ ACTIVE |

---

## 2. Benchmark Family Index (20 Families)

### Calculation Benchmarks (Phase A)

| ID | Name | AstroOS Module | Specification Status | Data Dependencies |
|----|------|----------------|---------------------|-------------------|
| BM-CALC | Planet Position Calculation | M2 — Chart Engine | ✅ FROZEN | Swiss Ephemeris, JPL Horizons |
| BM-HOUSE | House Cusp Calculation | M3 — House Engine | ✅ FROZEN | GC-MASTER |
| BM-VARGA | Divisional Chart Calculation | M6 — Divisional Charts | 🔴 NOT STARTED | GC-MASTER |
| BM-ONT | Ontology Verification | M12 — Astrology Ontology | 🔴 NOT STARTED | OntologyRegistry |

### Planetary Analysis Benchmarks (Phase B)

| ID | Name | AstroOS Module | Specification Status | Data Dependencies |
|----|------|----------------|---------------------|-------------------|
| BM-YOGA | Yoga Detection | M8 — Yoga Engine | 🔴 NOT STARTED | GC-MASTER, YogaRegistry (38 yogas) |
| BM-YOGA-EDGE | Yoga Edge Cases | M8 — Yoga Engine | 🔴 NOT STARTED | BM-YOGA |
| BM-BALA | Shadbala Computation | M9 — Shadbala Engine | 🔴 NOT STARTED | GC-MASTER, ShadbalaEngine (15 components) |
| BM-ASTAK | Ashtakavarga Computation | M7 — Ashtakavarga | 🔴 NOT STARTED | GC-MASTER, AshtakavargaEngine |
| BM-TRANSIT | Transit (Gochara) Computation | M11 — Transit Engine | 🔴 NOT STARTED | GC-MASTER, TransitEngine |

### Rule & Event Benchmarks (Phase C)

| ID | Name | AstroOS Module | Specification Status | Data Dependencies |
|----|------|----------------|---------------------|-------------------|
| BM-RULE | Rule Engine Evaluation | M13 — Rule Engine | 🔴 NOT STARTED | GC-MASTER, RuleRegistry (36 rules) |
| BM-RULE-EDGE | Rule Engine Edge Cases | M13 — Rule Engine | 🔴 NOT STARTED | BM-RULE |
| BM-EVENT | Event Detection | M14 — Event Engine | 🔴 NOT STARTED | GC-MASTER, PB-EVENTS |
| BM-TIMELINE | Timeline Construction | M15 — Timeline Engine | 🔴 NOT STARTED | BM-DASHA, BM-EVENT |
| BM-VERIFY | Verification Engine | M16 — Verification Engine | 🔴 NOT STARTED | BM-RULE, BM-EVENT |
| BM-DASHA | Dasha Computation | M5 — Dasha Module | 🔴 NOT STARTED | GC-MASTER, DashaEngine (6 systems) |

### API & Integration Benchmarks (Phase D)

| ID | Name | AstroOS Module | Specification Status | Data Dependencies |
|----|------|----------------|---------------------|-------------------|
| BM-API | API Correctness | All Routers | 🔴 NOT STARTED | GC-MASTER |
| BM-API-AUTH | Auth Flow | M1 — Foundation | 🔴 NOT STARTED | None |
| BM-API-ERROR | Error Handling | All Routers | 🔴 NOT STARTED | None |
| BM-PERF-CALC | Calculation Performance | All Engines | 🔴 NOT STARTED | BM-CALC infra |
| BM-PERF-THROUGHPUT | API Throughput | All Routers | 🔴 NOT STARTED | BM-API |
| VL-CONSISTENCY | Cross-Engine Consistency | All Engines | 🔴 NOT STARTED | All BM-* |

### AI Benchmarks (Phase E)

| ID | Name | AstroOS Module | Specification Status | Data Dependencies |
|----|------|----------------|---------------------|-------------------|
| BM-AI-FACT | AI Factual Accuracy | M19 — AI Engine | 🔴 NOT STARTED | RF-*, KnowledgeBase |
| BM-AI-INTERP | AI Interpretation Quality | M19 — AI Engine | 🔴 NOT STARTED | GC-MASTER |
| BM-AI-HALLUC | AI Hallucination Resistance | M19 — AI Engine | 🔴 NOT STARTED | BM-AI-FACT |
| BM-AI-REPORT | AI Report Generation | M20 — Report Engine | 🔴 NOT STARTED | BM-AI-INTERP |
| BM-RESEARCH | Research Engine Reproducibility | M17 — Research Engine | 🔴 NOT STARTED | GC-MASTER |
| BM-STATS | Statistics Engine Correctness | M18 — Statistics Engine | 🔴 NOT STARTED | SY-RANDOM |

### Regression, Edge Cases & Cross-Platform (Phase F–G)

| ID | Name | AstroOS Module | Specification Status | Data Dependencies |
|----|------|----------------|---------------------|-------------------|
| BM-REGRESS | Historical Bug Regression | All Modules | 🔴 NOT STARTED | All BM-* |
| BM-EDGE | Edge Case Catalogue | All Modules | 🔴 NOT STARTED | None |
| BM-INTEGRATION | Cross-Engine Integration | All Modules | 🔴 NOT STARTED | All BM-* |
| BM-PERF-STRESS | Stress/Volume Testing | All Modules | 🔴 NOT STARTED | BM-PERF |
| VL-XPLATFORM | Cross-Platform Validation | All Engines | 🔴 NOT STARTED | GC-MASTER |

### CI/Automation (Phase G)

| ID | Name | Specification Status | Data Dependencies |
|----|------|---------------------|-------------------|
| CI-UNIT | Benchmark Spec Runner | 🔴 NOT STARTED | All BM-* |
| CI-GOLDEN | Golden Dataset Integrity | 🔴 NOT STARTED | GC-MASTER |
| CI-REGRESSION | Automated Regression Detection | 🔴 NOT STARTED | BM-REGRESS |
| CI-PERF | Performance Regression Alerting | 🔴 NOT STARTED | BM-PERF |
| CI-REPORT | Automated Benchmark Report | 🔴 NOT STARTED | CI-* infra |

---

## 3. AstroOS Module-to-Benchmark Mapping

| Module # | Module Name | Primary Benchmark(s) | Secondary Benchmark(s) |
|----------|-------------|---------------------|----------------------|
| M1 | Foundation | BM-API-AUTH | BM-API-ERROR |
| M2 | Chart Engine | BM-CALC | BM-PERF-CALC |
| M3 | Graha/House/Aspect | BM-HOUSE, BM-BALA | VL-CONSISTENCY |
| M4 | Nakshatra | BM-CALC | BM-ONT |
| M5 | Dasha Module | BM-DASHA | BM-TIMELINE |
| M6 | Divisional Charts | BM-VARGA | BM-BALA (Saptavargaja/Ojayugmarasyamsa) |
| M7 | Ashtakavarga | BM-ASTAK | BM-TRANSIT |
| M8 | Yoga Engine | BM-YOGA, BM-YOGA-EDGE | BM-RULE |
| M9 | Shadbala Engine | BM-BALA | BM-VERIFY |
| M10 | — (part of M7) | — | — |
| M11 | Transit Engine | BM-TRANSIT | BM-EVENT |
| M12 | Ontology | BM-ONT | BM-AI-FACT |
| M13 | Rule Engine | BM-RULE, BM-RULE-EDGE | BM-VERIFY |
| M14 | Event Engine | BM-EVENT | BM-TIMELINE |
| M15 | Timeline Engine | BM-TIMELINE | BM-VERIFY |
| M16 | Verification Engine | BM-VERIFY | BM-RESEARCH |
| M17 | Research Engine | BM-RESEARCH | BM-STATS |
| M18 | Statistics Engine | BM-STATS | BM-RESEARCH |
| M19 | AI Engine | BM-AI-FACT, BM-AI-INTERP, BM-AI-HALLUC | BM-AI-REPORT |
| M20 | Report Engine | BM-AI-REPORT | BM-API |
| M21 | Export Engine | BM-API | BM-PERF |
| M22 | Visualization Engine | BM-API | BM-PERF |
| M23 | Admin Engine | BM-API | BM-API-AUTH |
| M24 | SDK Service | BM-API | — |
| M25 | Knowledge Engine | BM-AI-FACT | BM-ONT |
| M26 | Fact System | BM-RULE | BM-VERIFY |
| M27 | Production Readiness | BM-REGRESS, BM-PERF-STRESS | CI-* |

---

## 4. Cross-Cutting Specifications

| Artifact | Status | Location (when created) |
|----------|--------|------------------------|
| Benchmark Specification Template | ✅ FROZEN | `templates/benchmark-spec-template.md` |
| Golden Chart JSON Schema | ✅ FROZEN | `datasets/GC-MASTER-design.md` (§2.2) |
| Expected Results Format | ✅ FROZEN | `specifications/BM-CALC-expected-results.md` (§3) |
| Tolerance Matrix | ✅ FROZEN | `specifications/BM-CALC-master.md` (§8) |
| Confidence Classification (Verified/Estimated/Synthetic) | ✅ FROZEN | `specifications/BM-CALC-master.md` (§9) |
| Validation Matrix Template | ✅ FROZEN | `specifications/BM-CALC-validation-matrix.md` |
| Edge Case Classification Schema | 🔴 NOT STARTED | Phase 3/4 deliverable |
| Performance Baseline Format | 🔴 NOT STARTED | Phase 3 deliverable |

---

## 5. Reference Datasets (shared with RDO)

| Dataset | RDO Code | Available At | Notes |
|---------|----------|-------------|-------|
| Reference Signs | RF-SIGNS | RDO Phase A | 12 signs with lords, elements, modalities |
| Reference Nakshatras | RF-NAK | RDO Phase A | 27 nakshatras with lords, degrees |
| Reference Padas | RF-PADA | RDO Phase A | 108 padas, mathematically verified |
| Reference Planets | RF-PLANET | RDO Phase A | 9 grahas with classical attributes |
| Reference Houses | RF-HOUSE | RDO Phase A | 12 bhavas with significations |
| Reference Dashas | RF-DASHA | RDO Phase A | Period tables for 6 systems |
| Reference Karakas | RF-KARAKA | RDO Phase A | Naisargika karaka significations |

---

## 6. Supporting Knowledge Base

| Document | Type | Relevance |
|----------|------|-----------|
| [AstroOS Architecture Reference](../memory/../docs/architecture.md)* | Architecture | Full module documentation (27 modules) |
| [AstroOS README](../memory/../README.md)* | Project | Project overview, tech stack, setup |
| [RDO: Dataset Standards](../memory/astrosos-dataset-standards.md) | Handbook | Dataset quality/validation patterns |
| [RDO: Dataset Quality](../memory/astrosos-dataset-quality.md) | Handbook | Quality scoring, bias assessment |
| [AstroOS v2.0 Tech Research](../memory/astrosos-v2-technology-research.md) | Research | Platform architecture context |
| [Handbook: CQRS](../memory/handbook-cqrs.md) | Handbook | Read/write separation patterns |
| [Handbook: Verification Engine Design](to-be-created) | Design | Verification engine architecture |

*\*Accessible via AstroOS project directory at `C:\Users\rkmau\Downloads\ReplitplusClaude\AstroOS\`*

---

*End of INDEX. See [BENCHMARK_ROADMAP.md](BENCHMARK_ROADMAP.md) for the authoritative implementation plan.*
