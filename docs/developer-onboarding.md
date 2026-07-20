# Developer Onboarding Guide

> **Audience:** New developers joining the AstroOS project.
> **Target:** Productive, local-first development environment in under 30 minutes.

---

## First-Day Setup Checklist

- [ ] Git clone and install (see [README.md](../README.md))
- [ ] PostgreSQL running and database created
- [ ] `.env` file configured
- [ ] RSA keys generated
- [ ] Database migrations applied
- [ ] API starts and health check passes
- [ ] Frontend starts and loads in browser
- [ ] Test suite runs green
- [ ] Pre-commit hooks installed (see [pre-commit-setup.md](pre-commit-setup.md))

---

## Local Dev Environment Walkthrough

### 1. Clone & Install

```bash
git clone <repo-url> astroos
cd astroos

# Python dependencies
pip install -r apps/api/requirements.txt

# Node dependencies (from repo root)
pnpm install
```

### 2. Database

Create a PostgreSQL database (see README section 2 for SQL). Then verify:

```bash
psql -U astroos_user -d astroos_db -c "SELECT 1;"
```

### 3. Environment

```bash
cp .env.example .env   # or create from scratch (see README section 4)
# Edit .env: ensure DATABASE_URL matches your local PostgreSQL
```

### 4. RSA Keys (one-time)

```bash
PYTHONPATH=. python apps/api/security/generate_keys.py
```

### 5. Migrations

```bash
PYTHONPATH=. alembic -c database/alembic.ini upgrade head
```

### 6. Start Everything

```bash
# API + frontend (hot reload)
./scripts/dev.sh

# Or individually:
PYTHONPATH=. uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
# In another terminal:
cd apps/web && pnpm dev
```

Verify: `curl http://localhost:8000/api/healthz` returns `{"status": "ok", ...}`.

---

## Project Architecture

```
routers/   →  services/   →  repositories/   →  models/   (ORM)
  ↑              ↑                ↑
HTTP thin     business         DB access
              logic
```

Rules of thumb:
- **Routers contain zero business logic.** They validate input, call a service, return a response.
- **Services contain business rules.** They never import HTTP concepts (Request, Response, status codes).
- **Repositories handle SQLAlchemy.** They translate between ORM models and domain objects.
- **Domain models** (`apps/api/domain/`) are pure Python dataclasses with zero framework imports.
- **Schemas** (`apps/api/schemas/`) are Pydantic models for request/response serialization. They are the API contract.
- **Shared constants/enums** live in `packages/shared/` — importable by any engine or test.

---

## How to Run Tests

### Unit Tests (fast, no database)

```bash
PYTHONPATH=. pytest tests/unit/ -v
```

Run a single test file:

```bash
PYTHONPATH=. pytest tests/unit/test_dasha_engine.py -v
```

Run tests matching a keyword:

```bash
PYTHONPATH=. pytest tests/unit/ -k "shadbala" -v
```

### Full Suite with Coverage

```bash
PYTHONPATH=. pytest tests/ --cov=apps --cov=packages --cov-report=term-missing
```

### Integration Tests (require live PostgreSQL)

```bash
PYTHONPATH=. pytest tests/integration/ -m integration -v
```

### Precision Tests (require Swiss Ephemeris .se1 files)

```bash
PYTHONPATH=. pytest tests/precision/ -v
```

### Test Conventions

- **New engine/service code must include unit tests.** Aim for 100% coverage on new modules.
- **Integration tests** go in `tests/integration/` and are marked `@pytest.mark.integration`. They require a live database and (optionally) real `.se1` ephemeris files.
- **Fixtures** live in `tests/conftest.py`. Common patterns: `sample_birth_data`, `mock_ephemeris_wrapper`, `db_session`.
- **The test suite must stay green.** No PR may reduce the passing count.

---

## How to Add a New Endpoint

### 1. Define the schema

In `apps/api/schemas/`:

```python
# apps/api/schemas/example.py
from pydantic import BaseModel, Field

class ExampleRequest(BaseModel):
    """Request schema for the example endpoint."""
    name: str = Field(..., description="The name to greet")

class ExampleResponse(BaseModel):
    """Response schema for the example endpoint."""
    greeting: str = Field(..., description="The greeting message")
```

### 2. Implement the service

In `apps/api/services/`:

```python
# apps/api/services/example_service.py
from dataclasses import dataclass

@dataclass
class ExampleService:
    """Pure business logic — no HTTP imports."""

    def generate_greeting(self, name: str) -> str:
        return f"Hello, {name}!"
```

