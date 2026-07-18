# AstroOS v2.0.0 — Software Bill of Materials (SBOM)

> Direct dependencies only, read verbatim from each manifest in the working tree. Updated 2026-07-19 after the Governance Audit's blocker-resolution pass (see `GA_RELEASE_GOVERNANCE_AUDIT.md`). Transitive dependencies are not enumerated here — generate a full CycloneDX/SPDX SBOM with `pip-audit`/`cyclonedx-py` and `pnpm licenses` before GA if a complete transitive SBOM is required for compliance.

## Backend — `apps/api/requirements.txt` (now exact-pinned)

| Package | Version |
|---|---|
| fastapi | ==0.138.1 |
| uvicorn[standard] | ==0.49.0 |
| sqlalchemy[asyncio] | ==2.0.51 |
| asyncpg | ==0.31.0 |
| alembic | ==1.18.5 |
| psycopg2-binary | ==2.9.12 |
| pydantic | ==2.11.7 |
| pydantic-settings | ==2.14.2 |
| bcrypt | ==5.0.0 |
| python-jose[cryptography] | ==3.5.0 |
| cryptography | ==49.0.0 |
| redis | ==8.0.1 |
| python-multipart | ==0.0.32 |
| httpx | ==0.28.1 |
| pytest | ==9.1.1 |
| pytest-asyncio | ==1.4.0 |
| pytest-cov | ==7.1.0 |
| greenlet | ==3.5.3 |
| pyswisseph | ==2.10.3.2 |
| email-validator | ==2.3.0 |
| openpyxl | ==3.1.5 |
| timezonefinder | ==8.2.4 |
| truststore | ==0.10.4 |
| slowapi | ==0.1.10 |

All 24 pinned to the exact versions verified installed and importable in this environment (`pip show`/`pip list --format=freeze`), not guessed.

## Root package — `pyproject.toml` (name: `astroos`, version 2.0.0)

| Package | Version constraint |
|---|---|
| weasyprint | >=60.0 |
| prometheus-client | >=0.20.0 |
| jinja2 | >=3.0 |
| httpx | >=0.27.0 |

## Frontend — `apps/web/package.json` (version 2.0.0)

| Package | Version constraint |
|---|---|
| @tanstack/react-query | catalog: |
| @tanstack/react-query-devtools | ^5.62.0 |
| next | ^15.1.0 |
| react | catalog: |
| react-dom | catalog: |
| clsx | catalog: |
| tailwind-merge | catalog: |
| zod | catalog: |
| zustand | ^5.0.2 |
| js-cookie | ^3.0.5 |
| date-fns | ^4.1.0 |

Dev: `@types/js-cookie`, `@types/node`, `@types/react`, `@types/react-dom`, `autoprefixer`, `postcss`, `tailwindcss`, `typescript`, `eslint`, `eslint-config-next`, `@eslint/eslintrc` (added to activate a flat `eslint.config.mjs`, now committed and verified running clean).

## Python SDK — `sdks/python/pyproject.toml` (version 2.0.0, license: MIT — backed by root `LICENSE`)

| Package | Version constraint |
|---|---|
| httpx | >=0.27.0 |

## TypeScript SDK — `sdks/typescript/astroos/package.json` (version 2.0.0, license: MIT — backed by root `LICENSE`)

| Package | Version constraint |
|---|---|
| zod | ^3.23.0 |

The previous `axios` dependency was removed (unused — the SDK source uses native `fetch`, not axios). The orphaned, disconnected duplicate manifest previously at `sdks/typescript/package.json` has been deleted; this is now the single source of truth for the TypeScript SDK's dependencies.

## Licenses claimed vs. present

`MIT` is claimed in both SDK manifests. A root `LICENSE` file (MIT) now backs that claim. **Note:** its copyright line uses "AstroOS" as a placeholder holder name — replace with your actual legal entity/name if different before publishing.
