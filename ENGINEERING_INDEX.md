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

## Module Inventory (27 Modules)

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
| AstroDatabank Adapter | `apps/api/services/dataset_import/adapters/astrodatabank_adapter.py` | ✅ Complete |
| Architecture Docs | `docs/dataset_import/ARCHITECTURE.md` | ✅ Complete |
| Tests | `tests/unit/dataset_import/` | ✅ 22 passing, 9 skipped |

## First Dataset Import

| Metric | Value |
|---|---|
| Dataset ID | ASTRO-RS-COHORT-v0.1.0 |
| Source | AstroDatabank.xlsx (57,466 records) |
| Records imported | 49,964 |
| Quality score | 1.00 (Tier A) |
| Output | `datasets/rs/cohort/ASTRO-RS-COHORT-v0.1.0/` |
| Validation report | `ASTRO-RS-COHORT-v0.1.0_import_validation_report.json` |

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
