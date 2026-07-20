# Troubleshooting Local Setup

Common problems when setting up AstroOS locally (native PostgreSQL + FastAPI + Next.js). Follow [README.md](../README.md) "Local Setup" first; use this guide when a step fails.

---

## Python / API

### `python: command not found` (Windows Git Bash)

Git Bash often doesn't expose `python`. Options:
- Use the launcher: `py -3 ...`
- Add your install to PATH, e.g. `%LOCALAPPDATA%\Programs\Python\Python3xx`
- `scripts/dev.sh` auto-detects common Windows install locations.

### `ModuleNotFoundError: No module named 'apps'`

You forgot `PYTHONPATH=.`. All commands (uvicorn, alembic, pytest) must run from the repo root with:

```bash
PYTHONPATH=. uvicorn apps.api.main:app --reload
```

### `pip install` fails building `pyswisseph` or `asyncpg`

These packages need build tools when no wheel matches your Python version.
- Prefer Python 3.11 or 3.12 (prebuilt wheels available).
- Windows: install "Visual Studio Build Tools" (C++ workload) if a compile is required.
- Linux: `sudo apt install build-essential python3-dev`.

### API exits at startup: `DATABASE_URL ... field required`

`DATABASE_URL` has no default. Create a `.env` in the repo root (see README section 4) or export it in your shell.

### API exits: cannot read `private.pem` / `public.pem`

The RS256 keys are gitignored and must be generated after every fresh clone:

```bash
PYTHONPATH=. python apps/api/security/generate_keys.py
```

---

## PostgreSQL

### `connection refused` on port 5432

PostgreSQL isn't running.
- Windows: `services.msc` → start "postgresql-x64-15" (or your version).
- macOS: `brew services start postgresql@15`.
- Linux: `sudo systemctl start postgresql`.

### `password authentication failed for user "astroos_user"`

The user/database don't exist yet. As the `postgres` superuser:

```sql
CREATE USER astroos_user WITH PASSWORD 'astroos_pass';
CREATE DATABASE astroos_db OWNER astroos_user;
GRANT ALL PRIVILEGES ON DATABASE astroos_db TO astroos_user;
```

Then ensure `.env`'s `DATABASE_URL` matches exactly:
`postgresql+asyncpg://astroos_user:astroos_pass@localhost:5432/astroos_db`

### Alembic: `Target database is not up to date` / relation does not exist

Run migrations from the repo root:

```bash
PYTHONPATH=. alembic -c database/alembic.ini upgrade head
PYTHONPATH=. alembic -c database/alembic.ini current   # should print head revision
```

### `gen_random_uuid() does not exist`

Requires PostgreSQL 13+. Upgrade, or on very old installs run `CREATE EXTENSION pgcrypto;` in the database.

---

## Redis (optional)

Redis is only used for the JWT denylist (logout). **If Redis is absent, the API still runs** — logout becomes a no-op and a warning is logged. You do not need Redis for local development.

If you do run it and see `Connection refused` on 6379, start the service or remove/ignore `REDIS_URL`.

---

## Frontend

### `pnpm: command not found`

```bash
npm install -g pnpm
```

### `pnpm install` fails on workspace

Run it from the **repo root** (there is a `pnpm-workspace.yaml`), not inside `apps/web`.

### Frontend loads but API calls fail (404 / network error)

- The API must be running on port 8000 — Next.js rewrites proxy `/api/*` to `http://localhost:8000`.
- Check `curl http://localhost:8000/api/healthz`.
- If you changed the API port, update the rewrite target in `apps/web/next.config.ts` or set `API_PORT` consistently.

### Port 3000 or 8000 already in use

```bash
# Find and kill (Windows Git Bash)
netstat -ano | grep :8000
taskkill //PID <pid> //F
# macOS/Linux
lsof -i :8000 && kill <pid>
```

Or start on different ports: `API_PORT=8001 WEB_PORT=3001 ./scripts/dev.sh`.

---

## Ephemeris accuracy

### Health check shows `"mode": "moshier"`

No `.se1` Swiss Ephemeris data files were found. This is fine for development (~1 arc-minute accuracy). For full precision, download `sepl_18.se1` and `seas_18.se1` from https://www.astro.com/ftp/swisseph/ephe/ and place them in `data/ephemeris/`. Restart the API; the health check should report `"mode": "swiss"`.

---

## Tests

```bash
PYTHONPATH=. pytest tests/unit/ -v
```

- Unit tests need **no database**.
- Integration tests marked `integration` need a live PostgreSQL and (some) real `.se1` files; they are excluded by default (`-m "not integration"`).

---

## Still stuck?

1. Re-check each step in [README.md](../README.md) — order matters (DB → .env → keys → migrations → API → frontend).
2. Run the API in the foreground and read the first traceback line — startup errors are explicit (missing env var, missing key file, DB unreachable).
3. Check [docs/architecture.md](architecture.md) for how components fit together.
