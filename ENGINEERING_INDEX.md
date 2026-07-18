# AstroOS Engineering Index

> Complete cross-reference of all modules, test infrastructure, and supporting engineering documents.

## Project Documents

| Document | Path | Purpose |
|---|---|---|
| ENGINEERING_ROADMAP.md | `ENGINEERING_ROADMAP.md` | Build plan, milestones, governance decisions |
| ENGINEERING_STATUS.md | `ENGINEERING_STATUS.md` | Current status of all modules and test infrastructure |
| ENGINEERING_COMPLETION_REPORT.md | `ENGINEERING_COMPLETION_REPORT.md` | v1.0 final status report |
| REPOSITORY_CLEANUP_REPORT.md | `REPOSITORY_CLEANUP_REPORT.md` | 2026-07-16 audit: files deleted, `.env.example` fix, items reviewed and left alone |
| SECURITY_AUDIT_REPORT.md | `SECURITY_AUDIT_REPORT.md` | 2026-07-16 audit: `.env`/`.env.example` secrets, RSA key provenance and history exposure |
| GIT_CLEANUP_PLAN.md | `GIT_CLEANUP_PLAN.md` | 2026-07-16 plan (not executed): `.git` bloat root cause, reclaimable space, execution order |
| FINAL_ENGINEERING_AUDIT.md | `FINAL_ENGINEERING_AUDIT.md` | 2026-07-16 audit: CI reliability, API functionality verification, engineering integration validation |
| API_EXPOSURE_ASSESSMENT.md | `API_EXPOSURE_ASSESSMENT.md` | 2026-07-16 classification: which unrouted modules are intended-internal vs. candidate public APIs vs. supporting libraries |
| ONTOLOGY_REGISTRY_INTEGRATION_ASSESSMENT.md | `ONTOLOGY_REGISTRY_INTEGRATION_ASSESSMENT.md` | 2026-07-16 assessment (ER-002): whether Module 12 (Ontology) is unused, awaiting integration, obsolete, or should already be a dependency — finding: unintegrated, not obsolete; Module 24 (AI Engine) is a concrete integration candidate |

## Module Inventory (27 Modules)

> **API surface note (updated 2026-07-17 — see [API_EXPOSURE_ASSESSMENT.md](API_EXPOSURE_ASSESSMENT.md)):** All 13 "Candidate public API" modules that assessment identified now have a registered `APIRouter`: Ashtakavarga, Shadbala, Yoga, Transit, Timeline, Knowledge, Research, Statistics, Report, Export, Visualization, Admin Portal, AI Engine — alongside the original Auth, Horoscope (D1), Divisional Charts, Dasha, and Events. The HTTP surface grew from 17 to 87 endpoints. Astronomy Foundation (Module 2) and House/Bhava Engine (Module 6) remain intentionally internal-only (no client-facing deliverable independent of the routed responses they feed). Ontology (Module 12), the Rule Engine's Facts/Rules substrate (Module 13), Verification (Module 16), and SDK domain objects (Module 25) remain intentionally unrouted supporting libraries, per the same assessment's classification.
>
> Scope notes on the new routers: none have auth/role-gating (matches the pre-existing convention on every router); AI Engine wires 5 of 8 template generators (chart_summary, yoga_explanation, dasha_interpretation, transit_reading, qa — verification_report/research_insight/recommendation deferred, same placeholder-object complexity as Report); Visualization wires 5 of 6 types (timeline deferred for the same reason). Verified via `py_compile` + full app import + OpenAPI schema generation only — no live-DB test run was possible in this environment (see Test Suite Status below, unchanged).

| Module | Name | Status | Tests |
|---|---|---|---|
| Module 1 | Foundation | ✅ Complete | Unit |
| Module 2 | Astronomy Foundation | ✅ Complete | Unit |
| Module 3 | Birth Chart Engine | ✅ Complete | Unit + Integration |
| Module 4 | Divisional Charts | ✅ Complete | Unit + Integration |
| Module 5 | Graha Engine | ✅ Complete | Unit |
| Module 6 | House Engine | ✅ Complete | Unit + Integration |
| Module 7 | Aspect Engine | ✅ Complete | Unit + Integration |
| Module 8 | Yoga Engine | ✅ Complete | Unit + Integration |
| Module 9 | Shadbala Engine | ✅ Complete | Unit + Integration |
| Module 10 | Ashtakavarga Engine | ✅ Complete | Unit + Integration |
| Module 11 | Transit Engine | ✅ Complete | Unit + Integration |
| Module 12 | Astrology Ontology | ✅ Complete | Unit |
| Module 13 Phase 1 | Rule Engine Phase 1 | ✅ Complete | Unit |
| Module 13 Phase 2 | Rule Engine Phase 2 | ✅ Complete | Unit + Integration |
| Module 14 | Event Engine | ✅ Complete | Unit + Integration |
| Module 15 | Timeline Engine | ✅ Complete | Unit + Integration |
| Module 16 | Verification Engine | ✅ Complete | Unit + Integration |
| Module 17 | Research Engine | ✅ Complete | Unit + Integration |
| Module 18 | Report Engine | ✅ Complete | Unit + Integration |
| Module 19 | Statistics Engine | ✅ Complete | Unit + Integration |
| Module 20 | Knowledge Engine | ✅ Complete | Unit + Integration |
| Module 21 | Export Engine | ✅ Complete | Unit + Integration |
| Module 22 | Visualization Engine | ✅ Complete | Unit + Integration |
| Module 23 | Admin Portal | ✅ Complete | Unit + Integration |
| Module 24 | AI Engine | ✅ Complete | Unit + Integration |
| Module 25 | SDK & Public API | ✅ Complete | Unit + Integration |
| Module 26 | Monitoring & Deployment | ✅ Complete | Unit + Integration |
| Module 27 | Production Readiness | ✅ Complete | Unit + Integration |

