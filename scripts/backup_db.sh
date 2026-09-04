#!/usr/bin/env bash
#
# AstroOS — Database backup helper
#
# Creates a timestamped, compressed (custom-format) pg_dump into BACKUP_DIR
# (default D:/AstroOS_Backups — a separate drive, so dumps survive even if the
# project folder is lost). Override BACKUP_DIR to change location.
#
# Usage:
#   ./scripts/backup_db.sh [DBNAME]
#   BACKUP_DIR=/e/somewhere ./scripts/backup_db.sh astroos
#
#   DBNAME defaults to "astroos" (the populated database). Pass "astroos_db"
#   to back up the application database instead, or any other DB name.
#
# Connection (host/port/user/password) is read from DATABASE_URL in .env, so
# it stays in sync with the app. Override PG_BIN if PostgreSQL lives elsewhere.
#
# Restore (into an EXISTING, empty-ish target database):
#   PGPASSWORD=<pass> "$PG_BIN/pg_restore" -h localhost -p 5432 -U <user> \
#       -d <target_db> --clean --if-exists --no-owner <backups/FILE.dump>
#
set -euo pipefail

cd "$(dirname "$0")/.."   # repo root

DB="${1:-astroos}"
PG_BIN="${PG_BIN:-/c/Program Files/PostgreSQL/18/bin}"
ENV_FILE=".env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found." >&2
  exit 1
fi

# Parse DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
URL="$(grep '^DATABASE_URL=' "$ENV_FILE" | cut -d= -f2-)"
USER="$(echo "$URL"  | sed -E 's#.*://([^:]+):[^@]+@.*#\1#')"
PASS="$(echo "$URL"  | sed -E 's#.*://[^:]+:([^@]+)@.*#\1#')"
HOST="$(echo "$URL"  | sed -E 's#.*@([^:/]+):[0-9]+/.*#\1#')"
PORT="$(echo "$URL"  | sed -E 's#.*@[^:/]+:([0-9]+)/.*#\1#')"

BACKUP_DIR="${BACKUP_DIR:-/d/AstroOS_Backups}"
mkdir -p "$BACKUP_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="${BACKUP_DIR}/${DB}_${TS}.dump"

echo "Backing up '$DB' from $HOST:$PORT as '$USER' -> $OUT"
PGPASSWORD="$PASS" "$PG_BIN/pg_dump.exe" \
  -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" -Fc -f "$OUT"

SIZE="$(du -h "$OUT" | cut -f1)"
echo "OK: $OUT ($SIZE)"

# Retention: keep the 10 most recent dumps per database, prune older ones.
ls -t "${BACKUP_DIR}/${DB}"_*.dump 2>/dev/null | tail -n +11 | while read -r old; do
  echo "Pruning old backup: $old"
  rm -f "$old"
done
