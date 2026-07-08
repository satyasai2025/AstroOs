# AstroOS — Architecture Reference

## System Overview

AstroOS is a Vedic Astrology Research Platform built on Clean Architecture + Domain-Driven Design.

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser                                                        │
│  Next.js 15 (App Router) + TanStack Query + TailwindCSS        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS / JSON
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI (Python 3.11)                                          │
│  ├── Routers   (HTTP adapters — no business logic)              │
│  ├── Services  (Business rules — no ORM/HTTP)                   │
│  ├── Repos     (DB access — converts ORM ↔ Domain)             │
│  └── Domain    (Pure Python dataclasses — no dependencies)      │
└──────────┬──────────────────────────┬───────────────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐     ┌────────────────────────┐
│  PostgreSQL 16   │     │  Redis 7               │
│  (primary store) │     │  (JWT denylist + cache) │
└──────────────────┘     └────────────────────────┘
```

## Module Build Order

Modules are built sequentially. Each module is complete (domain → DB → API → frontend) before the next starts.

| # | Module | Domain |
|---|--------|--------|
| 1 | **Foundation** | Auth, Users, JWT, DB bootstrap |
| 2 | Chart Engine | Birth chart computation, Swiss Ephemeris |
| 3 | Graha Module | Planetary positions, dignities, aspects |
| 4 | Nakshatra Module | Lunar mansions, pada, ruling planet |
| 5 | Dasha Module | Vimshottari, Yogini, Chara systems |
| 6 | Divisional Charts | D1–D60 varga computation |
| 7 | Ashtakavarga | Bindu calculation, Sarvashtakavarga |
| 8 | Yoga Module | Raj Yoga, Dhana Yoga, pattern detection |
| 9 | Research Tools | Search, comparison, statistical analysis |
| 10 | Visualization | D3.js charts, Cytoscape.js relationship graphs |

## Dependency Rule

```
HTTP Routers
  └── Services (pure Python)
        └── Repositories (SQLAlchemy)
              └── Domain Models (dataclasses)
                    └── (no external dependencies)
```

The domain layer has zero framework imports.
Services know nothing about HTTP.
Repositories know nothing about HTTP or business rules.
Routers delegate everything; they contain zero business logic.

## Authentication Flow

```
Client → POST /api/v1/auth/login
       ← { access_token (30min, RS256), refresh_token (7d, RS256) }

Client → GET  /api/v1/auth/me   [Authorization: Bearer <access>]
Client → POST /api/v1/auth/refresh  { refresh_token }
       ← { new access_token, new refresh_token }   # rotation

Client → POST /api/v1/auth/logout
       # access JTI written to Redis denylist
       # DB session revoked
```

## Database Conventions

- All PKs: `UUID` (`gen_random_uuid()`) — no serial
- All timestamps: `TIMESTAMPTZ`
- Soft deletes: `deleted_at TIMESTAMPTZ NULL`
- `updated_at`: managed by DB trigger `set_updated_at()`
- Every schema change: Alembic migration in `database/versions/`
- Naming: `snake_case` tables, `ix_<table>_<column>` indexes

## Ephemeris Calculation Contract

- All calculations use Swiss Ephemeris (pyswisseph)
- Input: Julian Day Number (UTC) + geographic coordinates (WGS84)
- Ayanamsa system: configurable (default: Lahiri / Chitrapaksha)
- All results deterministic for the same input — cached in Redis
- Cache key: `sha256(julian_day + lat + lon + ayanamsa)`
- No floating-point mutation after return from ephemeris module
