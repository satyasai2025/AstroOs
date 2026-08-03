# Module 27 — Research Case Import (Phases 1–2): Implementation Report

**Scope:** Event-centric Research Case pipeline — 4-table data model, import
API, event-snapshot computation, frontend import UI.
**Status:** Phases 1–2 complete and verified against the live database.
Phase 3 (Pattern Discovery) and Phase 4 (bulk verification) not started.
**Date:** 2026-07-31

---

## 1. What Was Built

The event-centric research pipeline described in the Research Case System
implementation plan: life events are the primary data; each event gets
astrological snapshots (dasha, transits, yogas) computed at its date, enabling
"across N verified marriage events, X% showed Jupiter-Venus involvement"
style pattern discovery later.

### Phase 1 — Schema & Models

| File | State |
|---|---|
| `apps/api/models/research_case.py` | Pre-existing untracked file. **Fixed a real bug** — the backend enums were `class _X(str)` (not `enum.Enum`), so `SAEnum(_X, ...)` crashed at import with `TypeError: object of type 'type' has no len()`. Converted to `class _X(str, Enum)` and string-literal `server_default`s. |
| `apps/api/schemas/research_case.py` | Pre-existing untracked file. Extended with `to_domain()` converters and an explicit schema→backend event-type map (`"Job Change"` → `"job_change"`), plus `ResearchCaseSummarySchema` / `ResearchCaseListResponseSchema`. |
| `apps/api/domain/research_case.py` | **Created** — the schemas referenced it but it did not exist. Frozen dataclasses: `ResearchCase`, `PersonInfo`, `LifeEvent`, `EventSnapshot`, `Attachment`, plus import/feature/pattern DTOs. |
| `database/versions/0014_research_cases.py` | **Created** — `research_cases`, `life_events`, `event_snapshots`, `attachments` + 6 enum types. **Applied to the live DB** (was `0013`, now `0014`). |
| `database/env.py` | Research-case models wired in so Alembic autogenerate can see them. |
| `docs/research-case-schema.json` | **Created** — generated from `ResearchCaseBatchImportSchema.model_json_schema()`. |
| `examples/research_cases_sample.json` | **Created** — a 2-case sample file for the UI drop-zone. |

### Phase 2 — Import Pipeline

| File | State |
|---|---|
| `apps/api/services/research_validation.py` | Pre-existing untracked file. **Fixed 7 bugs** (see §2) — the validator crashed at runtime on every call. |
| `apps/api/services/import_service.py` | **Created** — `SnapshotComputer` + `ResearchCaseImportService`. |
| `apps/api/routers/research.py` | 4 endpoints added (see §3). |
| `apps/web/src/lib/types.ts` | Research-case TS types added (mirror of backend schemas). |
| `apps/web/src/lib/researchCases.ts` | **Created** — `researchCasesApi` client. |
| `apps/web/src/app/research/import/page.tsx` | **Created** — drag-and-drop JSON, validation preview, import results, imported-case list. |
| `apps/web/src/components/layout/AppShell.tsx`, `NavPanel.tsx` | "Case Import" nav link added. |

## 2. Bugs Found & Fixed

The untracked work carried latent bugs that had never been exercised (the
models/schemas/validator were never imported by anything until wired in here):

**Validator (`research_validation.py`) — 7 runtime bugs:**
1. Called `_valid_age_range()` but only `_valid_dob()` was defined → `NameError`.
2. Used `SourceConfidence` without importing it → `NameError`.
3. Referenced `person_bon_confidence` (typo) instead of the defined
   `person_birth_confidence` → `NameError`.
4. Loop variable was `event`, but the block used `e.` → `NameError`.
5. Read `e.event_type` — schema field is `type` → `AttributeError`.
6. Read `e.source_confidence` — schema field is `confidence` → `AttributeError`.
7. `seen_hashes = existing_hashes or set()` — an **empty set is falsy**, so the
   batch's shared hash set was discarded on every call and cross-case duplicate
   detection silently never fired. Fixed with an explicit `is not None` check.

**ORM (`models/research_case.py`):** the enum base bug described in §1.

**Import service (found during verification):** a case-level snapshot failure
originally called `session.rollback()`, which rolled back *earlier successful
cases in the same batch* — their reported success was a lie. Restructured to
compute snapshots **before** adding anything to the session (compute is pure,
no DB), so a failed case contributes nothing and never affects batch-mates.
Proven with a deliberately-invalid-timezone case.

## 3. API Endpoints

Added to the existing researcher-gated Research router (prefix `/api/v1/research`):

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/cases/import/schema` | JSON Schema for a batch import payload |
| `POST` | `/cases/validate` | Validate a batch without persisting |
| `POST` | `/cases/import` | Validate → snapshot-compute → persist (201) |
| `GET` | `/cases` | List imported cases (summary) |

## 4. Snapshot Computation Design

`SnapshotComputer` wraps the existing engines (HoroscopeEngine, DashaEngine,
TransitEngine, YogaEngine) — the same "compute once per case, reuse per event"
rule as `EventEngine`:

- **Once per case** (natal, date-invariant): D1 chart, dasha tree, active yogas.
- **Per event date** (date-dependent): active dasha chain via
  `find_active_dasha_chain()`, transit positions via `TransitEngine`.
- Snapshots are versioned and immutable (`snapshot_version = "1.0"`); a future
  algorithm change appends a new version rather than overwriting.

Verification against real ephemeris data: dasha correctly shifts per event date
(`rahu/rahu → rahu/mercury → rahu/saturn`), with 7 active yogas and 9 transit
features per event.

## 5. Verification Evidence (2026-07-31)

- Migration `0014` applied live; all 4 tables + 6 enums verified in Postgres.
- Full import end-to-end against the live DB: 1 case → 3 events → 3 snapshots
  persisted, read back, correct dasha/yoga/transit content. Test rows removed
  afterward (DB left pristine).
- Transaction isolation: a failing case in a batch does not roll back the
  successful case.
- All 4 endpoints present in the assembled app's OpenAPI (158 paths).
- Frontend typecheck (`tsc --noEmit`) passes clean.
- `docs/research-case-schema.json` generated; `examples/research_cases_sample.json`
  parses and validates (2/2 valid).
- **27 pytest tests added** in `apps/api/tests/research_case/` (self-contained,
  deliberately not depending on the shared `tests/conftest.py`, which is missing
  from the tree): 15 validator tests, 10 schema-conversion/SnapshotComputer
  tests (ephemeris-gated), 2 live-DB integration tests. All 27 pass.

## 6. Known Gaps / Next Steps

- **Async import job** (`/cases/import/status/{job_id}`) is **not** implemented —
  import is synchronous and returns full per-case results. A real async path
  needs the worker-pool/job machinery wired to a request-scoped session and was
  deliberately not faked.
- **Phase 3 — Pattern Discovery engine** (`pattern_discovery.py`,
  `GET /research/patterns/{event_type}`, `/research/patterns/compare`) — not
  started. The schemas/DTOs for features and patterns already exist in
  `apps/api/schemas/research_case.py` and `apps/api/domain/research_case.py`.
- **Phase 4** — bulk 50+ case verification not run.
