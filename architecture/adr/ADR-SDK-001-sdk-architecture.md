# ADR-SDK-001: AstroOS SDK Architecture

**Status:** Accepted
**Date:** 2026-07-18 (implementation complete)
**Owner:** Engineering CAO
**Phase:** G — SDK (Complete)

## Context

AstroOS Phase E delivered a functional backend API with versioning metadata in `SdkService`. The `sdks/` directory contains stubs for Python and TypeScript packages, but they lack:
- Client libraries with typed methods
- Authentication helpers
- Retry/timeout configuration
- Error handling aligned with the `ApiResponse` envelope
- Offline caching or data models

Phase G requires production-ready SDKs for Python and TypeScript that external integrators can use to consume AstroOS APIs without hand-rolling HTTP clients.

## Decision

Adopt a **Thin SDK Architecture** with three components:

```
┌───────────────────────────────────────────────────┐
│            Client Application                      │
├───────────────────────────────────────────────────┤
│      AstroOS SDK (typed wrapper)                   │
│  - Endpoint methods                                 │
│  - Auth session management                          │
│  - Retry + timeout policy                           │
│  - Response envelope unmarshalling                  │
├───────────────────────────────────────────────────┤
│            AstroOS REST API                        │
│  (existing FastAPI backend with /api/v1/*)         │
└───────────────────────────────────────────────────┘
```

### Key Decisions

1. **Python SDK:** Package name `astroos-sdk`, distributed on PyPI. Uses `httpx` for async HTTP, `pydantic` for data models. Includes sync and async client classes.

2. **TypeScript SDK:** Package name `@astroos/sdk`, distributed on npm. Uses `fetch` with `AbortController` for timeouts, `zod` for runtime schema validation. ESM + CJS dual build.

3. **Authentication:** SDKs accept API key or JWT. Store credentials in environment variables or OS keychain. Refresh token rotation handled transparently.

4. **Error Model:** All API errors raise typed exceptions (`AstroOSAuthError`, `AstroOSValidationError`, `AstroOSRateLimitError`) with `request_id` for support tracing.

5. **Retry Policy:** Exponential backoff with jitter for 429/5xx. Configurable max retries and backoff base. No retry on 4xx (except 429).

6. **Versioning:** SDKs target `ApiVersion.v1` exclusively in this phase. Future API versions will require SDK major version bumps.

## Consequences

### Positive
- Integrators can install SDK via standard package managers
- Typed methods reduce integration errors and improve IDE autocomplete
- Centralized retry/timeout logic reduces bug surface
- Request IDs propagate through exceptions, simplifying support

### Negative
- Two SDK codebases to maintain (Python + TypeScript)
- SDK release cadence must track API changes
- Additional CI/CD pipelines for PyPI and npm publishing

### Neutral
- SDK does not include offline caching (by design); caching is a future enhancement
- Webhook payload schemas are not part of SDK scope (future Phase I)

## Interface Contracts

### Python SDK

```python
from astroos_sdk import AstroOSClient, AstroOSAuthError, AstroOSRateLimitError

client = AstroOSClient(base_url="https://api.astroos.example.com", api_key="...")

# Typed request/response
chart = await client.horoscope.create_birth_chart(BirthChartRequest(...))
report = await client.report.generate(chart_id=chart.id, format=ReportFormat.PDF)

# Pagination helper
async for batch in client.datasets.list_gc_master(limit=100):
    process(batch)
```

### TypeScript SDK

```typescript
import { AstroOSClient, AstroOSAuthError } from "@astroos/sdk";

const client = new AstroOSClient({ baseURL: "https://api.astroos.example.com", apiKey: "..." });

const chart = await client.horoscope.createBirthChart(birthChartRequest);
const report = await client.report.generate({ chartId: chart.id, format: "pdf" });
```

### Shared Envelope

All SDK responses map to:

```json
{
  "success": true,
  "data": { ... },
  "pagination": { "page": 1, "limit": 100, "total": 500 },
  "version": "v1",
  "request_id": "req_abc123"
}
```

## Implementation Status

✅ **Complete** — 2026-07-18

| Component | Status |
|-----------|--------|
| Python SDK Client | ✅ Complete |
| Python SDK Models | ✅ Complete |
| Python SDK Exceptions | ✅ Complete |
| TypeScript SDK Client | ✅ Complete |
| TypeScript SDK Schemas | ✅ Complete |
| SDK Tests | ✅ Complete |
| SDK Documentation | ✅ Complete |

---
*Author: Chief Solutions Architect, 2026-07-18*