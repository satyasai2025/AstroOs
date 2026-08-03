# AstroOS — Vedic Astrology Research Platform

> **v2.3.0 "Lakshmi"** (released) · **Local-First** — everything runs on your machine (native PostgreSQL, FastAPI, Next.js; Redis optional). Docker/Kubernetes/cloud are out of scope; see [CLAUDE_START_HERE.md](CLAUDE_START_HERE.md).

A production-grade Vedic Astrology Research Platform for scholars, practitioners, and researchers. Built on Swiss Ephemeris with full divisional chart support (D1–D60), six Dasha systems, and a clean REST API.

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Prerequisites](#prerequisites)
4. [Local Setup](#local-setup)
   - [1. Clone and install](#1-clone-and-install)
   - [2. PostgreSQL](#2-postgresql)
   - [3. Redis (optional)](#3-redis-optional)
   - [4. Environment variables](#4-environment-variables)
   - [5. RSA keys](#5-rsa-keys)
   - [6. Run migrations](#6-run-migrations)
   - [7. Start the API](#7-start-the-api)
   - [8. Start the frontend](#8-start-the-frontend)
5. [API Reference](#api-reference)
6. [Running Tests](#running-tests)
7. [Project Structure](#project-structure)
8. [Module Build Status](#module-build-status)
9. [Architecture Notes](#architecture-notes)

---

## Overview

AstroOS computes Vedic birth charts from geographic coordinates and UTC birth times using the Swiss Ephemeris library. It supports:

- **Birth chart (D1)** with Graha drishti aspects and dignity scoring
- **15 Divisional charts** (D2 Hora through D60 Shashtiamsha) per Parashara rules
- **6 Dasha systems**: Vimshottari, Yogini, Ashtottari, Kalachakra, Chara (Jaimini), Narayana (Jaimini)
- **6 Ayanamsa systems**: Lahiri, KP, Raman, Yukteshwar, Fagan-Bradley, True Chitra
- **4 House systems**: Whole Sign, Placidus, Koch, Equal
- Multi-level dasha sub-periods: Mahadasha → Antardasha → Pratyantar → Sookshma → Prana

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **API** | FastAPI 0.115, Python 3.11, Uvicorn |
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript, TailwindCSS |
| **Database** | PostgreSQL 15+ (async via asyncpg + SQLAlchemy 2.0) |
| **Cache / Auth** | Redis (JWT denylist) |
| **Auth** | RS256 JWT (asymmetric keys), bcrypt |
| **Astrology** | pyswisseph 20230604 (Swiss Ephemeris) |
| **ORM / Migrations** | SQLAlchemy async, Alembic |
| **Testing** | pytest, pytest-asyncio |
| **Package manager** | pip (API) · pnpm (frontend) |

---

## Prerequisites

Install the following before proceeding:

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | `python3 --version` |
| pip | latest | `pip install --upgrade pip` |
| Node.js | 20+ | `node --version` |
| pnpm | 9+ | `npm install -g pnpm` |
| PostgreSQL | 15+ | Running locally (native install) |
| Redis | 7+ | Optional — auth denylist gracefully disabled if absent |
| Git | any | `git --version` |

---

## Local Setup

### 1. Clone and install

```bash
git clone <your-repo-url> astroos
cd astroos
```

Create and activate a Python virtual environment (keeps AstroOS's pinned
dependency versions isolated from other projects / your system Python):

```bash
python3 -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows (PowerShell/cmd)
.venv\Scripts\activate
```

Install Python dependencies:

```bash
pip install -r apps/api/requirements.txt
```

Install Node dependencies (from the workspace root):

```bash
pnpm install
```

---

### 2. PostgreSQL

Create a database and user (via `psql` against a local/native PostgreSQL install):

```sql
-- Run as postgres superuser
CREATE USER astroos_user WITH PASSWORD 'astroos_pass';
CREATE DATABASE astroos_db OWNER astroos_user;
GRANT ALL PRIVILEGES ON DATABASE astroos_db TO astroos_user;
```

---

### 3. Redis (optional)

Redis is only used for JWT token revocation (logout). The API runs without it — logout will be a no-op if Redis is unavailable.

```bash
# macOS
brew install redis && brew services start redis

# Ubuntu/Debian
sudo apt install redis-server && sudo systemctl start redis

# Docker
docker run -d --name astroos-redis -p 6379:6379 redis:7
```

---

### 4. Environment variables

Create a `.env` file in the project root:

```bash
# .env — never commit this file
DATABASE_URL=postgresql+asyncpg://astroos_user:astroos_pass@localhost:5432/astroos_db
REDIS_URL=redis://localhost:6379/0

# Optional overrides (defaults shown)
APP_NAME="AstroOS API"
APP_VERSION="2.2.0"
ENVIRONMENT=development
DEBUG=true
EPHEMERIS_PATH=data/ephemeris
JWT_PRIVATE_KEY_PATH=apps/api/security/keys/private.pem
JWT_PUBLIC_KEY_PATH=apps/api/security/keys/public.pem
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=["http://localhost:3000"]
```

> **Note:** The API reads these via `python-dotenv` / Pydantic Settings. You can also export them as shell variables.

---

### 5. RSA keys

Generate the RS256 key pair used for JWT signing (one-time setup):

```bash
PYTHONPATH=. python apps/api/security/generate_keys.py
```

This creates:
```
apps/api/security/keys/private.pem   ← keep secret, never commit
apps/api/security/keys/public.pem    ← safe to distribute
```

> Both files are gitignored. Re-run this command after a fresh clone.

---

### 6. Run migrations

Apply all database migrations before starting the API:

```bash
PYTHONPATH=. alembic -c database/alembic.ini upgrade head
```

Verify:

```bash
PYTHONPATH=. alembic -c database/alembic.ini current
# Expected output: <revision_id> (head)
```

---

### 7. Start the API

```bash
PYTHONPATH=. uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API is now available at:

| URL | Description |
|-----|-------------|
| `http://localhost:8000/api/healthz` | Health check |
| `http://localhost:8000/api/docs` | Swagger UI (debug mode only) |
| `http://localhost:8000/api/redoc` | ReDoc (debug mode only) |
| `http://localhost:8000/api/openapi.json` | OpenAPI schema |

Quick health check:

```bash
curl http://localhost:8000/api/healthz
```

```json
{
  "status": "ok",
  "version": "2.2.0",
  "environment": "development",
  "ephemeris": { "mode": "moshier", "official_data": false }
}
```

---

### 8. Start the frontend

```bash
cd apps/web
pnpm dev
```

The frontend runs at `http://localhost:3000`. API calls are proxied via Next.js rewrites (`/api/*` → `http://localhost:8000`).

> Both the API and frontend must be running for full functionality.

---

### One-command dev environment

Instead of steps 7–8, you can start both with hot reload via:

```bash
./scripts/dev.sh          # API (:8000) + frontend (:3000)
./scripts/dev.sh --api    # API only
./scripts/dev.sh --web    # frontend only
```

The script is portable bash (Linux, macOS, and Windows Git Bash), auto-detects the Python interpreter, and generates the RSA keys if missing.

If setup fails at any step, see [docs/troubleshooting.md](docs/troubleshooting.md).

---

## API Reference

> Curated overview below. For the full endpoint catalogue with examples see
> [docs/api-reference.md](docs/api-reference.md) and the interactive Swagger UI at
> `http://localhost:8000/api/docs` (available when `DEBUG=true`).

All endpoints are prefixed with `/api/v1`.

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login, receive access + refresh tokens |
| `POST` | `/auth/refresh` | Rotate tokens using refresh token |
| `POST` | `/auth/logout` | Revoke tokens (requires Redis) |

### Horoscope — Birth Chart (D1)

```bash
POST /api/v1/horoscope/d1
Content-Type: application/json

{
  "birth_datetime_utc": "1986-06-15T10:30:00+00:00",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "ayanamsa": "lahiri",
  "house_system": "W"
}
```

### Divisional Charts (D2–D60)

```bash
# Single varga
POST /api/v1/divisional/{varga}
# e.g. /api/v1/divisional/D9

# All 15 vargas in one call
POST /api/v1/divisional/all
```

Supported vargas: `D2`, `D3`, `D4`, `D7`, `D9`, `D10`, `D12`, `D16`, `D20`, `D24`, `D27`, `D30`, `D40`, `D45`, `D60`

### Dasha Systems

```bash
POST /api/v1/dasha/{system}
# system = vimshottari | yogini | ashtottari | kalachakra | chara | narayana
```

Request body:

```json
{
  "birth_datetime_utc": "1986-06-15T10:30:00+00:00",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "ayanamsa": "lahiri",
  "house_system": "W",
  "max_depth": 3
}
```

`max_depth`: `1` = Mahadasha only · `2` = + Antardasha · `3` = + Pratyantar · `4` = + Sookshma · `5` = + Prana

| System | Cycle | Basis |
|--------|-------|-------|
| `vimshottari` | 120 yr | Moon nakshatra |
| `yogini` | 36 yr | Moon nakshatra |
| `ashtottari` | 108 yr | Moon nakshatra |
| `kalachakra` | 100 yr | Moon Navamsha (D9) sign |
| `chara` | variable | Jaimini, D1 sign lords |
| `narayana` | variable | Jaimini, D9 sign lords |

---

## Running Tests

```bash
# All unit tests (no database required)
PYTHONPATH=. pytest tests/unit/ -v

# Full suite with coverage
PYTHONPATH=. pytest tests/ -v --cov=apps --cov=packages --cov-report=term-missing

# Single module
PYTHONPATH=. pytest tests/unit/test_dasha_engine.py -v
```

Current status: `apps/api/tests/unit/` and `apps/api/tests/research_case/`
collect and pass (run with `PYTHONPATH=apps/api`). The shared
`tests/conftest.py` (providing `require_test_db`, `minimal_chart`,
`natal_snapshot`, `test_engine`, and `db_session` fixtures) had gone missing
from the tree — silently breaking collection of the whole `apps/api/tests/`
suite — and has been restored from git history, along with the DB-free
`tests/precision/conftest.py`. A few tests that had drifted from refactored
APIs (`AdminEngine`'s repo-only constructor, `EntityLinker`'s registry-based
lookup) were updated to match. DB-backed tests still skip without
`TEST_DATABASE_URL` set. See `docs/module-27-research-case-import-report.md`
for the full list of what broke and why.

Also working: **27 tests in `apps/api/tests/research_case/`** (15 validator
unit tests + 10 schema-conversion/`SnapshotComputer` tests, ephemeris-gated +
2 live-DB integration tests) — all passing. Module 27 (Research Case Import)
is verified end-to-end against a live PostgreSQL.

---

## Project Structure

```
.
├── apps/
│   ├── api/                      FastAPI backend
│   │   ├── config.py             Settings (Pydantic Settings, env vars)
│   │   ├── main.py               App factory + router registration
│   │   ├── dependencies.py       DI: DB session, Redis, auth guard
│   │   ├── domain/               Pure Python domain models (no framework)
│   │   │   ├── chart.py          Birth chart, Graha position models
│   │   │   └── dasha.py          DashaPeriod, DashaTree models
│   │   ├── models/               SQLAlchemy ORM models (17 tables)
│   │   ├── schemas/              Pydantic request/response schemas
│   │   ├── repositories/         DB access layer (ORM ↔ domain): user_repository.py,
│   │   │                         birth_chart_repository.py, planet_position_repository.py,
│   │   │                         house_repository.py, divisional_chart_repository.py,
│   │   │                         divisional_planet_repository.py, dasha_repository.py
│   │   ├── services/             Business logic
│   │   │   ├── ephemeris_wrapper.py   Swiss Ephemeris low-level wrapper
│   │   │   ├── ephemeris_service.py   Service layer for chart computation
│   │   │   ├── horoscope_engine.py    D1 birth chart engine + persist_d1() (orchestrates below)
│   │   │   ├── graha_engine.py        Graha dignity + strength scoring (Module 5)
│   │   │   ├── aspect_engine.py       Graha drishti / aspect computation (Module 7)
│   │   │   ├── house_engine.py        Bhava classification + lordship (Module 6)
│   │   │   ├── yoga_engine.py         Yoga Engine orchestrator (Module 8)
│   │   │   ├── yoga_predicates.py     Shared yoga rule vocabulary (houses_from, house_of_lord, etc.)
│   │   │   ├── yoga_registry.py       @register_yoga decorator + catalog
│   │   │   ├── yogas/                 One module per yoga category (Panch Mahapurusha,
│   │   │   │                         Gajakesari, Dhana, Raja, Neecha Bhanga — Phase 1;
│   │   │   │                         Chandra, Nabhasa, Arishta — Phase 2; Sanyasa,
│   │   │   │                         solar yogas, Amala/Kalasarpa — Phase 3)
│   │   │   ├── divisional_engine.py   D2–D60 varga engine + persist_chart()/persist_all()
│   │   │   └── dasha_engine.py        All 6 dasha system engines + persist_tree()
│   │   ├── routers/              HTTP handlers (thin, no business logic)
│   │   │   ├── auth.py
│   │   │   ├── horoscope.py
│   │   │   ├── divisional.py
│   │   │   └── dasha.py
│   │   └── security/             JWT (RS256), bcrypt, RSA key generation
│   │       └── keys/             private.pem + public.pem (gitignored)
│   └── web/                      Next.js 15 frontend
│       └── src/
│           ├── app/              App Router pages
│           ├── lib/              API client, auth hooks, types
│           └── components/       React components
│
├── packages/
│   └── shared/                   Shared Python constants + enums
│       ├── constants.py          All dasha period tables, sign lords, etc.
│       └── enums.py              Graha, Rashi, Nakshatra, ChartType enums
│
├── database/
│   ├── alembic.ini               Alembic configuration
│   ├── env.py                    Alembic migration environment
│   └── versions/
│       ├── 0001_initial_schema.py        Users, sessions, audit log
│       ├── 0002_astrology_schema.py      17 Vedic astrology tables
│       ├── 0003_dasha_persistence_fixes.py  dasha_type enum + lord column widening
│       ├── 0004_audit_column_completeness.py  missing created_at/updated_at/deleted_at
│                                             + combustion_orb_deg precision fix
│       └── 0005_seed_reference_tables.py  signs (12) / nakshatras (27) / padas (108)
│
├── data/
│   └── ephemeris/                Swiss Ephemeris .se1 data files (optional)
│                                 Without them: Moshier polynomial fallback
├── tests/
│   ├── conftest.py               pytest fixtures
│   ├── unit/                     Unit tests (no DB required)
│   └── integration/              Integration tests (require live DB)
│
├── scripts/
│   └── dev.sh                    Start API + frontend with hot reload
│
├── docs/
│   ├── architecture.md           Full architecture reference
│   ├── api-reference.md          Curated API reference with examples
│   ├── troubleshooting.md        Local setup troubleshooting guide
│   ├── contributing.md           Contribution guide
│   ├── developer-onboarding.md   Developer onboarding guide
│   ├── migration-v2.1-to-v2.2.md Migration guide v2.1 → v2.2
│   ├── deprecation-policy.md     API deprecation lifecycle
│   ├── pre-commit-setup.md       Pre-commit hooks setup
│   └── sdk/                      SDK versioning and publishing docs
│
├── attached_assets/              Project specification documents
├── replit.md                     Replit-specific project notes
└── README.md                     This file
```

---

## Module Build Status

| Module | Status | Description |
|--------|--------|-------------|
| 1 — Foundation | ✅ Complete | Auth, Users, RS256 JWT, DB bootstrap |
| 2 — Chart Engine | ✅ Complete | Swiss Ephemeris wrapper, birth chart |
| 3 — Graha Module | ✅ Complete | Planetary positions, dignities, aspects |
| 4 — Nakshatra Module | ✅ Complete | Lunar mansions, pada, ruling planets |
| 5 — Divisional Charts | ✅ Complete | D1–D60 varga computation (15 vargas) |
| 6 — Dasha Module | ✅ Complete | 6 dasha systems, 5-level sub-periods |
| 7 — Ashtakavarga | ✅ Complete | Bindu, Sarvashtakavarga (`/api/v1/ashtakavarga`) |
| 8 — Yoga Module | ✅ Complete | Yoga detection Phases 1–3 (`/api/v1/yoga`) |
| 9 — Research Tools | ✅ Complete | Projects, snapshots, statistics (`/api/v1/research`, `/api/v1/statistics`) |
| 10 — Visualization | ✅ Complete | Visualization payload engine (`/api/v1/visualization`) |
| 5+ | — Shadbala, Transit, Timeline, Reports, AI, Knowledge Graph, Workflow, Benchmark | ✅ Complete | See `/api/docs` and [docs/api-reference.md](docs/api-reference.md) |

---

## Architecture

**Local-First Architecture:**
```
User
 ↓
Next.js (Frontend)
 ↓
FastAPI (Backend API)
 ↓
PostgreSQL (Primary Data Store)
 ↓
Swiss Ephemeris (Astronomical Calculations)
```

All components run locally on a single machine. No external services required for core functionality. Swiss Ephemeris provides accurate planetary positions; PostgreSQL stores all computed charts and research data.

**Clean Architecture** — Domain → Repository → Service → Router. Each layer only imports inward.

**Async-first** — SQLAlchemy async engine (asyncpg), all FastAPI routes are async.

**Soft deletes** — All tables carry `deleted_at TIMESTAMPTZ NULL`. Hard deletes are never used.

**Constant-time auth** — Login checks bcrypt even when email doesn't exist (prevents timing oracle attacks).

**Moshier fallback** — If no `.se1` ephemeris files are present in `data/ephemeris/`, the engine falls back to Moshier polynomial approximation (~1 arc-minute accuracy). For production precision, download the Swiss Ephemeris data files from [astro.com](https://www.astro.com/ftp/swisseph/ephe/) and place `sepl_18.se1` and `seas_18.se1` in `data/ephemeris/`.

**DB timestamps** — `updated_at` is set by a PostgreSQL trigger, never by application code.

**UUID PKs** — All transactional tables use `gen_random_uuid()` as primary keys (prevents enumeration attacks).

**Persistence** — `HoroscopeEngine`, `DivisionalEngine`, and `DashaEngine` now persist every computed chart to PostgreSQL (`persist_d1()`, `persist_chart()`/`persist_all()`, `persist_tree()`), in addition to returning it in the API response. See [`docs/architecture.md`](docs/architecture.md#persistence-flow) for the full flow, the repository layer, and known limitations (e.g. `nakshatra_id` left `NULL` until the reference tables are seeded).
