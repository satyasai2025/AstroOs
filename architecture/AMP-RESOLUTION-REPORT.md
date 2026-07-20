# AMP Resolution Report

**Date:** 2026-07-19
**Authority:** Architecture Office (CAO), AstroOS v2.1.0 "Vistara"
**Scope:** All 8 open Architecture Maintenance Proposals (AMP-001 through AMP-008) in `architecture/decisions/`.

## Governance Basis

Decisions follow the local-first mandate in `CLAUDE_START_HERE.md` and `ASTROOS_PHASE_I_V2_1_ROADMAP.md`: AstroOS is a local-first, single-user platform (native PostgreSQL, FastAPI + Next.js local, Redis optional). Docker/Kubernetes/Helm/cloud/multi-region are out of scope; the 34 frozen Enterprise Architecture Library documents describing such infrastructure are historical/future references. Consequently:

- Corrections requiring superseding ADRs against frozen, out-of-scope enterprise documents are **rejected/deferred** — the governance cost is disproportionate for documents not in the active development path.
- Corrections to tracking files (STATUS.md) or runtime documentation (docstrings) that improve local-first clarity without touching business logic are **accepted and applied**.

## Resolutions

| AMP | Title | Decision | Documents updated |
|---|---|---|---|
| AMP-001 | Disaster Recovery tenant-tier forward reference | **ACCEPTED — Option C (defer as tracked gap)** | AMP file only |
| AMP-002 | STATUS.md stale contradictory note | **ACCEPTED — applied** | STATUS.md, AMP file |
| AMP-003 | Disaster Recovery "fourth" vs "fifth" ordinal | **REJECTED (deferred)** | AMP file only |
| AMP-004 | Semantic Search / Knowledge Graph ordinal drift | **REJECTED (deferred)** | AMP file only |
| AMP-005 | Digital Twin cardinal/ordinal phrasing | **REJECTED** | AMP file only |
| AMP-006 | Ambiguous "Category" field / phase | **ACCEPTED — Option B applied; Option A rejected** | STATUS.md, AMP file |
| AMP-007 | Completion Report "four proposals" count | **REJECTED** | AMP file only |
| AMP-008 | Ontology Registry dependency model | **ACCEPTED — A: Option A1; B: Option B2** | apps/api/domain/ontology.py (docstring), AMP file |

## AMP-009/010 — Applied (Phase III, 2026-07-20)

| AMP | Title | Decision | Fix applied |
|---|---|---|---|
| AMP-009 | `/report/chart/pdf` and `/report/chart/csv` call `.model_dump()` on plain dataclass | **FIXED** — ChartReport dataclass converted to ChartReportResponse Pydantic model before `.model_dump()` | `apps/api/routers/report.py` |
| AMP-010 | `templates/reports/` directory missing | **FIXED** — Template path corrected to `apps/api/templates/reports/`; 7 template files created (base.html + horoscope, marriage, career, health, wealth, spiritual, transit) | `apps/api/services/report_template_engine.py`, `apps/api/templates/reports/*` |

## Rationale Per AMP

### AMP-001 — ACCEPTED (Option C: defer as tracked gap)
Disaster Recovery (ADR-EAL-029) and Multi Tenancy (ADR-EAL-021) are unimplemented enterprise documents covering multi-tenant/multi-region concerns explicitly outside the local-first scope. No runtime behavior depends on the forward reference. Recorded as an implementation-phase blocker: tenant tiering must exist before DR's tier-based RTO/RPO logic is built. Superseding ADRs (Options A/B) declined as disproportionate.

### AMP-002 — ACCEPTED (applied)
STATUS.md is a tracking file, not a frozen ADR; the stale parenthetical ("PLATFORM phase complete — 10/10. ENTERPRISE phase in progress.") directly contradicted the line above it. Deleted as routine maintenance.

### AMP-003 — REJECTED (deferred)
The one-word ordinal fix ("fourth" → "fifth") is sound but purely cosmetic, and Disaster Recovery is a frozen, out-of-scope document. A superseding ADR for a narrative tally is disproportionate. The AMP file stands as the permanent errata record; fold the fix in if ADR-EAL-029 is ever superseded substantively.

