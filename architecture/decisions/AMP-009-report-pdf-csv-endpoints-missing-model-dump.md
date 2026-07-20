# AMP-009: `/report/chart/pdf` and `/report/chart/csv` call `.model_dump()` on a plain dataclass

**Severity:** High (both endpoints always 500)
**Status:** Proposed
**Discovered:** 2026-07-20, during Phase II.4 (Worker Pools & Batch Scaling) end-to-end testing
**Discovered by:** Phase II Orchestrator, while building `apps/api/services/batch_report_service.py`

## Defect

`apps/api/routers/report.py`, `generate_chart_pdf` (line ~293) and
`generate_chart_csv` (line ~326), both do:

```python
report = ReportEngine.build_chart_report(...)   # returns domain.report.ChartReport
pdf_bytes = ReportTemplateEngine.render_pdf(report.model_dump())
```

`ReportEngine.build_chart_report` returns `apps.api.domain.report.ChartReport`,
a plain `@dataclass(frozen=True)` (see `apps/api/domain/report.py`) — it has
no `.model_dump()` method. Every call to either endpoint raises:

```
AttributeError: 'ChartReport' object has no attribute 'model_dump'
```

The sibling JSON endpoint `POST /report/chart` does **not** have this bug —
it correctly converts the domain object via the router's own
`_metadata_response()` / `_sections_response()` helpers into the Pydantic
`ChartReportResponse` (which does have `.model_dump()`) before returning.
The PDF/CSV endpoints skip that conversion step entirely.

A second, related issue: even a correct `.model_dump()` on the *Pydantic*
response would not by itself satisfy `ReportTemplateEngine.render_csv`,
which reads `section["data"]` per section — the domain `ReportSection`
dataclass nests that under `section.content.data`. The router's
`_sections_response()` helper already flattens this correctly
(`data=dict(s.content.data)`); the PDF/CSV endpoints must use the same
flattening, not a raw dataclass or a naive dump.

## How this shipped

No test exercises either endpoint —
`grep -rl "report/chart/pdf\|report/chart/csv" tests/` returns nothing.
`PHASE_F_COMPLETION_REPORT.md` and `ASTROOS_V2_STATUS.md` mark "PDF Export"
and "CSV Export" complete based on the endpoint existing and manual/partial
verification, not an automated request through the full stack.

## Proposed fix (not applied by this AMP)

In `generate_chart_pdf` / `generate_chart_csv`, build the response the same
way `build_chart_report` (the JSON endpoint) already does — via
`_metadata_response(report.metadata)` / `_sections_response(report.sections)`
assembled into a `ChartReportResponse`, then `.model_dump()` that — before
passing to `ReportTemplateEngine`. Add regression tests for both endpoints
(currently absent) as part of the fix.

## Governance note

`apps/api/routers/report.py` is part of the frozen Phase F deliverable.
Per `CLAUDE_START_HERE.md` ("Do not modify completed modules unless
requested") this AMP proposes the fix without applying it. Phase II.4's
own new code (`apps/api/services/batch_report_service.py`) does **not**
call `report.model_dump()`; it implements the same flattening
`_sections_response()` performs, applied locally to avoid depending on a
router module from a service module (layering) and to avoid duplicating
the bug. This AMP tracks fixing the router itself under proper governance
approval.

---
*Filed: Phase II Orchestrator, 2026-07-20*
