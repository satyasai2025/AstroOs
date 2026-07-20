# AstroOS v2.1.0 "Vistara" — Release Notes

> **Release Date:** 2026-07-19  
> **Codename:** Vistara (Local-First Enhancement)  
> **Version:** 2.1.0  
> **Commit:** e9bd90ad8c9cf1da1dc46c66bc2baa3ebb047b8c

AstroOS v2.1.0 is a Phase I enhancement series focused on **precision, UX, research tooling, and governance** for the local-first Vedic Astrology Research Platform.

## Highlights

- **Shadbala Engine** — Full 6-fold strength computation (Naisargika, Dig, Drik, Chesta, Sthana, Kala) for all 9 grahas.
- **Ashtakavarga Engine** — Bhinnashtakavarga and Sarvashtakavarga with classical Shodhana reductions.
- **Precision Tests** — Verified planetary positions within <1 arc-second against Swiss Ephemeris golden references. Graceful Moshier fallback when `.se1` files are missing.
- **D3.js Visualizations** — North Indian diamond chart, interactive Dasha timeline with countdown, Nakshatra/Pada selector with search.
- **Dark Mode** — Light/dark theme toggle, persisted to localStorage.
- **Research Tools** — Project CRUD, snapshots/version comparison, CSV/JSON export with citations, research mode toggle (query logging), hypothesis validation workflow.
- **Yoga Detection Upgrades** — Phase 2 yogas (Chandra, Nabhasa, Arishta, etc.), strength scoring 0–100, composite yoga detection, activation timeline in Dasha, weakness conditions.
- **Governance Compliance** — All 8 AMPs resolved; governance audit passed; local-first architecture preserved (PostgreSQL localhost, FastAPI + Next.js local, Redis optional).

## Setup

Local-first setup remains unchanged:

```bash
# Clone and prepare
git clone <repo>
cd AstroOS
pnpm install
pip install -r requirements.txt

# Generate RSA keys for JWT signing
PYTHONPATH=. python apps/api/security/generate_keys.py

# Start database (PostgreSQL) locally and set DATABASE_URL in .env
# See README.md for complete instructions.

# Run dev environment (API + frontend with hot reload)
./scripts/dev.sh
```

API docs are available at `http://localhost:8000/api/docs` (Swagger) once the backend is running.

## Upgrade Notes

- This release is a **minor version bump** from v2.0.0 GA. There are no breaking changes to the API contract.
- All v2.0.0 data and charts remain compatible. New endpoints are additive.
- The `scripts/dev.sh` launcher is now the recommended way to start the dev environment.

## Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for the complete list of additions, fixes, and known issues.

## Support

See [docs/troubleshooting.md](docs/troubleshooting.md) for common setup issues. For API-specific questions, consult [docs/api-reference.md](docs/api-reference.md).

---

**Release Office** — AstroOS v2.1.0 is now GA.