## Dataset Import Framework

| Component | Location | Status |
|---|---|---|
| Framework | `apps/api/services/dataset_import/` | ✅ Complete |
| Source Adapter Base | `apps/api/services/dataset_import/adapter_base.py` | ✅ Complete |
| Schema Mapper | `apps/api/services/dataset_import/schema_mapper.py` | ✅ Complete |
| Validator | `apps/api/services/dataset_import/validator.py` | ✅ Complete |
| Normalizer | `apps/api/services/dataset_import/normalizer.py` | ✅ Complete |
| Deduplicator | `apps/api/services/dataset_import/deduplicator.py` | ✅ Complete |
| Quality Scorer | `apps/api/services/dataset_import/quality_scorer.py` | ✅ Complete |
| Exporter | `apps/api/services/dataset_import/exporter.py` | ✅ Complete |
| Excel Adapter | `apps/api/services/dataset_import/adapters/excel_adapter.py` | ✅ Complete |
| Cohort Excel Adapter | `apps/api/services/dataset_import/adapters/cohort_excel_adapter.py` | ✅ Complete |
| Architecture Docs | `docs/dataset_import/ARCHITECTURE.md` | ✅ Complete |
| Tests | `tests/unit/dataset_import/` | ✅ 22 passing, 9 skipped |

## First Dataset Import

| Metric | Value |
|---|---|
| Dataset ID | ASTRO-RS-COHORT-v1.0.0 |
| Source | Cohort source file (49,964 imported) |
| Records imported | 49,964 |
| Quality score | 1.00 (Tier A) |
| Output (canonical, Research Data Office — Stable) | `research-data/research/cohort/ASTRO-RS-COHORT-v1.0.0/` |
| Validation report | `ASTRO-RS-COHORT-v1.0.0_import_validation_report.json` |

> **2026-07-17 reconciliation:** Engineering originally imported this dataset to `datasets/rs/cohort/ASTRO-RS-COHORT-v0.1.0/` (Candidacy). Research Data Office reviewed and promoted it to Stable v1.0.0 under their own path — see `research-data/STATUS.md`/`INDEX.md`. Content is byte-identical between both copies; the Engineering copy is kept as a historical artifact, not deleted, but is no longer the canonical reference.

## Test Suites

| Suite | Location | Tests | Status |
|---|---|---|---|
| Unit Tests | `tests/unit/` | ~1450 | ✅ All passing |
| Integration Tests | `tests/integration/` | ~80 | ✅ All passing |
| Dataset Import Tests | `tests/unit/dataset_import/` | 22 | ✅ All passing (9 skipped — xlsx path) |
| **Total** | — | **1559** | **0 failed, 1529 passed, 17 skipped** |

**Last clean run:** July 2026, pytest 9.1.1, pytest-asyncio 1.4.0, Python 3.13.5

## Test Infrastructure

| Component | Location | Status |
|---|---|---|
| Root conftest | `tests/conftest.py` | ✅ One engine, one session lifecycle |
| Integration conftest | `tests/integration/conftest.py` | ✅ Uses root `test_engine` |
| Unit conftest | `tests/unit/conftest.py` | ✅ Domain object factories only |
| pytest config | `apps/api/pytest.ini` | ✅ `asyncio_mode = auto` |
| pyproject config | `pyproject.toml` | ✅ `asyncio_default_fixture_loop_scope = session` |

## Database

| Component | Connection | Status |
|---|---|---|
| Test DB | `postgresql+asyncpg://astroos_test@localhost:5432/astroos_test_db` | ✅ Available |
| ENUM types | 7 custom types (rashi, graha, nakshatra_name, chart_type, ayanamsa_system, dignity_type, dasha_type) | ✅ Created in `_ensure_enums()` |
| Schema lifecycle | `test_engine` fixture | ✅ `create_all` / `drop_all` at session boundaries |

---

*Last updated: 2026-07-16*
