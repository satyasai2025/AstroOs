# AstroOS v2.0.0 GA Release Notes

> **Release Date:** 2026-07-19  
> **Status:** General Availability (GA)  
> **Codename:** "Siddhanta" (Establishment of Principles)

---

## Overview

AstroOS v2.0.0 represents the culmination of the enterprise Vedic Astrology platform, delivering a complete, production-ready system for birth chart computation, analysis, and reporting. This release transitions AstroOS from development to General Availability.

---

## Core Features

### 🏛️ Platform Architecture
- **API Layer:** FastAPI 0.115 with 87 HTTP endpoints
- **Frontend:** Next.js 15 with App Router, React 19, TypeScript
- **Database:** PostgreSQL 15+ (async via asyncpg + SQLAlchemy 2.0)
- **Cache/Auth:** Redis for JWT denylist
- **ASTROLOGY:** Swiss Ephemeris (pyswisseph 2.10.0) with Moshier fallback

### 🔐 Authentication & RBAC
- RS256 JWT authentication with asymmetric keys
- Role-Based Access Control (RBAC)
- Roles: `authenticated`, `researcher`, `admin`
- Token refresh and revocation

### 📊 Chart Computation
- **D1 Birth Chart:** Full planetary positions, house cusps, dignities
- **15 Divisional Charts (Vargas):** D2–D60 computation
- **6 Dasha Systems:** Vimshottari, Yogini, Ashtottari, Kalachakra, Chara, Narayana
- **6 Ayanamsa Systems:** Lahiri, KP, Raman, Yukteshwar, Fagan-Bradley, True Chitra
- **4 House Systems:** Whole Sign, Placidus, Koch, Equal

### 📈 Analysis Pipeline
- **Yoga Engine:** 47 rules across 10 categories detection
- **Rule Engine:** Priority-based evaluation with IN/NOT IN operators
- **Knowledge Graph:** Ontology-backed reasoning
- **Research Engine:** Snapshot capture for research projects
- **Unified Workflow:** Single endpoint for complete analysis pipeline

### 📄 Report Generation (Phase F)
- **Templates:** 7 professional report templates
  - Horoscope, Marriage, Career, Health, Wealth, Spiritual, Transit
- **Export Formats:** PDF (WeasyPrint), CSV, JSON
- **Customizable:** Optional timeline, verification, statistics sections

### 🔌 SDKs (Phase G)
- **Python SDK:** Full client with Pydantic models, typed exceptions
- **TypeScript SDK:** Zod schemas for type-safe API interaction

### 🚀 Production (Phase H)
- **Monitoring:** Prometheus metrics (`chart_computation_duration_seconds`, `api_request_duration_seconds`, `db_pool_usage`)
- **Health Checks:** `/health/live` (liveness) and `/health/ready` (readiness)
- **CI/CD:** GitHub Actions with Bandit + Trivy security scanning
- **Container:** Multi-stage Docker build with non-root user

---

## API Endpoints

| Category | Endpoints |
|----------|-----------|
| Auth | `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `POST /api/v1/auth/refresh` |
| Horoscope | `POST /api/v1/horoscope/d1` |
| Divisional | `POST /api/v1/divisional/{varga}`, `POST /api/v1/divisional/all` |
| Dasha | `POST /api/v1/dasha/{system}` |
| Yoga | `POST /api/v1/yoga/evaluate` |
| Report | `POST /api/v1/report/chart`, `POST /api/v1/report/chart/pdf`, `POST /api/v1/report/chart/csv` |
| Workflow | `POST /api/v1/workflow/analyze` |
| Health | `GET /api/healthz`, `GET /health/live`, `GET /health/ready`, `GET /metrics` |

---

## Installation

### Backend (API Server)

```bash
# Install dependencies
pip install -r apps/api/requirements.txt

# Run migrations
PYTHONPATH=. alembic -c database/alembic.ini upgrade head

# Start server
PYTHONPATH=. uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd apps/web
pnpm install
pnpm dev
```

### Docker (Production)

```bash
docker build -t astroos:2.0.0 -f Dockerfile.prod .
docker run -p 8000:8000 astroos:2.0.0
```

### Python SDK

```bash
pip install astroos
```

### TypeScript SDK

```bash
npm install @astroos/sdk
```

---

## Configuration

Required environment variables (see `.env.example`):

```env
DATABASE_URL=postgresql+asyncpg://astroos:password@localhost:5432/astroos
REDIS_URL=redis://localhost:6379/0
EPHEMERIS_PATH=data/ephemeris
JWT_PRIVATE_KEY_PATH=apps/api/security/keys/private.pem
JWT_PUBLIC_KEY_PATH=apps/api/security/keys/public.pem
```

---

## Changes Since v1.0.0-alpha

### Breaking Changes
- None. v2.0.0 is backward compatible with v1.0.0-alpha API contracts.

### New Features
- Report generation with PDF/CSV export
- Python and TypeScript SDKs
- Production monitoring and health endpoints
- Docker production image

### Security Updates
- Trivy vulnerability scanning in CI
- Bandit security scanning in CI
- Non-root container user

---

## Benchmarks & Accuracy

- **BM-CALC:** 9 planets validated per chart (Tier A/B tolerance)
- **BM-HOUSE:** 4 house systems validated
- **BM-VARGA:** 15 vargas, 675 checks
- **GC-MASTER Dataset:** 5 reference charts computed successfully

---

## Upgrade Guide

No upgrade path needed from v1.0.0-alpha. Fresh installation recommended.

---

## Support

- **Documentation:** https://docs.astroos.io
- **Issues:** https://github.com/astroos/astroos/issues
- **SDK Docs:** `docs/sdk/quickstart-python.md`, `docs/sdk/quickstart-typescript.md`

---

## Credits

Built by the Autonomous Engineering Organization for AstroOS.
- Architect: System design and ADR compliance
- Principal Engineer: Implementation and code quality  
- DevOps: CI/CD, containerization, production readiness
- QA: Testing and validation
- Security: Security audits and compliance
- PM: Release coordination and documentation

---

*© 2026 AstroOS. MIT License.*