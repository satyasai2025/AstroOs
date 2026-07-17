# AstroOS Benchmark Office — ROADMAP

> **Status:** ACTIVE — authoritative implementation plan
> **Owner:** Chief QA & Benchmark Architect (Agent 4)
> **Version:** 1.0
> **Date:** 2026-07-15
> **Supersedes:** All prior informal benchmark planning

---

## 0. Benchmark ID Convention

Every benchmark artifact is identified by a structured code:

```
BM-{CATEGORY}-{NNN}
```

| Prefix | Category | Example |
|--------|----------|---------|
| `BM-CALC` | Calculation Accuracy Benchmarks | `BM-CALC-001` |
| `BM-HOUSE` | House Calculation Benchmarks | `BM-HOUSE-001` |
| `BM-VARGA` | Varga/Divisional Chart Benchmarks | `BM-VARGA-001` |
| `BM-YOGA` | Yoga Detection Benchmarks | `BM-YOGA-001` |
| `BM-DASHA` | Dasha Computation Benchmarks | `BM-DASHA-001` |
| `BM-BALA` | Shadbala Benchmarks | `BM-BALA-001` |
| `BM-ASTAK` | Ashtakavarga Benchmarks | `BM-ASTAK-001` |
| `BM-TRANSIT` | Transit (Gochara) Benchmarks | `BM-TRANSIT-001` |
| `BM-RULE` | Rule Engine Benchmarks | `BM-RULE-001` |
| `BM-EVENT` | Event Engine Benchmarks | `BM-EVENT-001` |
| `BM-TIMELINE` | Timeline Engine Benchmarks | `BM-TIMELINE-001` |
| `BM-VERIFY` | Verification Engine Benchmarks | `BM-VERIFY-001` |
| `BM-RESEARCH` | Research Engine Benchmarks | `BM-RESEARCH-001` |
| `BM-STATS` | Statistics Engine Benchmarks | `BM-STATS-001` |
| `BM-AI` | AI Engine Evaluation Benchmarks | `BM-AI-001` |
| `BM-API` | API Correctness Benchmarks | `BM-API-001` |
| `BM-PERF` | Performance Benchmarks | `BM-PERF-001` |
| `BM-REGRESS` | Regression Suites | `BM-REGRESS-001` |
| `BM-EDGE` | Edge Case Catalogues | `BM-EDGE-001` |
| `BM-ONT` | Ontology Benchmarks | `BM-ONT-001` |

Additional dataset prefixes for reference/test data:

| Prefix | Category |
|--------|----------|
| `RF-*` | Reference Datasets (shared with RDO) |
| `GC-*` | Golden Chart Datasets (verified reference charts) |
| `SY-*` | Synthetic Datasets |
| `PB-*` | Public Figure Datasets |
| `VL-*` | Validation Data |

---

## 1. Build Phases

### Phase A — Foundation & Reference (Q3 2026)

**Goal:** Establish reference benchmarks, golden datasets, and basic calculation verification.

| Benchmark | Priority | Dependencies | Est. Effort |
|-----------|----------|-------------|-------------|
| **Governance** — ROADMAP, STATUS, INDEX | P0 | Phase 1 Audit | 1 session |
| **BM-CALC** — Planet position calculation (9 graha × 6 ayanamsa × 5 charts) | P0 | Swiss Ephemeris + JPL Horizons reference | ✅ COMPLETE (2026-07-15) |
| **BM-HOUSE** — House cusp calculation (4 systems × 10 charts) | P0 | BM-CALC | ✅ COMPLETE (2026-07-15) |
| **BM-VARGA** — Divisional chart calculation (15 vargas × 5 charts) | P0 | BM-HOUSE | 3 sessions |
| **BM-ONT** — Ontology entity/relationship verification | P0 | Module 12 (OntologyRegistry) | 1 session |
| **GC-MASTER** — Golden Master Dataset (5 verified reference charts) | P0 | BM-CALC, BM-HOUSE | 3 sessions |
| **RF-SIGNS/RF-NAK/RF-PADA** — Reference data (extract from seed migrations) | P1 | RDO Phase A | 1 session |
| **REGRESSION-SETUP** — Regression catalogue structure | P1 | None | 1 session |

**Gate:** All P0 benchmarks have specification documents approved and frozen.

---

### Phase B — Planetary Analysis (Q3 2026)

**Goal:** Validate all planet-centric calculation engines.

| Benchmark | Priority | Dependencies | Est. Effort |
|-----------|----------|-------------|-------------|
| **BM-YOGA** — All 38 yoga evaluators × GC-MASTER charts | P0 | GC-MASTER, YogaRegistry | 3 sessions |
| **BM-BALA** — Shadbala 15 components × GC-MASTER charts | P0 | GC-MASTER, ShadbalaEngine | 3 sessions |
| **BM-ASTAK** — Ashtakavarga + Shodhana × GC-MASTER charts | P0 | GC-MASTER, AshtakavargaEngine | 2 sessions |
| **BM-TRANSIT** — Transit + Vedha × GC-MASTER + date ranges | P0 | GC-MASTER, TransitEngine | 2 sessions |
| **BM-YOGA-EDGE** — Yoga boundary/edge cases (38 × false positives) | P1 | BM-YOGA | 2 sessions |

