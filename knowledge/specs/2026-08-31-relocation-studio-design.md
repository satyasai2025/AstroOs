# Relocation Studio — Frontend Preview UI Design

Date: 2026-08-31
Status: Approved (design review)
Scope: One feature — a frontend page that runs the relocation engine and
displays the four relocation technique fixtures (09-12) through the live API.

## Problem

The relocation technique fixtures (paran_crossings, sun_angular,
midpoints_to_angles, harmonic_interpretation) are backend-only
TechniqueDefinitions. Nothing in `apps/web` renders them, so users cannot see
the calculations working. Without a UI the calculations are effectively
invisible and unverifiable.

## Goals

- Provide a research-section page where a user supplies birth data + target
  location and sees relocation technique results rendered.
- Keep computation server-side (Swiss Ephemeris + RelocationEngine).
- Reuse the existing technique framework (TechniqueResolver + TechniqueEngine)
  and the existing frontend API client / research page patterns.

## Non-Goals

- No client-side ephemeris computation.
- No changes to the technique framework or the relocation engine's fact
  schema (the fixtures 09-12 are already committed and tested).
- No geo-coding autocomplete (user supplies lat/lon directly, or via presets).

## Architecture

Three parts, following existing conventions:

### 1. Backend: new router `apps/api/routers/relocation.py`

- `POST /api/v1/relocation/analyze`, protected by the same `_authenticated`
  dependencies used by the technique router (see `apps/api/main.py:427`).
- Request body: `birth_utc`, `birth_lat`, `birth_lon`, `target_lat`,
  `target_lon`, optional `ayanamsa`, `house_system`.
- Handler flow:
  1. `RelocationEngine(...).compute_facts(birth_utc, birth_lat, birth_lon,
     target_lat, target_lon)` → `list[Fact]`.
  2. Build `FactRegistry` from the facts (same pattern as
     `apps/api/routers/technique.py:_facts_from_dict`).
  3. Resolve the four relocation techniques by id via
     `TechniqueResolver().resolve_by_id(...)` —
     `paran_crossings`, `sun_angular`, `midpoints_to_angles`,
     `harmonic_interpretation` (their objectives differ, so resolve by id
     rather than objective).
  4. `TechniqueEngine().execute(tech, facts)` for each resolved technique.
- Response schema (`RelocationAnalyzeResponse`):
  - `birth` / `target` coordinates echoed.
  - `angles`: Asc/MC label + sign + harmonic family.
  - `techniques`: list of technique evaluations, each with technique_id,
    name, confidence, confidence_basis, is_matched, and triggers (rule_id,
    rule_name, role, status, matched/failed/missing, explanation).
  - `facts`: the raw relocation fact keys the page needs (midpoint counts,
    paran data) — minimal, explicit subset, not the whole registry.
- Register in `apps/api/main.py`: `app.include_router(
  relocation_router.router, prefix="/api/v1", dependencies=_authenticated )`.

### 2. Frontend: page + studio component

- New route: `apps/web/src/app/research/relocation/page.tsx` (server
  component with metadata), rendering `<RelocationStudio />` inside a
  `max-w-7xl` container — mirrors `research/synastry/page.tsx`.
- New component: `apps/web/src/components/research/RelocationStudio.tsx`
  ("use client").
  - Form: birth datetime, birth lat/lon, target lat/lon, ayanamsa (default
    lahiri), house system (default P).
  - Preset buttons pre-fill the form: the Provo test case used by the unit
    tests plus two well-known example charts. Presets fill the form; user can
    edit and run.
  - Submit via `api.post("/v1/relocation/analyze", body)` (existing client,
    `apps/web/src/lib/api.ts`).
  - Renders: location header (Asc/MC labels + harmonic family), and one card
    per technique with triggered/not-triggered/insufficient-data rules,
    confidence, and explanation text.
  - Loading + error states.
- Nav entry: add `/research/relocation` item to the Research module in
  `apps/web/src/config/navConfig.ts` (icon + viewId following neighbours).

### 3. Tests

- Backend: `apps/api/tests/unit/test_relocation_router.py` — happy path with
  the Provo preset returns 200, echoes coordinates, includes all four
  technique ids, and at least one trigger is present. Auth-gated check.
- Frontend: rely on existing Playwright e2e config for a smoke test of the
  page render + form submit; extend `apps/web/e2e` if a suitable spec file
  exists.

## Data Flow

```
User → RelocationStudio form → api.post("/v1/relocation/analyze")
  → relocation router → RelocationEngine.compute_facts → FactRegistry
  → TechniqueResolver + TechniqueEngine (4 techniques)
  → JSON response → RelocationStudio renders cards
```

## Error Handling

- Backend: 422 on malformed request (FastAPI defaults); explicit ValueError
  from the engine mapped to 400.
- Frontend: error banner with the API error message; loading spinner during
  the request; empty/insufficient-data techniques shown with their rule
  statuses rather than silently dropped.

## Testing / Verification

- `.venv/bin/python -m pytest apps/api/tests/unit/test_relocation_router.py -q`
- Full relocation suite still green:
  `.venv/bin/python -m pytest apps/api/tests/unit/test_relocation_techniques.py apps/api/tests/unit/test_relocation_engine.py -q`
- Frontend: `pnpm --dir apps/web typecheck`, `next lint` on the new files.
- Manual preview: start API + web, visit `/research/relocation`, run the
  Provo preset, confirm all four cards render with sensible triggers.

## Open Questions / Risks

- Relocation router needs Swiss Ephemeris data files at runtime; same
  dependency as the existing engine tests — no new risk.
- The Research nav is gated behind `SHOW_BETA_FEATURES`; the new item should
  follow whatever flag neighbouring items use so it appears alongside them.
