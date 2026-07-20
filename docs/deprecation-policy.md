# Deprecation Policy

> **Applies to:** AstroOS REST API (`/api/v1/*`), Python SDK (`astroos`),
> TypeScript SDK (`@astroos/sdk`).
>
> **Version:** 2.2.0

---

## API Versioning Strategy

AstroOS uses a single active API version at a time, denoted by the URL prefix:

- **Current:** `/api/v1/`
- **Future:** `/api/v2/` (when introduced)

### Principles

1. **Backward compatibility within a major version.** Adding new endpoints,
   request fields, or response fields is always backward compatible. Removing
   or renaming is not.
2. **Version is part of the URL path.** Content negotiation (Accept headers) is
   not used for versioning.
3. **One active version at a time.** When v2 is introduced, v1 enters a
   deprecation cycle with a minimum 6-month notice period. Overlapping support
   for two versions is temporary.
4. **The SDKs track the platform version.** Python `astroos` and TypeScript
   `@astroos/sdk` share the platform's major.minor version and are released in
   lockstep with the API.

---

## Deprecation Lifecycle

Every deprecation follows a three-phase lifecycle:

```
DEPRECATED ──(≥ 90d)──→ SUNSET ──(≥ 30d)──→ REMOVED
```

### Phase 1: Deprecated

**What happens:**
- The endpoint/field is documented as deprecated.
- A `Sunset` header is added to responses indicating the planned removal date.
- The deprecated feature continues to work exactly as before.
- SDK methods are marked with `@deprecated` (TypeScript TSDoc) or emit
  `DeprecationWarning` (Python).
- A migration path is documented (what to use instead).

**Signals:**

| Signal | Where |
|--------|-------|
| `Sunset: Sat, 1 Jan 2027 00:00:00 GMT` | HTTP response header |
| `"deprecated": true` | OpenAPI schema for the endpoint |
| `@deprecated use v2Method() instead` | TypeScript SDK |
| `DeprecationWarning: ...` | Python SDK |
| Deprecation notice | CHANGELOG, migration guide |

**Duration:** Minimum **90 calendar days** between DEPRECATED and SUNSET.

### Phase 2: Sunset

**What happens:**
- The endpoint/field is documented as sunset.
- The API returns a `410 Gone` status with a JSON body explaining the
  replacement.
- No functional code path remains — the old endpoint is a thin redirector.
- Sunset features remain in the OpenAPI schema but are marked with
  `"x-sunset": true`.
- SDK methods raise clear errors with migration instructions.

**Duration:** Minimum **30 calendar days** between SUNSET and REMOVED.

### Phase 3: Removed

**What happens:**
- The endpoint/field code is deleted from the API codebase.
- The OpenAPI schema no longer includes it.
- SDK methods are removed.
- Database columns (if any) are removed in an Alembic migration.

---

## Minimum Notice Periods

| Change Type | Notice Period | Example |
|-------------|--------------|---------|
| Endpoint removal | 90 days deprecated + 30 days sunset | `POST /api/v1/old-endpoint` → 410 → deleted |
| Request field removal | 90 days deprecated | `field` in request body |
| Response field removal | 90 days deprecated | `field` in response body |
| SDK method removal | 90 days deprecated + 30 days sunset | `client.oldMethod()` |
| SDK parameter removal | 90 days deprecated | `useNewParam` |
| Behavior change (breaking) | 180 days deprecated | Different default, different error codes |
| Database schema change | 180 days deprecated + migration guide | Column removal |

> Emergency security fixes may bypass these periods with an Architecture Office
> ADR and a clear migration path.

---

## How to Mark an Endpoint as Deprecated

### Step 1: Update the router

```python
# apps/api/routers/my_router.py
from fastapi import APIRouter, Response
from datetime import datetime, timezone

router = APIRouter(prefix="/v1", tags=["my"])

SUNSET_DATE = "Sat, 01 Jan 2027 00:00:00 GMT"

@router.get(
    "/old-endpoint",
    deprecated=True,  # ← shows in OpenAPI / Swagger UI
    description="[DEPRECATED] Use GET /api/v2/new-endpoint instead.",
)
async def old_endpoint(response: Response):
    # Set the Sunset header
    response.headers["Sunset"] = SUNSET_DATE
    response.headers["Deprecation"] = "true"

    # ... existing logic (unchanged) ...
    return {"result": "data"}
```