**Gate:** All P0 benchmarks produce expected results for GC-MASTER charts.

---

### Phase C — Rule & Event Systems (Q4 2026)

**Goal:** Validate the higher-order rule, event, timeline, and verification engines.

| Benchmark | Priority | Dependencies | Est. Effort |
|-----------|----------|-------------|-------------|
| **BM-RULE** — 36 rules × GC-MASTER charts (matched + unmatched) | P0 | GC-MASTER, RuleRegistry | 3 sessions |
| **BM-EVENT** — Event detection × known historical events | P0 | GC-MASTER + PB-EVENTS | 2 sessions |
| **BM-TIMELINE** — Timeline construction × known life timelines | P0 | BM-DASHA, BM-EVENT | 2 sessions |
| **BM-VERIFY** — Rule-vs-event alignment × known pairs | P0 | BM-RULE, BM-EVENT | 2 sessions |
| **BM-DASHA** — 6 dasha systems × historical event dates | P0 | GC-MASTER, DashaEngine | 3 sessions |
| **BM-RULE-EDGE** — Rule engine boundary cases | P1 | BM-RULE | 1 session |

**Gate:** Every rule/event/timeline/verification benchmark has known expected output.

---

### Phase D — API & Integration (Q4 2026)

**Goal:** Validate the full API surface and engine integration.

| Benchmark | Priority | Dependencies | Est. Effort |
|-----------|----------|-------------|-------------|
| **BM-API** — Request/response correctness (all 5 routers) | P0 | GC-MASTER, all engines | 3 sessions |
| **BM-API-AUTH** — Auth flow (register/login/refresh/logout) | P0 | None | 1 session |
| **BM-API-ERROR** — Error handling (invalid inputs, missing data) | P0 | None | 2 sessions |
| **BM-PERF-CALC** — Calculation latency baseline (mean/p95/p99) | P1 | BM-CALC infra | 1 session |
| **BM-PERF-THROUGHPUT** — Concurrent request baseline | P1 | BM-API | 1 session |
| **VL-CONSISTENCY** — Cross-engine consistency (same input → same output) | P1 | All BM-* | 2 sessions |

**Gate:** All API benchmarks pass against the actual running API.

---

### Phase E — AI & Research Engines (Q1 2027)

**Goal:** Verify AI engine correctness and research engine reproducibility.

| Benchmark | Priority | Dependencies | Est. Effort |
|-----------|----------|-------------|-------------|
| **BM-AI-FACT** — Factual accuracy (200+ QA pairs) | P0 | RF-* + knowledge base | 4 sessions |
| **BM-AI-INTERP** — Interpretation quality (50+ chart interpretations) | P0 | GC-MASTER, AIEngine | 3 sessions |
| **BM-AI-HALLUC** — Hallucination resistance (100+ adversarial inputs) | P0 | BM-AI-FACT | 3 sessions |
| **BM-AI-REPORT** — Report generation (10+ full report benchmarks) | P1 | BM-AI-INTERP | 2 sessions |
| **BM-RESEARCH** — Research engine reproducibility | P1 | GC-MASTER, ResearchEngine | 2 sessions |
| **BM-STATS** — Statistics engine correctness | P1 | SY-RANDOM | 2 sessions |

**Gate:** AI factual accuracy ≥ 90% on known-correct chart facts.

---

### Phase F — Full Regression & Stress (Q1–Q2 2027)

**Goal:** Build the complete regression and stress-testing infrastructure.

| Benchmark | Priority | Dependencies | Est. Effort |
|-----------|----------|-------------|-------------|
| **BM-REGRESS** — Historical bug regression suite | P0 | All BM-* | Ongoing |
| **BM-EDGE** — Systematic edge case collection (100+ cases) | P0 | None | 3 sessions |
| **BM-PERF-STRESS** — Stress/volume testing | P1 | BM-PERF baseline | 2 sessions |
| **BM-INTEGRATION** — Cross-engine integration scenarios | P1 | All BM-* | 3 sessions |
| **VL-XPLATFORM** — Cross-software comparison (Jagannatha Hora, etc.) | P2 | GC-MASTER | 3 sessions |

**Gate:** All regression tests pass before any v2.0 release candidate.

---

### Phase G — Automation & CI (Q2–Q3 2027)

**Goal:** Integrate the full benchmark suite into automated CI.

| Benchmark | Priority | Dependencies | Est. Effort |
|-----------|----------|-------------|-------------|
| **CI-UNIT** — Benchmark spec runner (pytest integration) | P0 | All BM-* | 3 sessions |
| **CI-GOLDEN** — Golden dataset integrity check (automatic) | P0 | GC-MASTER | 1 session |
| **CI-REGRESSION** — Automated regression detection | P0 | BM-REGRESS | 2 sessions |
| **CI-PERF** — Performance regression alerting | P1 | BM-PERF | 2 sessions |
| **CI-REPORT** — Automated benchmark report generation | P1 | CI-* infra | 2 sessions |

