# AstroOS v2.0 Roadmap

> Authoritative build plan for AstroOS v2 — phases, deliverables, office ownership, and the first milestone.
> Source: `planning/vision/AstroOS v2.0 Vision.txt` (theme and phase list) and `AstroOS v2.0.txt` (five-office operating model).
> The v1 office roadmaps (`ENGINEERING_ROADMAP.md`, `architecture/ROADMAP.md`, `benchmarks/BENCHMARK_ROADMAP.md`, `knowledge/ROADMAP.md`, `research-data/ROADMAP.md`) remain in force as historical records and governance references — this document does not supersede them, it sits alongside them for everything that is new v2 work.
> Date: 2026-07-17

## Theme

**From Foundation to Intelligent Astrology Platform.** v1 produced specifications, documentation, and a governed but largely API-unexposed engine. v2 shifts the emphasis to execution, integration, user experience, and research — turning what v1 specified and built into something a user or researcher can actually run against.

## Operating model

Per `AstroOS v2.0.txt`, five offices continue with the same non-overlapping boundaries v1 established, now applied to execution rather than specification:

| Office | Owns | Does NOT own | Workflow |
|---|---|---|---|
| Engineering (CEO-ENG) | Backend, frontend, SDKs, API layer, DB, CI/CD, testing, performance, security, DevOps | Architecture decisions, astrology knowledge, benchmarks, research datasets | Requirement → Design Review → Implementation → Testing → CI → Docs → Engineering Audit |
| Architecture (CAO) | System architecture, ADRs, RFCs, module boundaries, dependency rules | Implementation | Requirement → Research → Architecture → Review → Approval → Governance |
| Knowledge (CKO) | Ontology, classical texts, catalogues, glossary, cross-references, conflicts, Knowledge Graph | Calculations | Research → Source Verification → Knowledge Modeling → Review → Approval |
| Benchmark (CBO) | Benchmark specs, gold-standard datasets, accuracy metrics, validation methodology | Algorithm implementation | Specification → Dataset Selection → Validation Design → Review → Approval |
| Research Data (CRDO) | Research datasets, metadata, data standards, import pipelines, dataset quality/versioning | Benchmark rules, software implementation | Acquire → Clean → Validate → Version → Publish → Audit |

Cross-office work flows through formal requests (ER/ADR·RFC/KR/BR/RDR), same discipline v1 used — Engineering does not modify Architecture/Benchmark/Knowledge/Research Data content without one, and vice versa.

## Phases

### Phase A — Platform Integration (2–3 weeks)

**Objectives:**
1. Complete API exposure for approved public services.
2. Integrate the frontend (`apps/web`) with backend APIs.
3. Connect Knowledge Engine, Rule Engine, and Report Engine to each other (not merely individually reachable).
4. Complete authentication and user workflows.

**Deliverable:** AstroOS Platform Alpha.

**Status:** Objective 1 is substantially complete — see `ASTROOS_V2_STATUS.md`. Objectives 2–4 not started.

### Phase B — Research Engine

**Objectives:** Execute Research Data Office datasets; Dataset Registry; Statistical Engine; Event Correlation; Research Dashboard.

**Deliverable:** AstroOS Research Platform.

### Phase C — Benchmark Execution

Unlike v1 (which produced specifications only), v2 executes them: run BM-CALC, BM-HOUSE, BM-VARGA, BM-ONT and generate measurable benchmark reports.

### Phase D — Knowledge Intelligence

Move beyond static catalogues: Knowledge Graph, rule explanation engine, citation engine, conflict-aware reasoning.

### Phase E — AI Layer

AstroOS's differentiator: natural-language horoscope queries, explaining *why* a yoga exists, a research assistant, chart comparison, hypothesis generation, knowledge retrieval with citations.

### Phase F — Reports

Professional reports (Horoscope, Dasha, Transit, Marriage, Career, Health, Wealth, Spiritual, Research), exportable as PDF / JSON / API.

### Phase G — SDK

Complete Python SDK, REST SDK, CLI, plugin architecture.

### Phase H — Production

Docker, monitoring, logging, backups, deployment, versioning, release pipeline.

## First v2 Milestone — M1

**"First End-to-End Astrology Pipeline"**

Success criteria:
- Enter birth details
- Generate D1 chart
- Generate all required Vargas
- Compute Dashas
- Detect Yogas
- Apply Rule Engine
- Query Knowledge Office
- Correlate Research Data
- Produce a cited report
- Validate against Benchmark specifications

This is a complete vertical slice of AstroOS, not isolated components — see `ASTROOS_V2_MILESTONES.md` for tracked progress against each criterion.

## Roadmap rules

- This roadmap, read fresh at the time of the decision, is the sequencing authority for v2 work — same discipline the v1 Architecture roadmap used.
- Work proceeds phase by phase (A → H); a skip must be justified by an actual dependency, not convenience.
- New phases or scope changes require an explicit decision recorded in `ASTROOS_V2_STATUS.md`, not silent expansion.
- v1 office roadmaps are not reopened by this document. If v2 work requires a v1 artifact to change, it goes through that office's formal request process.

## Open dependency

`planning/vision/AstroOS v2.0 Vision.txt` recommended committing and tagging `v1.0.0-foundation` as a clean baseline before v2 coding began. Following extensive Phase A0 and Phase A1 completion, all open blockers have been resolved. The baseline is officially frozen, and instead of a foundation tag, the completion of Phase A allows us to push and tag `v1.0.0-alpha` directly.

---

*Last updated: 2026-07-17*
