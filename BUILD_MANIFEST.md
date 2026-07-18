# AstroOS v2.0.0 — Build Manifest

> Records the exact environment and commands used to verify this release candidate. Generated 2026-07-19. See `GA_RELEASE_GOVERNANCE_AUDIT.md` for full validation results.

## Source

| Field | Value |
|---|---|
| Base commit | `d98fd018055b633cdb7256b329a834b3e8e892b5` (tag `v1.0.0-alpha`) |
| Working tree | 288 uncommitted changes on top of base commit (not yet committed — see Governance Audit Phase 1) |
| Branch | `main` |

## Toolchain versions used for verification (this environment)

| Tool | Version |
|---|---|
| Python | 3.13.5 |
| Node.js | v24.17.0 |
| npm | 11.13.0 |
| pytest | 9.1.1 |
| FastAPI | 0.138.1 |
| SQLAlchemy | 2.0.51 |
| Alembic | 1.18.5 |

CI (`.github/workflows/ci.yml`, as currently written — presently YAML-invalid, see audit) targets Python 3.11 and Node 20, which differ from the versions used to verify locally above; both should be treated as in-scope for compatibility testing once CI is fixed and rerun.

## Build commands (backend)

```bash
pip install -r apps/api/requirements.txt
python apps/api/security/generate_keys.py
alembic -c database/alembic.ini upgrade head   # verified: single linear head, 0001-0010
TEST_DATABASE_URL=<postgres-url> pytest -c apps/api/pytest.ini -m "not integration"  # 1759 passed, 0 failed
TEST_DATABASE_URL=<postgres-url> pytest -c apps/api/pytest.ini -m "integration"      # 2 passed
TEST_DATABASE_URL=<postgres-url> pytest -c apps/api/pytest.ini -m "regression"       # 31 passed
```

All three verified against a live Postgres instance on 2026-07-19 — see `GA_RELEASE_GOVERNANCE_AUDIT.md`'s "Full Test-Suite Validation" section for the 13 real bugs this surfaced and fixed.

## Build commands (frontend)

```bash
cd apps/web
pnpm install --frozen-lockfile
pnpm run typecheck   # verified clean
pnpm run lint         # verified clean (eslint.config.mjs added)
pnpm run build
```

## Build commands (SDKs)

```bash
# Python SDK — verified successful
cd sdks/python && python -m build --wheel
# -> dist/astroos_sdk-2.0.0-py3-none-any.whl

# TypeScript SDK — verified successful (after adding zod + fixing a field-naming bug)
cd sdks/typescript/astroos && npm install && npx tsc
# -> dist/index.js, dist/index.d.ts, dist/schemas.js, dist/schemas.d.ts
```

## Container build

```bash
docker build -t astroos:2.0.0 -f Dockerfile.prod .
```

**Not executed in this environment** — no Docker daemon available in this sandbox. Static review flags a likely defect in the builder stage (see `GA_RELEASE_GOVERNANCE_AUDIT.md` Phase 2). Must be run and confirmed on a Docker-capable host before GA.

## Reproducibility notes

- `apps/api/requirements.txt` is now pinned exactly (`==` throughout, 24/24 entries, all values read from `pip show`/`pip list --format=freeze` in this verification environment, not guessed). A dedicated lockfile (`pip-compile`/`uv pip compile`) would still be a further improvement for full transitive-dependency reproducibility, but direct dependencies are no longer a moving target.
- `apps/web` frontend has a `pnpm-lock.yaml` — reproducible as-is.
- Python SDK (`sdks/python`) and TypeScript SDK have no lockfiles of their own; low risk given each has 1–2 direct dependencies, but worth adding for strict reproducibility.
