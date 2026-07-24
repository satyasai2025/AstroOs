# AstroOS v2.0 Index

> Cross-reference of v2 governance documents and their relationship to v1's office documentation.
> Date: 2026-07-17

## v2 Governance Documents

| Document | Path | Purpose |
|---|---|---|
| ASTROOS_V2_ROADMAP.md | `ASTROOS_V2_ROADMAP.md` | Authoritative v2 build plan — phases A–H, office operating model, M1 milestone |
| ASTROOS_V2_STATUS.md | `ASTROOS_V2_STATUS.md` | Current status of every v2 phase |
| ASTROOS_V2_INDEX.md | `ASTROOS_V2_INDEX.md` | This document |
| ASTROOS_V2_RELEASE_PLAN.md | `ASTROOS_V2_RELEASE_PLAN.md` | Versioning, tagging, and deployment strategy for v2 |
| ASTROOS_V2_MILESTONES.md | `ASTROOS_V2_MILESTONES.md` | Milestone tracker, starting with M1 |
| CHANGELOG_V2.md | `CHANGELOG_V2.md` | Dated changelog of v2 work |
| ALPHA_RELEASE_READINESS_REPORT.md | `ALPHA_RELEASE_READINESS_REPORT.md` | GD-RDO-001 closure + authoritative readiness assessment, supersedes `FOUNDATION_RELEASE_REVIEW.md`'s verdict |

## Source planning documents

| Document | Path | Role |
|---|---|---|
| AstroOS v2.0 Vision | `planning/vision/AstroOS v2.0 Vision.txt` | Theme and phase list this roadmap is built from |
| AstroOS v2.0 (office prompts) | `AstroOS v2.0.txt` | Defines the five-office operating model (CEO-ENG, CAO, CKO, CBO, CRDO) carried into `ASTROOS_V2_ROADMAP.md`'s "Operating model" section |

## Relationship to v1 documentation

**v1 office roadmaps remain in force as historical records and governance references — they are not superseded, reopened, or duplicated by the v2 documents above.**

| Office | v1 documents (still authoritative for v1-era decisions) | v2 documents (authoritative for new work) |
|---|---|---|
| Engineering | `ENGINEERING_ROADMAP.md`, `ENGINEERING_STATUS.md`, `ENGINEERING_INDEX.md`, `ENGINEERING_COMPLETION_REPORT.md` | `ASTROOS_V2_ROADMAP.md` Phase A (Engineering-owned objectives), `CHANGELOG_V2.md` |
| Architecture | `architecture/ROADMAP.md`, `architecture/STATUS.md`, `architecture/INDEX.md`, `architecture/COMPLETION_REPORT.md`, `architecture/decisions/*.md` (ADRs/AMPs) | Any new v2 ADR/RFC continues to live under `architecture/decisions/` — this index does not introduce a second ADR log |
| Knowledge | `knowledge/ROADMAP.md`, `knowledge/STATUS.md`, `knowledge/INDEX.md`, `knowledge/KNOWLEDGE_COMPLETION_REPORT.md` | `ASTROOS_V2_ROADMAP.md` Phase D (Knowledge Intelligence) |
| Benchmark | `benchmarks/BENCHMARK_ROADMAP.md`, `benchmarks/BENCHMARK_STATUS.md`, `benchmarks/BENCHMARK_INDEX.md` | `ASTROOS_V2_ROADMAP.md` Phase C (Benchmark Execution) |
| Research Data | `research-data/ROADMAP.md`, `research-data/STATUS.md`, `research-data/INDEX.md`, `research-data/governance/*.md` (including resolved finding `GD-RDO-001`) | `ASTROOS_V2_ROADMAP.md` Phase B (Research Engine) |

**Rule:** a v2 phase touching a v1 office's owned artifacts (e.g. Phase D modifying Knowledge's ontology, Phase C running Benchmark's specs) goes through that office's same formal-request discipline v1 established (KR/BR/RDR/ADR/ER) — v2 phase ownership in the table above does not grant unilateral edit rights over v1 content.

## Quick status snapshot

See `ASTROOS_V2_STATUS.md` for full detail. As of 2026-07-17: Phase A complete (all 4 objectives), M1 milestone 9/10 criteria done, `GD-RDO-001` resolved, `v1.0.0-alpha` already tagged but stale relative to the working tree (see `ALPHA_RELEASE_READINESS_REPORT.md`), Phases B–H not started.

---

*Last updated: 2026-07-17*
