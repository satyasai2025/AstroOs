# Prediction Chain Explorer: Implementation Report

**Scope:** `PredictionChainExplorer` — a per-life-area visual chain (house → lord → karaka strength → varga position → current Dasha relevance → final index) explaining the real computed inputs behind AstroOS's synthesized KPI indices.
**Status:** Complete, committed, pushed.
**Date:** 2026-08-10

---

## 1. What Was Built

### Component (`apps/web/src/components/charts/PredictionChainExplorer.tsx`)

- Four-tab selector (Marriage / Career / Wealth / Health). Each tab renders a vertical chain of cards connected by arrows, ending in a highlighted result card showing the corresponding KPI value.
- `buildChain(area, result)` assembles the chain per area from data already computed elsewhere in the app (`kpiScoring.ts`), rather than inventing new fields:
  - **Marriage**: 7th House → 7th lord strength → Venus (spouse karaka) → Jupiter (marital happiness karaka) → Navamsa (D9) placement of Venus → current Dasha relevance → `marriageIndex()`.
  - **Career**: 10th House → 10th lord strength → matched career yogas → Dasamsha (D10) placement of the 10th lord → current Dasha relevance → `careerIndex()`.
  - **Wealth**: 2nd House + 11th House lord strengths → Jupiter (fortune karaka) → Hora (D2) placement of the 2nd lord → current Dasha relevance → `wealthPotential()`.
  - **Health**: 6th House (disease/injury) + 1st House (Ascendant/body) lord strengths → Trimshamsha (D30) placement of the 6th lord → current Dasha relevance → `healthRisk()`.
- Each varga (divisional chart) is the classically correct one per life area — D9 for marriage, D10 for career, D2 for wealth, D30 for health — rather than defaulting to D9 everywhere.
- Strength badges (`strengthBadge()`) color-code each node Strong (≥6.5), Moderate (≥4), or Weak, with "No data" as an explicit fallback.
- The Dasha node cross-checks the current Mahadasha/Antardasha lords against the planets relevant to that chain and flags whether the active period is actually "activating" that life area.
- Every node traces back to a real field already consumed by `kpiScoring.ts` — nothing is fabricated for this view, which is the deliberate scope decision over building a generic Knowledge-Graph-style ontology (the Karakatva database backing that approach is still too sparse to be meaningful).

### Integration points

- Rendered on the chart detail page (`apps/web/src/app/(main)/charts/page.tsx`).
- Rendered inline in the Knowledge Graph viewer (`apps/web/src/app/(main)/knowledge-graph/page.tsx`) as the concrete, chart-specific counterpart to that page's abstract prediction-dependency graphs.

## 2. Verification

Code-reviewed against `kpiScoring.ts` to confirm each chain node maps 1:1 to a field the corresponding index function (`marriageIndex`, `careerIndex`, `wealthPotential`, `healthRisk`) actually reads — no invented nodes. Visual verification (tab switching, badge coloring, varga fallback text when a divisional chart isn't computed) was previously done in-browser during initial development; not re-verified in this documentation pass.

## 3. Not Done / Out of Scope

- No generic ontology-style Knowledge Graph (would require a materially more populated Karakatva database).
- No editable/interactive chain (read-only visualization of already-computed values).

## 4. Files

- `apps/web/src/components/charts/PredictionChainExplorer.tsx` (main component)
- Consumes: `apps/web/src/lib/kpiScoring.ts`, `apps/web/src/lib/astro.ts` (`PLANET_SYMBOLS`)
- Used by: `apps/web/src/app/(main)/charts/page.tsx`, `apps/web/src/app/(main)/knowledge-graph/page.tsx`

Commit: `d8f3308` ("chore: commit admin panel and related infrastructure"), pushed to `origin/feat/ai-settings-and-fixes`.
