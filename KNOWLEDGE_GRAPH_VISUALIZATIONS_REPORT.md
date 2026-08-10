# Knowledge Graph Visualization Viewer: Implementation Report

**Scope:** Reusable in-place viewer (`/knowledge-graph`) for the 10 Knowledge Graph visualization cards — tabs, related-visualization navigation, and honest per-card Rules/Sources data provenance for the two prediction cards.
**Status:** 9 of 10 cards complete and browser-verified. Classical Rule Graph and four sidebar stubs remain external links / not built.
**Date:** 2026-08-10

---

## 1. What Was Built

### Viewer shell (`apps/web/src/app/knowledge-graph/page.tsx`)

- One persistent module — clicking a card swaps content in place (`VisualizationViewer`), never navigates away. Breadcrumb (`Knowledge Graph › Visualizations › [Title]`), `← Back`, tabs, Details panel, and Related Visualizations (clickable, same-page) are all wired to live state.
- Tabs adapt per card instead of showing fake tabs with nothing behind them:
  - All cards: **Graph**, **Explanation**.
  - `prediction-dependency` and `prediction-tree` additionally get **Rules** (real BPHS rule citations from `PredictionRelatedRules`) and **Sources** (real per-field data provenance from `PredictionDataSources`), both driven by the same computed `buildPredictionGraph` result so the graph, its citations, and its inputs can never drift apart.
- Filter tabs (All / Prediction Engine / Entity Relationships / Strength Analysis / Time Based / Research / Classical Knowledge), search, sort (Default/A→Z/Z→A), and Grid/List view are functional against the 10-card catalog (`GRAPH_CARDS`).

### Prediction Data Sources — humanized (`apps/web/src/components/charts/predictions/PredictionDataSources.tsx`)

Originally every source row displayed the raw API field path verbatim (`chart.planet_strengths[Saturn].is_exalted`, `yogas.results[BPHS-RY-001]`, `dasha.mahadashas`) — meaningless to a non-technical user and indistinguishable from noise. Fixed:

- `humanizeField()` translates known raw-path shapes into plain language: `Saturn — exalted (very strong placement)`, `Mars aspects Saturn`, `Yoga rule BPHS-RY-001`, `Mahadasha timeline`, `Saturn — directional strength (Shashtiamsas)`, `Saturn — Deeptadi avastha (brightness state)`.
- `isRawFieldPath()` detects API-shaped labels (`chart.`, `yogas.`, `shadbala/all.`, `avastha/all[...]`) vs hand-written labels (`"House & Sign Strength"`), so only genuine raw paths get rewritten.
- The raw path is not deleted — it's moved behind a **"Show technical details"** toggle at the end of each expanded row (after Status/Reason/What-was-checked/Used-By/Last-Updated/Impact), so a researcher can still get to it without it being the primary label everyone else sees.

### Avastha / Digbala data — wired up

`buildPredictionGraph(area, result, extras)` accepts `{ avastha, shadbalaAll }` to compute the Avastha (Planetary State) and Digbala (Directional Strength) factors. `apps/predictions/page.tsx` already fetched these via `useAvastha`/`useShadbalaAll`, but `knowledge-graph/page.tsx` never did — so those two factors always showed **Unavailable** in this viewer regardless of whether the data actually existed. Fixed by fetching the same two queries in `VisualizationViewer` and passing them through. Verified: Data Quality went from 92% (23/25, 2 unavailable) to 100% (27/27) on the same chart.

### Decorative legend chips → plain text

The Details panel's bottom row (`card.legend`, e.g. "House / Planet / Sign / Strength / Result") was rendered as `<span>` pills with `rounded-full` + `border` styling — visually identical to a clickable filter-chip pattern, but with no `onClick` and no relationship to what's actually filterable in the underlying graph (e.g. the real House Dependency Graph filters by relationship type — Lordship, Aspect, Argala — not by these labels). Building real cross-graph filtering to match would mean touching 7+ differently-shaped graph components. Instead, restyled to plain text (`Shows: House, Planet, Sign, Strength, Result`) so it no longer looks like a dead control.

## 2. Verification

Browser-tested end-to-end against a real chart ("chennai modal test", Career) via the in-app preview:
- Card gallery filters/search/sort/grid-list toggle.
- Prediction Dependency Graph: Graph tab shows the real computed chain (10th House → Saturn → strengths/aspects → yogas → dasha/transit → Career Strength 67/100); Rules tab lists real BPHS rule citations; Sources tab shows 100% data quality with all 27 rows in plain language and a working technical-details toggle.
- Backend dependency caught mid-session: the FastAPI server (port 8001) had stopped, producing `ERR_CONNECTION_REFUSED` on login and making the whole app look broken — restarted via `.claude/launch.json`'s `api` config, not a code bug.

## 3. Not Done (explicitly out of scope for this pass)

None of the following affect prediction computation — they're read-only browsing/reference UI on top of already-computed results.

| Item | Current state |
|---|---|
| **Classical Rule Graph** (card 10/10) | Still an external link to `/knowledge/bphs`; no inline rule-graph component built. |
| Entity Browser (sidebar) | Stub nav entry, "Soon" — no page. |
| Rule Explorer (sidebar) | Stub nav entry, "Soon" — no page. |
| Saved Graphs (sidebar) | Stub nav entry, "Soon" — no page. |
| Graph Compare (sidebar) | Stub nav entry, "Soon" — no page. |

## 4. Files Changed

- `apps/web/src/app/knowledge-graph/page.tsx` — Avastha/Digbala data wiring, legend chip restyle.
- `apps/web/src/components/charts/predictions/PredictionDataSources.tsx` — field-path humanization, technical-details toggle reordering.

Commit: `b1dc684` on `feat/ai-settings-and-fixes`.
