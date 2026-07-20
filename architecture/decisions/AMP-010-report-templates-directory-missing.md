# AMP-010: `templates/reports/` directory referenced by ReportTemplateEngine does not exist

**Severity:** High (PDF/HTML report rendering unconditionally fails; CSV unaffected)
**Status:** Proposed
**Discovered:** 2026-07-20, during Phase II.4 (Worker Pools & Batch Scaling) end-to-end testing, immediately after AMP-009
**Discovered by:** Phase II Orchestrator

## Defect

`apps/api/services/report_template_engine.py`:

```python
_TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "templates", "reports"
)
_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), ...)
```

`__file__` is `apps/api/services/report_template_engine.py`; four `..`
levels up from `apps/api/services/` lands **above the repository root**,
at `<repo-parent>/templates/reports` — a directory that does not exist on
disk anywhere in this checkout (confirmed: no `horoscope.html`, `base.html`,
or any `templates/reports/*.html` file exists in the repository at all,
via repo-wide search).

Effect:
- `ReportTemplateEngine.render_html()` → `jinja2.TemplateNotFound: horoscope.html`,
  caught internally, falls back to `base.html`, which also doesn't exist →
  unhandled `TemplateNotFound: base.html` propagates to the caller.
- `ReportTemplateEngine.render_pdf()` (calls `render_html` first) always fails.
- `GET /report/templates` (`list_templates()`) degrades gracefully — it
  catches `FileNotFoundError` and returns `[]` — so this symptom alone
  (an always-empty template list) is easy to miss in casual testing.
- `ReportTemplateEngine.render_csv()` is **unaffected** — it builds CSV
  directly from the report dict without Jinja2/templates, and was verified
  working end-to-end in Phase II.4 testing (real Swiss Ephemeris chart →
  CSV, correct output).

## How this shipped

`PHASE_F_COMPLETION_REPORT.md` lists "Templates (7/8) ✅ Complete —
horoscope.html, marriage.html, career.html, health.html, wealth.html,
spiritual.html, transit.html" and "PDF Export ✅ Complete". No template
file matching that list exists in the repository, and (per AMP-009) no
test exercises the PDF/HTML rendering path end-to-end. The most likely
explanation is the templates were authored in a prior session/environment
and never committed, or were removed by a later cleanup without the
completion report being revised.

## Proposed fix (not applied by this AMP)

1. Correct `_TEMPLATES_DIR` to point at a path that actually exists inside
   the repository (e.g. `templates/reports/` at the repo root, or colocate
   under `apps/api/templates/reports/` — an Architecture decision, since it
   affects packaging/deployment paths).
2. Author or restore the 7 listed template files (or reduce the claimed
   count in `PHASE_F_COMPLETION_REPORT.md` to match reality).
3. Add regression tests that actually render a PDF end-to-end (would have
   caught this, and AMP-009, immediately).

## Governance note

`report_template_engine.py` and `templates/` are part of the frozen Phase F
deliverable — not modified by this AMP, per `CLAUDE_START_HERE.md`. Phase
II.4's batch job API (`apps/api/services/batch_report_service.py`) handles
this correctly without a code change: PDF-format batch subjects fail
individually with the captured error recorded per-subject in the batch's
`MANIFEST.txt`, while the rest of the batch and CSV-format batches are
unaffected — verified in testing (1 PDF subject → 0/1 succeeded, error
"base.html" in manifest; 2 CSV subjects → 2/2 succeeded). Until AMP-009 and
this AMP are resolved, **CSV is the only working batch export format**;
this is documented in `ASTROOS_V2_STATUS.md` and `PHASE_II_ORCHESTRATOR_LOG.md`.

---
*Filed: Phase II Orchestrator, 2026-07-20*
