# Action Plan for Atlas — Governance Compliance Remediation

**Based on Governance_Audit_Phases_FGH.md findings**  
**Status:** ❌ Phases F, G, H cannot be frozen until these actions are complete

---

## 🔴 CRITICAL (Must fix before freeze consideration)

### Phase H - Production Implementation

1. **Integrate monitoring routes in `apps/api/main.py`**
   - Add import: `from apps.api.monitoring import setup_monitoring_routes`
   - Add call before `return app`: `setup_monitoring_routes(app)`
   - Without this, `/metrics`, `/health/live`, `/health/ready` endpoints do not exist

---

## 🟡 HIGH PRIORITY (Required for completeness)

### Phase F - Reports

2. **Create missing `dasha.html` template**
   - File: `templates/reports/dasha.html`
   - Pattern: Follow existing templates (marriage.html, career.html)

3. **Create unit tests**
   - File: `tests/unit/test_report_template_engine.py`
   - Test methods: `render_html`, `render_pdf`, `render_csv`, `list_templates`

### Phase G - SDK

4. **Fix empty SDK directory**
   - Either: Create `sdks/python/astroos/api/__init__.py` with `_ReportAPI` class
   - Or: Remove empty `sdks/python/astroos/api/` and `sdks/python/astroos/models/` directories

5. **Add TypeScript Zod schemas**
   - Create: `sdks/typescript/astroos/schemas/chart.ts`
   - Add: Zod schema for `ChartReportRequest`, `ChartReportResponse`

6. **Add SDK documentation**
   - File: `docs/sdk/quickstart-python.md`
   - File: `docs/sdk/quickstart-typescript.md`

---

## 🟢 MEDIUM PRIORITY (Governance prerequisites)

### All Phases - Governance

7. **Update ADR status to "Accepted"**
   - Edit: `architecture/adr/ADR-REPORT-001-reporting-architecture.md` — change status
   - Edit: `architecture/adr/ADR-SDK-001-sdk-architecture.md` — change status
   - Edit: `architecture/adr/ADR-PRODUCTION-001-production-architecture.md` — change status

8. **Create completion reports**
   - File: `PHASE_F_COMPLETION_REPORT.md`
   - File: `PHASE_G_COMPLETION_REPORT.md`
   - File: `PHASE_H_COMPLETION_REPORT.md`

9. **Update STATUS.md**
   - File: `ASTROOS_V2_STATUS.md`
   - Change Phases F, G, H from "🔴 Not started" to "✅ Complete"

---

## Verification Commands

After fixes, run to verify:

```bash
# Test ReportTemplateEngine
pytest tests/test_sdk.py -v

# Verify monitoring routes exist
curl http://localhost:8000/metrics
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

---

## Upon Completion

Submit for follow-up governance audit. All phases can then be reconsidered for freeze.