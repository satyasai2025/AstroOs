#!/usr/bin/env bash
#
# AstroOS local development launcher (Phase I.1).
#
# Starts the FastAPI backend (uvicorn --reload) and the Next.js frontend
# (pnpm dev) together, with hot reload on both. Portable bash: works on
# Linux, macOS, and Windows Git Bash.
#
# Usage:
#   ./scripts/dev.sh            # start API (:8000) + frontend (:3000)
#   ./scripts/dev.sh --api      # API only
#   ./scripts/dev.sh --web      # frontend only
#
# Prerequisites (see README.md "Local Setup"):
#   - PostgreSQL running locally, DATABASE_URL set in .env
#   - RSA keys generated (apps/api/security/keys/*.pem)
#   - Migrations applied (alembic upgrade head)
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

RUN_API=1
RUN_WEB=1
case "${1:-}" in
  --api) RUN_WEB=0 ;;
  --web) RUN_API=0 ;;
  "") ;;
  *) echo "Usage: $0 [--api|--web]"; exit 1 ;;
esac

# ── Locate a Python interpreter (Git Bash on Windows may lack `python`) ──────
find_python() {
  for cand in python3 python py; do
    if command -v "$cand" >/dev/null 2>&1; then
      echo "$cand"; return 0
    fi
  done
  # Common Windows install location
  local win_py="$LOCALAPPDATA/Programs/Python"
  if [ -d "$win_py" ]; then
    local exe
    exe=$(ls -d "$win_py"/Python3*/python.exe 2>/dev/null | sort | tail -1 || true)
    if [ -n "$exe" ]; then echo "$exe"; return 0; fi
  fi
  return 1
}

PIDS=()
cleanup() {
  echo ""
  echo "Shutting down..."
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ── Pre-flight checks ────────────────────────────────────────────────────────
if [ "$RUN_API" = 1 ]; then
  PYTHON="$(find_python)" || { echo "ERROR: Python not found on PATH."; exit 1; }
  if [ ! -f ".env" ] && [ -z "${DATABASE_URL:-}" ]; then
    echo "WARNING: no .env file and DATABASE_URL is not set — the API will fail to start."
    echo "         See README.md section 'Environment variables'."
  fi
  if [ ! -f "apps/api/security/keys/private.pem" ]; then
    echo "WARNING: RSA keys missing — generating them now..."
    PYTHONPATH=. "$PYTHON" apps/api/security/generate_keys.py
  fi
fi

if [ "$RUN_WEB" = 1 ] && ! command -v pnpm >/dev/null 2>&1; then
  echo "ERROR: pnpm not found. Install with: npm install -g pnpm"
  exit 1
fi

# ── Start processes ──────────────────────────────────────────────────────────
if [ "$RUN_API" = 1 ]; then
  echo "Starting API on http://localhost:${API_PORT} (hot reload)..."
  PYTHONPATH=. "$PYTHON" -m uvicorn apps.api.main:app \
    --host 127.0.0.1 --port "$API_PORT" --reload &
  PIDS+=($!)
fi

if [ "$RUN_WEB" = 1 ]; then
  echo "Starting frontend on http://localhost:${WEB_PORT} (hot reload)..."
  (cd apps/web && pnpm dev --port "$WEB_PORT") &
  PIDS+=($!)
fi

echo ""
echo "AstroOS dev environment running. Press Ctrl+C to stop."
[ "$RUN_API" = 1 ] && echo "  API:      http://localhost:${API_PORT}/api/healthz  (docs: /api/docs when DEBUG=true)"
[ "$RUN_WEB" = 1 ] && echo "  Frontend: http://localhost:${WEB_PORT}"

wait
