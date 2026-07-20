# Research Data Privacy Tools — AstroOS v2.3.0

## Overview

Tools for managing research data privacy on a single-user local-first platform.
Replaces the broader "GDPR Compliance" task from the original Phase III plan —
consent management is not applicable to a single-user research tool.

## Features

### 1. Export All My Data
```bash
# Export all research data as a portable archive
astroos data export --output ./astroos-data-export-2026-07-20.zip
```

The export includes:
- Chart computation records (D1, divisional)
- Research project metadata and snapshots
- Experiment configurations and results
- Query logs (if research mode was enabled)

### 2. Delete All Data
```bash
# Delete all research data from the local database
astroos data delete --confirm
```

Caveats:
- Data is deleted from PostgreSQL only. If you have previous exports/snapshots,
  those files remain on disk — delete them manually if needed.
- Running data is cached in `~/.astroos/cache/` - run `astroos data clean-cache`
  to clear cached computation results.

### 3. Anonymization for Research Publishing

When publishing research findings, you may want to anonymize chart data:

```bash
# Anonymize a research project export
astroos data anonymize --project <id> --output ./anonymized-export.json
```

This replaces:
- Birth names with "Subject-001", "Subject-002", etc.
- Exact birth times with time ranges (e.g., "10:00-11:00")
- Geographic coordinates with region-level data (e.g., "North India")
- Preserves all astrological calculations and yoga detections

## Privacy Principles

1. **Local by default** — All data stays on your machine. No cloud sync.
2. **Export before delete** — Always export before deleting data.
3. **Anonymize for sharing** — Use anonymization before publishing research.
4. **No telemetry** — The app never phones home.
