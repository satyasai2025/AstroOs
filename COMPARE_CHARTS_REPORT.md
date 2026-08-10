# Compare Charts Page: Implementation Report

**Scope:** `/charts/compare` — side-by-side comparison of 2-4 saved charts (planets, houses, dasha, yogas, summary), with JSON/CSV/PDF export, shareable links, and locally saved comparison sets.
**Status:** Complete and browser-verified against 4 real saved charts.
**Date:** 2026-08-10

---

## 1. What Was Built

### Page shell (`apps/web/src/app/charts/compare/page.tsx`)

- Fetches the signed-in user's saved charts (`useMyCharts`), opens a picker modal, and runs comparisons sequentially through `/workflow/analyze` — sequential rather than `Promise.all` to stay under that endpoint's 6/minute rate limit, with already-fetched results cached per chart (`resultCache`) so re-opening a saved comparison or re-running doesn't re-hit the API.
- Consumes shareable links (`?ids=a,b,c,d`): validates the IDs belong to the signed-in account before running the comparison, since saved charts are per-user and cross-account sharing isn't meaningful.
- Handles the empty state (`<2` saved charts), loading, and 429 rate-limit errors with distinct messages.

### Chart picker (`components/CompareChartsModal.tsx`)

Checkbox list of the user's saved charts, enforces 2-4 selection (disables further checkboxes at 4, disables Compare below 2), Cancel resets selection state.

### Comparison workspace (`components/ComparisonWorkspace.tsx`)

Five tabs, all driven by real computed chart data (no placeholder/mock content):
- **Planets** — rashi/house/degree/retrograde per planet per chart, with a Match column (`DifferenceHighlight.tsx`: exact / same-lord "similar" / different).
- **Houses** — sign + occupants per house (1-12) per chart, same Match logic.
- **Dasha** — current mahadasha/antardasha and % elapsed per chart, computed from real `dasha.mahadashas` windows.
- **Yogas** — union of all yoga names present in any compared chart, ✓/— grid per chart.
- **Summary** — % of planets sharing the same rashi across all charts; **Life Domain Scores** (Career/Relationship/Wealth/Overall Strength/Health Risk) reusing the same heuristic scoring from `lib/kpiScoring.ts` already used on the dashboard's Prediction Chains, explicitly labeled as heuristic rather than classical-formula output; a **Venn diagram** (`VennDiagram.tsx`) of planetary sign overlap between the first and last compared chart (2-set only, noted in UI when >2 charts); an N-axis **radar chart** (`EnhancedRadarChart.tsx`) plotting all compared charts' scores together.

Header actions: **Save** (names and persists the current comparison), **Share** (copies a `?ids=` link to clipboard, falls back to `window.prompt` if clipboard access fails), **Export JSON/CSV/PDF**.

### Exporters

- `JsonExporter.tsx` / `CsvExporter.tsx` — snapshot the full comparison (planets, houses, dasha, yogas, life domain scores) to a downloadable file.
- `PdfExporter.tsx` — opens a print-friendly report in a new tab for the browser's native print-to-PDF, rather than pretending to generate a PDF directly — no PDF library is installed in this project, so this is the honest working approach.

### Saved comparisons (`hooks/useSavedComparisons.ts`)

`localStorage`-backed (`astroos_saved_comparisons`): save, delete, pin/unpin. Listed on the main page below the picker; "Open" re-runs the comparison for that saved set (using the result cache when possible).

## 2. Verification

Browser-tested end-to-end via the in-app preview, signed in as a real account, against 4 real saved charts ("chennai modal test", "Rajesh", "Mumbai Test", "Test Import Two"):

- Picker modal: selection, 4-chart cap, Compare enabling at 2+.
- All 5 workspace tabs loaded real per-chart data with no console errors: Planets (Match column correctly flagged all 9 planets "✗ Different" across 4 unrelated charts), Houses (correctly flagged one house "≈ Similar" — same rashi lord, different sign), Dasha (real mahadasha/antardasha + % elapsed per chart), Yogas (real ✓/— grid), Summary (0% same-rashi banner consistent with the Planets tab, Life Domain Scores, Venn diagram, radar chart all rendered).
- Save → Back → reappears in Saved Comparisons list → Open → reloads identical data. Test entry deleted after verification.
- Export buttons (JSON/CSV/PDF) were not clicked (would trigger a file download, which needs separate confirmation) — verified by reading `CsvExporter.tsx`/`JsonExporter.tsx`/`PdfExporter.tsx` source instead.

**Environment note:** initial verification attempt hit `ERR_CONNECTION_REFUSED`/CORS errors on login — caused by the dev web server auto-assigning port 50374 (default 3000 was occupied by another session), which isn't in the API's CORS allowlist. Restarted on the project's pre-configured `web-cors-port` (3001) fixed it; not an app bug.

## 3. Discrepancy with `TEST_PLAN_CompareCharts.md`

That test plan (untracked, local-only) describes an earlier/aspirational design — exactly-2-chart side-by-side layout, an "AI Summary" tab with a similarity-score badge and narrative recommendations, and a "Saved" tab inside the workspace. The actual shipped implementation differs: 2-4 charts, no narrative AI summary (replaced by the real heuristic Life Domain Scores + Venn + radar), and Saved Comparisons lives on the main page rather than as a workspace tab. The shipped design is what's documented here; the test plan's TC-01–TC-20 checklist does not match current behavior and shouldn't be used as-is for future QA.

## 4. Files

- `apps/web/src/app/charts/compare/page.tsx`
- `apps/web/src/app/charts/compare/components/CompareChartsModal.tsx`
- `apps/web/src/app/charts/compare/components/ComparisonWorkspace.tsx`
- `apps/web/src/app/charts/compare/components/DifferenceHighlight.tsx`
- `apps/web/src/app/charts/compare/components/VennDiagram.tsx`
- `apps/web/src/app/charts/compare/components/EnhancedRadarChart.tsx`
- `apps/web/src/app/charts/compare/components/CsvExporter.tsx`
- `apps/web/src/app/charts/compare/components/JsonExporter.tsx`
- `apps/web/src/app/charts/compare/components/PdfExporter.tsx`
- `apps/web/src/app/charts/compare/hooks/useSavedComparisons.ts`

Commit: `6fb01fc` on `feat/ai-settings-and-fixes` (already on `origin`).