### 3. Create the router

In `apps/api/routers/`:

```python
# apps/api/routers/example.py
from fastapi import APIRouter, Depends

from apps.api.schemas.example import ExampleRequest, ExampleResponse
from apps.api.services.example_service import ExampleService
from apps.api.dependencies import get_db_session

router = APIRouter(prefix="/example", tags=["example"])
service = ExampleService()

@router.post("/greet", response_model=ExampleResponse)
async def greet(body: ExampleRequest):
    greeting = service.generate_greeting(body.name)
    return ExampleResponse(greeting=greeting)
```

### 4. Register the router

In `apps/api/main.py`:

```python
from apps.api.routers import example

app.include_router(
    example.router,
    prefix="/api/v1",
    dependencies=[Depends(require_authenticated)]  # or require_admin, etc.
)
```

### 5. Write tests

```python
# tests/unit/test_example_endpoint.py
async def test_example_service():
    service = ExampleService()
    result = service.generate_greeting("World")
    assert result == "Hello, World!"
```

### Checklist

- [ ] Schema defined with `Field(description=...)` for OpenAPI docs
- [ ] Service is pure Python (no FastAPI/HTTP imports)
- [ ] Router is thin (no business logic)
- [ ] Router registered in `main.py` with appropriate auth dependency
- [ ] Unit tests cover the service
- [ ] Integration test covers the full request/response (if applicable)
- [ ] API reference in `docs/api-reference.md` updated

---

## How to Add a New Yoga

### 1. Create the yoga evaluator

In `apps/api/services/yogas/`:

```python
# apps/api/services/yogas/my_new_yoga.py
from apps.api.domain.yoga import YogaDefinition, YogaResult
from apps.api.services.yoga_registry import register_yoga
from apps.api.services.yoga_predicates import houses_from, house_of_lord

@register_yoga(
    yoga_id="BPHS-OMY-008",
    name="My New Yoga",
    category="solar",
    description="Description of the yoga",
    rule_version="1.0",
    requires=("D1", "HouseEngine"),
)
async def evaluate_my_new_yoga(ctx) -> YogaResult | None:
    # Business logic here
    conditions = []
    satisfied = []
    missing = []

    # ... check conditions, populate satisfied/missing ...

    return YogaResult(
        yoga_id="BPHS-OMY-008",
        name="My New Yoga",
        rule_version="1.0",
        is_present=len(missing) == 0,
        satisfied=satisfied,
        missing=missing,
        trace=[],
    )
```

### 2. Ensure the module is imported

In `apps/api/services/yogas/__init__.py`, the new module is auto-discovered
via the package's import chain. No manual registration needed — the
`@register_yoga` decorator handles it.

### 3. Add tests

```python
# tests/unit/yogas/test_my_new_yoga.py
async def test_my_new_yoga_detected():
    # Build a YogaContext with the required planetary positions
    # Call evaluate_my_new_yoga(ctx)
    # Assert is_present=True for matching configurations
    pass

async def test_my_new_yoga_not_detected():
    # Assert is_present=False for non-matching configurations
    pass
```

### Checklist

- [ ] `@register_yoga` decorator applied with stable `yoga_id`
- [ ] `rule_version` starts at `"1.0"` (bumped when evaluator logic changes)
- [ ] `requires` tuple lists all dependencies
- [ ] Results include `satisfied`/`missing`/`trace` for full auditability
- [ ] Unit tests for both "detected" and "not detected" scenarios
- [ ] No predictive language in results (descriptive only)

---

## Code Review Checklist

### General

- [ ] Does the code follow Clean Architecture (routers → services → repositories → models)?
- [ ] Are there no framework imports in domain models?
- [ ] Are there no business logic imports in routers?
- [ ] Are all public functions and classes typed with Python type hints?
- [ ] Do Pydantic schemas have `Field(description=...)` on non-obvious fields?
- [ ] Are new features covered by unit tests?
- [ ] Do all existing tests still pass?

### Backend (Python)

- [ ] Async-first: all routes are `async def`, DB calls use async SQLAlchemy
- [ ] Soft deletes: new tables carry `deleted_at TIMESTAMPTZ NULL`
- [ ] UUID primary keys (`gen_random_uuid()`), not serial IDs
- [ ] New constants/enums added to `packages/shared/` for cross-module reuse
- [ ] Docstrings on all public classes and methods (Google-style)
- [ ] No bare `except:` — catch specific exceptions