### AMP-004 — REJECTED (deferred)
Same disposition as AMP-003 for Semantic Search (ADR-EAL-031, "seventh" → "sixth") and Knowledge Graph (ADR-EAL-032, "eighth" → "seventh"). Two superseding ADRs for word-level cosmetic drift in frozen FUTURE-phase documents is unjustified. AMP file is the errata record.

### AMP-005 — REJECTED
The AMP itself confirms the numbers are arithmetically consistent — this is a style preference, not an error. No superseding ADR against Digital Twin (ADR-EAL-030) is warranted.

### AMP-006 — ACCEPTED (Option B); Option A REJECTED
Option B applied: a "Phase" column (FOUNDATION / PLATFORM / ENTERPRISE / FUTURE, per ROADMAP.md) added to STATUS.md's Completed (Frozen) table — routine maintenance on a tracking file, fully resolving the reader-facing ambiguity. Option A (frontmatter edits to all 34 frozen documents) rejected: churn on frozen out-of-scope documents with no benefit beyond Option B.

### AMP-007 — REJECTED
The grouping (five distinct `designateMandatory()` proposals presented as four review items) is editorially defensible, as the AMP concedes, and COMPLETION_REPORT.md is frozen by its own terms. The literal count of five is recorded in the AMP resolution for anyone using the report as a checklist. All five proposals concern out-of-scope enterprise documents.

### AMP-008 — ACCEPTED (Decision A: Option A1; Decision B: Option B2)
- **Decision A (Module 12 ↔ Module 13):** Option A1. The Rule Engine's Facts-only vocabulary discipline (`domain/facts.py`, as built and tested) is authoritative; the stale "Module 13 consumes this" claim in `domain/ontology.py`'s docstring is retired. Docstring corrected (documentation-only, no business logic touched, no frozen ADR affected). Option B1 (FactBuilder translation) declined for v2.1.0 as speculative plumbing with no current rule requirement.
- **Decision B (Module 12 ↔ Module 24):** Option B2. The 21-name duplication in `ai_engine.py` is small, rarely-changing, and cross-verified by OntologyRegistry's tests (a drift tripwire). Replacing it would modify working business logic for low benefit. Risk formally **accepted, not overlooked**; Option A2 may be re-proposed via a separately-scoped Engineering Request if drift is observed.
- No Engineering Request required: A1's outcome was documentation-only (applied); B2's outcome is no change.

## Files Modified

- `architecture/decisions/AMP-001-disaster-recovery-tenant-tier-forward-reference.md` — status + resolution
- `architecture/decisions/AMP-002-status-stale-note.md` — status + resolution
- `architecture/decisions/AMP-003-disaster-recovery-ordinal-inconsistency.md` — status + resolution
- `architecture/decisions/AMP-004-semantic-search-ordinal-drift.md` — status + resolution
- `architecture/decisions/AMP-005-digital-twin-phrasing-inconsistency.md` — status + resolution
- `architecture/decisions/AMP-006-category-field-phase-ambiguity.md` — status + resolution
- `architecture/decisions/AMP-007-completion-report-proposal-count.md` — status + resolution
- `architecture/decisions/AMP-008-ontology-registry-dependency-model.md` — status + resolution
- `architecture/STATUS.md` — stale note deleted (AMP-002); Phase column added (AMP-006); AMP tracking paragraphs updated to reflect closure
- `apps/api/domain/ontology.py` — docstring corrected per AMP-008 Decision A (Option A1); no code/business logic changed

## Invariants Preserved

- No frozen Enterprise Architecture Library document (`architecture/enterprise/*.md`, ADR-EAL-001…034) was modified.
- COMPLETION_REPORT.md remains frozen and untouched.
- No business logic, API, or database schema was changed.
- All decisions are consistent with the local-first governance rules: nothing requiring K8s/Helm/cloud was accepted for implementation.