### Step 2: Update the OpenAPI schema description

```python
@router.get(
    "/old-endpoint",
    deprecated=True,
    summary="[DEPRECATED] Old endpoint — use /new-endpoint",
    description=(
        "**DEPRECATED** — will be removed after "
        + SUNSET_DATE
        + ". "
        "Use `GET /api/v2/new-endpoint` instead. "
        "See the migration guide at docs/migration-v2-to-v3.md for details."
    ),
)
```

### Step 3: Mark in the SDK

**Python SDK:**

```python
import warnings
from typing import Any

class AstroOSClient:
    def old_method(self, *args: Any, **kwargs: Any) -> Any:
        """[DEPRECATED] Use new_method() instead.

        Raises DeprecationWarning.
        """
        warnings.warn(
            "old_method() is deprecated. Use new_method() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.new_method(*args, **kwargs)
```

**TypeScript SDK:**

```typescript
export class AstroOSClient {
  /**
   * @deprecated Use `newMethod()` instead. Will be removed after 2027-01-01.
   */
  async oldMethod(...args: any[]): Promise<any> {
    console.warn("oldMethod() is deprecated. Use newMethod() instead.");
    return this.newMethod(...args);
  }
}
```

### Step 4: Add to OpenAPI `deprecated` fields

For **response fields** being deprecated, add to the schema:

```python
from pydantic import BaseModel, Field
import warnings

class OldResponse(BaseModel):
    new_field: str = Field(..., description="The replacement field")
    old_field: str = Field(
        ...,
        description="[DEPRECATED] Use new_field instead. Will be removed after 2027-01-01.",
        deprecated=True,  # Pydantic v2+ — shows in generated OpenAPI
    )
```

### Step 5: Document the deprecation

- Add an entry to `CHANGELOG.md` under a `### Deprecated` section.
- Update `docs/api-reference.md` noting which endpoints are deprecated.
- Reference the migration path in the deprecation notice.

---

## What Is NOT a Breaking Change

The following are **not** considered breaking and do not require a deprecation
cycle:

- Adding a new endpoint
- Adding an optional request field (with a documented default)
- Adding a response field (clients must ignore unknown fields)
- Changing the order of fields in a JSON response
- Performance improvements that don't change correctness
- Bug fixes that align behavior with documented API contract
- Adding new enum values (clients must handle unknown enum values gracefully)
- Extending an error's `detail` field with more information
- Changing internal (non-exported) SDK symbols

---

## Client Guidance

### How to prepare for deprecations

1. **Ignore unknown fields.** Always parse responses with a parser that
   discards or tolerates unknown keys (Pydantic, Zod, plain JSON.parse — all
   do this by default).
2. **Listen for `Sunset` headers.** If your integration monitors response
   headers, you can automate migration before a removal.
3. **Upgrade SDKs promptly.** The SDK is the fastest path to know what changed.
4. **Watch the CHANGELOG.** All deprecations are announced in the changelog
   with the planned removal date.

### Example: Checking for deprecation headers

```python
import httpx

response = httpx.get("http://localhost:8000/api/v1/old-endpoint")
if "deprecation" in response.headers:
    sunset = response.headers.get("sunset", "unknown")
    print(f"WARNING: This endpoint is deprecated. Sunset: {sunset}")
```

---

## Policy Exceptions

Exceptions to this policy require:

1. An Architecture Office ADR documenting the rationale.
2. A minimum 30-day notice period (reduced from 90) for security-critical
   changes.
3. A clear migration path documented before the change ships.

No exceptions are granted for breaking changes without notice except in cases
of active security vulnerability (CVE or equivalent).

---

## Related Documents

- [docs/api-reference.md](api-reference.md) — current API endpoint catalogue
- [docs/migration-v2.1-to-v2.2.md](migration-v2.1-to-v2.2.md) — migration guide
- [docs/sdk/VERSIONING.md](sdk/VERSIONING.md) — SDK versioning and stability
- [CHANGELOG.md](../CHANGELOG.md) — release history and deprecation notices