**Gate:** Full benchmark suite runs in CI on every PR to AstroOS.

---

## 2. External Dependencies

| Dependency | Required For | Status | Action Needed |
|------------|-------------|--------|---------------|
| **JPL Horizons API** | BM-CALC reference values (planet positions) | AVAILABLE | Query script per chart |
| **Swiss Ephemeris .se1 files** | Official-data calculations | AVAILABLE (optional) | Document mode differences |
| **IANA tzdata** | Timezone-aware chart verification | ON TRACK | Quarterly sync |
| **Jagannatha Hora / other software** | VL-XPLATFORM cross-validation | PENDING | Identify target software |
| **Wikipedia API** | PB-WIKI public chart collection | AVAILABLE | Share with RDO |
| **Classical text sources** | Yoga/rule verification | IN PROGRESS | Per-module sourcing already done |
| **RDO datasets** | Shared reference data integration | IN PROGRESS | RF-SIGNS/NAK/PADA available |

---

## 3. Governance Decisions Required

| ID | Decision | Context | Needed By | Recommendation |
|----|----------|---------|-----------|---------------|
| GD-BM-001 | **Golden chart sourcing policy** | How do we select public figures for golden datasets? | Phase A end | Birth time ≥ Tier B confidence; source must be documented |
| GD-BM-002 | **Tolerance specification** | What precision tolerance for each calculation type? | Phase A end | Positions: ≤ 0.1°; Aspects: ≤ 1°; Dasha dates: ±1 day |
| GD-BM-003 | **Ayanamsa reference standard** | Which ayanamsa values are authoritative for benchmarks? | Phase A end | Use Swiss Ephemeris values as ground truth |
| GD-BM-004 | **Cross-platform comparison scope** | Which external tools to compare against? | Phase F | Evaluate Jagannatha Hora + 1 more |
| GD-BM-005 | **AI evaluation methodology** | Human evaluation vs automated metrics? | Phase E start | Automated first; human eval for selected cases |
| GD-BM-006 | **Benchmark versioning scheme** | How to version benchmarks when engine behavior changes | Phase A end | SemVer: major on breaking spec changes, minor on additions |

---

## 4. Repository Infrastructure

| Need | Timeline | Notes |
|------|----------|-------|
| Benchmark directory structure | Immediate | `benchmarks/` root with per-phase subdirectories |
| Golden dataset format (JSON) | Phase A start | Deterministic JSON with content hash |
| Reference chart data files | Phase A start | Verified birth data with sources |
| Benchmark runner script | Phase G | Python harness or pytest plugin |
| Performance log storage | Phase E | Time-series DB or structured JSONL |
| CI integration | Phase G | GitHub Actions workflow |

---

## 5. Release Milestones

| Milestone | Date | Deliverables |
|-----------|------|-------------|
| **M-BM1: Foundation Ready** | 2026-08-01 | Governance docs frozen; BM-CALC ✅ FROZEN; BM-HOUSE ⬅️, BM-VARGA pending |
| **M-BM2: Golden Charts** | 2026-08-15 | GC-MASTER v1.0 (5 charts); BM-YOGA, BM-BALA, BM-ASTAK spec'd |
| **M-BM3: Engine Coverage** | 2026-09-15 | BM-RULE, BM-EVENT, BM-TIMELINE, BM-VERIFY, BM-DASHA spec'd |
| **M-BM4: API Verified** | 2026-10-15 | BM-API complete; BM-PERF baseline established |
| **M-BM5: AI Evaluated** | 2027-01-15 | BM-AI-FACT/INTERP/HALLUC complete |
| **M-BM6: Full Regression** | 2027-03-15 | BM-REGRESS + BM-EDGE complete |
| **M-BM7: CI Automated** | 2027-06-15 | Full suite automated; benchmark gate on AstroOS releases |

---

## 6. Quality Gates

Every phase gate requires:

- [ ] All P0 benchmark specifications approved and frozen
- [ ] Golden datasets verified against ≥ 2 independent calculation sources
- [ ] Expected results documented with confidence tier (Verified/Estimated/Synthetic)
- [ ] All edge cases catalogued
- [ ] Known limitations documented
- [ ] `_metadata.json` complete per benchmark specification
- [ ] Changelog initialized

**Release Gate (all AstroOS releases):**

- [ ] All BM-CALC, BM-HOUSE, BM-VARGA pass
- [ ] No regression in BM-REGRESS suite
- [ ] Performance within baseline tolerance (if BM-PERF established)
- [ ] All golden dataset integrity checksums match

---

## 7. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-15 | Chief QA & Benchmark Architect (Agent 4) | Initial authoritative roadmap |

---

*This ROADMAP is authoritative. All benchmark work shall proceed according to the phases and gates defined herein. Deviations require documented justification and approval.*
