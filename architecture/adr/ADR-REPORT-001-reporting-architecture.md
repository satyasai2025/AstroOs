# ADR-REPORT-001: AstroOS Reporting Architecture

**Status:** Accepted
**Date:** 2026-07-18 (implementation complete)
**Owner:** Engineering CAO
**Phase:** F — Reports (Complete)

## Context

AstroOS Phase E delivered a functional ReportEngine that assembles structured JSON reports from computed domain objects (D1Chart, Timeline, VerificationFindings, AggregateReport). The current API returns `ReportSection` lists with arbitrary `data` dicts.

Phase F requires professional horoscope reports (9 types: Horoscope, Dasha, Transit, Marriage, Career, Health, Wealth, Spiritual, Research) exportable as PDF/JSON/CSV. The existing infrastructure is JSON-only and template-less.

## Decision

Adopt a **Template-First Reporting Architecture** with three layers:

```
┌─────────────────────────────────────────────┐
│         Presentation Layer                  │
│  PDF Renderer · JSON Formatter · CSV Export │
├─────────────────────────────────────────────┤
│         Template Layer                      │
│  Jinja2 HTML templates (9 report types)     │
│  JSON schema templates                      │
│  CSV column templates                       │
├─────────────────────────────────────────────┤
│         Assembly Layer                      │
│  ReportEngine (existing)                    │
│  + ReportTemplateEngine (new)               │
└─────────────────────────────────────────────┘
```

### Key Decisions

1. **PDF Generation:** Use WeasyPrint (Python) for HTML→PDF conversion. It supports CSS print media, page breaks, headers/footers, and embedded fonts. Converts HTML templates to PDF without browser automation.

2. **Template Engine:** Jinja2 with custom filters for astrology terms (rashi names, nakshatra, yoga descriptions). Templates versioned in `templates/reports/`.

3. **Report Types as Plugins:** Each report type (Horoscope, Dasha, etc.) is a plugin class registered in a registry. This satisfies the Open/Closed Principle — adding a new report type doesn't modify core code.

4. **Export Format Strategy:** JSON remains canonical (fastest, most complete). PDF is rendered from the same data via HTML template. CSV is a flattened view of specific report sections.

## Consequences

### Positive
- Templates are maintainable by non-engineers (astrologers can edit Jinja2)
- Report types are independently testable
- PDF templates reuse frontend CSS vocabulary (cosmic-950, amber-500)
- JSON output remains the API default; PDF is an opt-in export

### Negative
- WeasyPrint introduces a new dependency (libffi, libpango, libcairo system packages required in Docker)
- HTML→PDF rendering is slower than native PDF generation (~300-800ms per report on typical hardware)
- Template versioning requires a migration strategy when report layouts change

### Neutral
- CSV export is limited to "flat" report sections (no nested structures)
- PDF fonts must be bundled or rely on system fonts (requires fontconfig in Docker)

## Interface Contracts

### New: `POST /report/chart/pdf` (StreamingResponse)
```
Request:  ChartReportRequest + {format: "pdf"|"json"}
Response: application/pdf (StreamingResponse)
```

### New: `POST /report/chart/csv` (StreamingResponse)
```
Request:  ChartReportRequest + {sections: string[]}
Response: text/csv (StreamingResponse)
```

## Implementation Status

✅ **Complete** — 2026-07-18

| Component | Status |
|-----------|--------|
| ReportTemplateEngine | ✅ Complete |
| PDF Export Endpoint | ✅ Complete |
| CSV Export Endpoint | ✅ Complete |
| Jinja2 Templates | ✅ Complete |
| WeasyPrint Dependency | ✅ Complete |

---
*Author: Chief Solutions Architect, 2026-07-18*