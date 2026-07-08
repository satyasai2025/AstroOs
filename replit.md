# AstroOS — Vedic Astrology Research Platform

A production-grade Vedic Astrology Research Platform for scholars, practitioners, and researchers. Built on Swiss Ephemeris with full divisional chart (D1–D60) support, Vimshottari Dasha, Ashtakavarga, and Yoga detection.

## Run & Operate

| Command | Purpose |
|---------|---------|
| `cd apps/api && python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload` | FastAPI backend (dev) |
| `cd apps/web && pnpm dev` | Next.js frontend (dev) |
| `alembic -c database/alembic.ini upgrade head` | Run DB migrations |
| `alembic -c database/alembic.ini revision --autogenerate -m "description"` | Generate migration |
| `python apps/api/security/generate_keys.py` | (Re)generate RSA key pair |
| `pytest -c apps/api/pytest.ini` | Run test suite |
| `pnpm run typecheck` | TypeScript typecheck (all packages) |

## Stack

**Frontend**: Next.js 15 (App Router), React 19, TypeScript, TailwindCSS, TanStack Query

**Backend**: FastAPI, Python 3.11, SQLAlchemy (async), Alembic

**Database**: PostgreSQL (async via asyncpg)

**Cache**: Redis (JWT denylist + ephemeris result cache)

**Auth**: RS256 JWT (asymmetric), bcrypt password hashing

**Astrology Engine**: Swiss Ephemeris (pyswisseph) — Module 2

**Charts**: D3.js, Cytoscape.js — Module 10

**Testing**: pytest + pytest-asyncio, Vitest

## Repository Map

```
apps/
  api/              — FastAPI backend (Python)
    config.py       — All settings via env vars (Pydantic Settings)
    main.py         — App factory + router registration
    dependencies.py — DI: DB session, Redis, auth guard
    domain/         — Pure Python domain models (no framework)
    models/         — SQLAlchemy ORM models
    schemas/        — Pydantic request/response schemas
    repositories/   — DB access layer (converts ORM ↔ domain)
    services/       — Business logic (no ORM/HTTP)
    routers/        — HTTP handlers (no business logic)
    security/       — JWT (RS256), bcrypt, RSA key pair
  web/              — Next.js frontend
    src/app/        — App Router pages
    src/lib/        — API client, auth hooks, types
    src/components/ — React components

packages/
  shared/           — Shared Python enums and constants (Vedic astrology)
  ephemeris/        — Swiss Ephemeris wrapper (Module 2)

database/
  alembic.ini       — Alembic config
  env.py            — Alembic migration environment
  versions/         — Versioned migrations (0001_initial_schema, …)

tests/
  conftest.py       — pytest fixtures (mock DB, mock Redis)
  unit/             — Unit tests (services, domain)
  integration/      — Integration tests (require live DB)
  e2e/              — End-to-end tests

docs/
  architecture.md   — Full architecture reference
```

## Architecture Decisions

- **Clean Architecture**: Domain → Repository → Service → Router. Each layer imports only inward.
- **Async-first**: SQLAlchemy async engine (asyncpg), FastAPI async routes throughout.
- **RS256 JWT**: Asymmetric keys allow public-key-only verification in future microservices.
- **Soft deletes**: All tables carry `deleted_at TIMESTAMPTZ NULL`; hard deletes are never used.
- **DB-managed timestamps**: `updated_at` is set by a PostgreSQL trigger, never by application code.
- **UUID PKs**: `gen_random_uuid()` — no serial integers; prevents enumeration attacks.
- **Constant-time auth**: Login checks password even when email doesn't exist (prevents timing oracle).

## Module Build Order

| Module | Status | Domain |
|--------|--------|--------|
| 1 — Foundation | ✅ Complete | Auth, Users, JWT, DB bootstrap |
| 2 — Chart Engine | ⬜ Next | Swiss Ephemeris wrapper, birth chart computation |
| 3 — Graha Module | ⬜ | Planetary positions, dignities, aspects |
| 4 — Nakshatra Module | ⬜ | Lunar mansions, pada, ruling planet |
| 5 — Dasha Module | ⬜ | Vimshottari, Yogini, Chara systems |
| 6 — Divisional Charts | ⬜ | D1–D60 varga computation |
| 7 — Ashtakavarga | ⬜ | Bindu calculation, Sarvashtakavarga |
| 8 — Yoga Module | ⬜ | Raj Yoga, Dhana Yoga, pattern detection |
| 9 — Research Tools | ⬜ | Search, comparison, statistical analysis |
| 10 — Visualization | ⬜ | D3.js charts, Cytoscape.js |

## Required Environment Variables

| Variable | Source | Notes |
|----------|--------|-------|
| `DATABASE_URL` | Runtime-managed (Replit) | PostgreSQL connection string |
| `REDIS_URL` | Set manually | Default: `redis://localhost:6379/0` |
| `JWT_PRIVATE_KEY_PATH` | Default in config | `apps/api/security/keys/private.pem` |
| `JWT_PUBLIC_KEY_PATH` | Default in config | `apps/api/security/keys/public.pem` |

## Gotchas

- RSA keys are gitignored. Run `python apps/api/security/generate_keys.py` after cloning.
- Run migrations before starting the API: `alembic -c database/alembic.ini upgrade head`
- Use `PYTHONPATH=.` when running Python scripts from the workspace root.
- Next.js rewrites `/api/*` → FastAPI backend. Both must be running for full functionality.
- `asyncpg` requires `postgresql+asyncpg://` URL; Alembic needs `postgresql://`. `dependencies.py` auto-converts.

## User Preferences

- No placeholder code — every module is production-complete before the next starts.
- No simplified architecture — follow Clean Architecture + DDD strictly.
- Wait for explicit instruction before starting the next module.