### Frontend (TypeScript)

- [ ] TypeScript strict mode — no `any`, no `// @ts-ignore`
- [ ] `pnpm lint` and `pnpm typecheck` pass
- [ ] No inline styles — use TailwindCSS utility classes
- [ ] API calls go through the SDK client, not raw `fetch`

### Database

- [ ] Schema changes have an Alembic migration in `database/versions/`
- [ ] `updated_at` is set by DB trigger, not application code
- [ ] New reference/seed data is a migration, not a manual script

### Documentation

- [ ] README updated if setup steps, prerequisites, or project structure changed
- [ ] API reference (`docs/api-reference.md`) updated for new endpoints
- [ ] Architecture doc (`docs/architecture.md`) updated for new modules
- [ ] `CLAUDE_START_HERE.md` updated if project-level facts changed

---

## Debugging Tips

### The API won't start

```bash
# Read the first traceback line — startup errors are explicit:
# - "DATABASE_URL: field required" → missing .env
# - "No such file or directory: 'private.pem'" → missing RSA keys
# - "connection refused" → PostgreSQL not running

# Run in foreground for visible logs:
PYTHONPATH=. uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Tests fail

```bash
# Run with verbose output to see the first failure:
PYTHONPATH=. pytest tests/unit/ -v --tb=short

# Run with full traceback:
PYTHONPATH=. pytest tests/unit/ -v --tb=long

# Run a single failing test:
PYTHONPATH=. pytest tests/unit/test_something.py::test_name -v --tb=long
```

### Alembic migration issues

```bash
# Check current revision:
PYTHONPATH=. alembic -c database/alembic.ini current

# View migration history:
PYTHONPATH=. alembic -c database/alembic.ini history

# Re-run migrations from scratch (destroys data):
PYTHONPATH=. alembic -c database/alembic.ini downgrade base
PYTHONPATH=. alembic -c database/alembic.ini upgrade head
```

### Swiss Ephemeris returns wrong values

```bash
# Check mode — Moshier fallback is ~1 arc-minute less accurate:
curl http://localhost:8000/api/healthz | python -m json.tool
# Look for "mode": "swiss" vs "mode": "moshier"

# Ensure .se1 files are in data/ephemeris/:
ls -la data/ephemeris/
# Should contain sepl_18.se1 and seas_18.se1
```

### API returns 401/403 unexpectedly

```bash
# Check the token:
# Decode the JWT payload (public part only):
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null || echo "Invalid token"

# Regenerate tokens:
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","password":"changeme123"}'
```

### Memory or performance issues

```bash
# Check the worker pool sizes — default may be too high for your machine:
# Reduce in .env:
WORKER_POOL_CPU_SIZE=1
WORKER_POOL_IO_SIZE=2
WORKER_POOL_AI_SIZE=0   # Disable AI pool

# Profile a single request:
PYTHONPATH=. python -m cProfile -o profile.out apps/api/main.py
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start API | `PYTHONPATH=. uvicorn apps.api.main:app --reload` |
| Start frontend | `cd apps/web && pnpm dev` |
| Start both | `./scripts/dev.sh` |
| Run all tests | `PYTHONPATH=. pytest tests/ -v` |
| Run unit tests | `PYTHONPATH=. pytest tests/unit/ -v` |
| Run with coverage | `PYTHONPATH=. pytest tests/ --cov=apps --cov=packages` |
| Run migrations | `PYTHONPATH=. alembic -c database/alembic.ini upgrade head` |
| Create migration | `PYTHONPATH=. alembic -c database/alembic.ini revision --autogenerate -m "description"` |
| Lint Python | `ruff check apps/` |
| Format Python | `ruff format apps/` |
| Lint TypeScript | `cd apps/web && pnpm lint` |
| TypeCheck | `cd apps/web && pnpm typecheck` |
| Generate RSA keys | `PYTHONPATH=. python apps/api/security/generate_keys.py` |

---

## See Also

- [README.md](../README.md) — local setup
- [docs/api-reference.md](api-reference.md) — API endpoint catalogue
- [docs/architecture.md](architecture.md) — full architecture reference
- [docs/contributing.md](contributing.md) — contribution guidelines
- [docs/pre-commit-setup.md](pre-commit-setup.md) — pre-commit hooks
- [docs/troubleshooting.md](troubleshooting.md) — common fixes
