# Contributing to AstroOS

AstroOS is a **local-first, single-user** Vedic astrology research platform (v2.1.0 "Vistara" line). Before contributing, read:

1. [CLAUDE_START_HERE.md](../CLAUDE_START_HERE.md) — project ground rules and scope
2. [README.md](../README.md) — local setup
3. [docs/architecture.md](architecture.md) — system design
4. [ASTROOS_PHASE_I_V2_1_ROADMAP.md](../ASTROOS_PHASE_I_V2_1_ROADMAP.md) — current roadmap

## Scope rules (non-negotiable)

- Everything runs locally: native PostgreSQL, FastAPI, Next.js. Redis is optional (JWT denylist only).
- **Out of scope:** Docker/Kubernetes/Helm/cloud deployment, multi-region, Celery, plugin marketplace, mobile SDKs. Existing Docker/K8s files are historical references only.
- Architecture changes require an ADR under `architecture/adr/` (frozen ADRs are never edited).

## Development environment

Follow the README "Local Setup" (target: under 30 minutes), then use:

```bash
./scripts/dev.sh          # API (:8000) + frontend (:3000), hot reload
./scripts/dev.sh --api    # API only
./scripts/dev.sh --web    # frontend only
```

## Code layout & conventions

Clean Architecture, layers import inward only:

```
routers/ (HTTP, thin)  →  services/ (business logic)  →  repositories/ (DB)  →  models/ (ORM)
schemas/ (Pydantic request/response)      domain/ (pure Python, no framework)
```

- **Backend:** Python 3.11+, async-first (asyncpg + SQLAlchemy 2.0 async), type hints and docstrings on all public functions/classes. No business logic in routers.
- **Frontend:** Next.js 15 App Router, TypeScript strict, TailwindCSS. `pnpm lint` and `pnpm typecheck` must pass.
- **Database:** migrations via Alembic (`database/versions/`), soft deletes only (`deleted_at`), `updated_at` set by DB trigger, UUID primary keys.
- **Constants/enums** shared between engines live in `packages/shared/`.

## Testing

```bash
PYTHONPATH=. pytest tests/unit/ -v                       # fast, no DB
PYTHONPATH=. pytest tests/ --cov=apps --cov=packages     # full with coverage
```

- New engine/service code requires unit tests; aim for 100% coverage on new modules (existing engines hold this bar).
- Tests requiring a live DB or real `.se1` ephemeris files go in `tests/integration/` and must be marked `integration`.
- The suite must stay green: no PR may reduce the passing count.

## Workflow

1. Branch from `main` (never commit directly to `main`).
2. Keep changes scoped to one concern; do not mix refactors with features.
3. Update documentation touched by your change (README, `docs/`, and `CLAUDE_START_HERE.md` if project-level facts changed).
4. Run tests + lint before opening a PR.
5. Commit messages: conventional style preferred, e.g. `feat(dasha): add yogini sub-period pruning`, `docs: fix setup steps`.

## Docstring style

Short imperative summaries; Google-style sections when parameters need explanation:

```python
def houses_from(reference_house: int, offset: int) -> int:
    """Return the house number `offset` places from `reference_house` (1-12, wrapping)."""
```

Pydantic models get a one-line class docstring plus `Field(description=...)` on non-obvious fields — these surface directly in the OpenAPI docs.
