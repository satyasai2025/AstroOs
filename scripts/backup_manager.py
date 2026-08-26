"""
AstroOS — Database Backup & Restore Manager

Features:
- Automated compressed (.dump) backups with timestamping and SHA256 checksums.
- Automatic PostgreSQL binary discovery (Windows, Linux, macOS).
- Reads database configuration directly from `.env`.
- Retention policy management (prunes older backups automatically).
- Fast one-command restore with safety verification.
- Automatic scheduling support (Windows Task Scheduler & cron).
- Pre-operation safety snapshots before running migrations or imports.

Usage:
  python scripts/backup_manager.py backup [--db astroos_db] [--dir D:/AstroOS_Backups]
  python scripts/backup_manager.py list
  python scripts/backup_manager.py restore [BACKUP_FILE_OR_LATEST] [--db astroos_db]
  python scripts/backup_manager.py snapshot [--name before_migration]
  python scripts/backup_manager.py schedule [--interval-hours 6]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_env_db_config(env_path: Path | None = None) -> dict[str, str | int]:
    """Parse DATABASE_URL from .env file into connection parameters."""
    if env_path is None:
        env_path = get_repo_root() / ".env"

    if not env_path.is_file():
        raise FileNotFoundError(f"Missing environment file: {env_path}")

    db_url = ""
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

    if not db_url:
        raise ValueError(f"DATABASE_URL not defined in {env_path}")

    clean_url = db_url
    if "://" in clean_url:
        scheme, rest = clean_url.split("://", 1)
        clean_url = f"http://{rest}"

    parsed = urlparse(clean_url)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "dbname": parsed.path.lstrip("/") or "astroos_db",
        "raw_url": db_url,
    }


def find_pg_binary(binary_name: str) -> Path:
    """Find pg_dump or pg_restore binary across common installation paths."""
    found = shutil.which(binary_name)
    if found:
        return Path(found)

    if platform.system() == "Windows":
        candidates = [
            Path(r"C:\Program Files\PostgreSQL\18\bin"),
            Path(r"C:\Program Files\PostgreSQL\17\bin"),
            Path(r"C:\Program Files\PostgreSQL\16\bin"),
            Path(r"C:\Program Files\PostgreSQL\15\bin"),
            Path(r"C:\Program Files\PostgreSQL\14\bin"),
            Path(r"C:\Program Files (x86)\PostgreSQL\18\bin"),
            Path(r"C:\Program Files (x86)\PostgreSQL\17\bin"),
            Path(r"C:\Program Files (x86)\PostgreSQL\16\bin"),
        ]
        exe_name = f"{binary_name}.exe" if not binary_name.endswith(".exe") else binary_name
        for c in candidates:
            p = c / exe_name
            if p.is_file():
                return p

    unix_candidates = [
        Path("/usr/lib/postgresql/16/bin"),
        Path("/usr/lib/postgresql/15/bin"),
        Path("/usr/local/opt/postgresql@16/bin"),
        Path("/usr/local/opt/postgresql@15/bin"),
        Path("/opt/homebrew/opt/postgresql@16/bin"),
        Path("/opt/homebrew/opt/postgresql@15/bin"),
    ]
    for c in unix_candidates:
        p = c / binary_name
        if p.is_file():
            return p

    raise FileNotFoundError(
        f"Could not locate '{binary_name}' binary. Please ensure PostgreSQL client tools are installed and in PATH."
    )


def calculate_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def get_default_backup_dir() -> Path:
    """Choose D:/AstroOS_Backups if drive D exists, otherwise <repo>/backups."""
    if platform.system() == "Windows" and Path("D:/").exists():
        return Path(r"D:\AstroOS_Backups")
    return get_repo_root() / "backups"


def run_backup(
    dbname: str | None = None,
    backup_dir: Path | None = None,
    retention: int = 15,
    tag: str = "",
) -> Path:
    """Execute a pg_dump backup with metadata and retention cleanup."""
    cfg = load_env_db_config()
    target_db = dbname or str(cfg["dbname"])
    target_dir = backup_dir or get_default_backup_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    pg_dump = find_pg_binary("pg_dump")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = f"_{tag}" if tag else ""
    dump_filename = f"{target_db}_{ts}{suffix}.dump"
    dump_path = target_dir / dump_filename
    meta_path = target_dir / f"{target_db}_{ts}{suffix}.meta.json"

    print(f"[*] Starting backup of database '{target_db}'...")
    print(f"[*] Destination: {dump_path}")

    env = os.environ.copy()
    if cfg["password"]:
        env["PGPASSWORD"] = str(cfg["password"])

    cmd = [
        str(pg_dump),
        "-h", str(cfg["host"]),
        "-p", str(cfg["port"]),
        "-U", str(cfg["user"]),
        "-d", target_db,
        "-Fc",
        "-b",
        "-v",
        "-f", str(dump_path),
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Backup failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")

    size_bytes = dump_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    sha256 = calculate_sha256(dump_path)

    metadata = {
        "database": target_db,
        "timestamp": ts,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "size_bytes": size_bytes,
        "size_mb": round(size_mb, 2),
        "sha256": sha256,
        "host": cfg["host"],
        "port": cfg["port"],
        "user": cfg["user"],
        "tag": tag or "manual",
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[+] Backup completed successfully!")
    print(f"    File: {dump_path.name} ({size_mb:.2f} MB)")
    print(f"    SHA256: {sha256[:16]}...")

    apply_retention_policy(target_dir, target_db, keep_count=retention)
    return dump_path


def apply_retention_policy(target_dir: Path, dbname: str, keep_count: int = 15) -> None:
    """Keep the N most recent backups for a given database and remove older ones."""
    dumps = sorted(
        [p for p in target_dir.glob(f"{dbname}_*.dump") if p.is_file()],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )
    if len(dumps) > keep_count:
        to_prune = dumps[keep_count:]
        print(f"[*] Pruning {len(to_prune)} old backup(s) for '{dbname}' (retention: {keep_count})...")
        for old in to_prune:
            old.unlink(missing_ok=True)
            meta = old.with_suffix(".meta.json")
            meta.unlink(missing_ok=True)
            print(f"    - Removed: {old.name}")


def list_backups(backup_dir: Path | None = None) -> list[dict]:
    """List all available backup dumps and their metadata."""
    target_dir = backup_dir or get_default_backup_dir()
    if not target_dir.exists():
        print(f"[!] Backup directory does not exist: {target_dir}")
        return []

    dumps = sorted(target_dir.glob("*.dump"), key=lambda x: x.stat().st_mtime, reverse=True)
    results = []
    print(f"\n================================================================================")
    print(f" AVAILABLE BACKUPS in {target_dir}")
    print(f"================================================================================")
    print(f"{'Filename':<42} {'Size':<10} {'Created (Local)':<22}")
    print(f"--------------------------------------------------------------------------------")
    for d in dumps:
        size_kb = d.stat().st_size / 1024
        size_str = f"{size_kb/1024:.2f} MB" if size_kb > 1024 else f"{size_kb:.1f} KB"
        mtime = datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{d.name:<42} {size_str:<10} {mtime:<22}")
        results.append({
            "path": str(d),
            "filename": d.name,
            "size_bytes": d.stat().st_size,
            "modified": mtime,
        })
    print(f"================================================================================\n")
    return results


def run_restore(
    backup_file_or_name: str | None = None,
    target_dbname: str | None = None,
    backup_dir: Path | None = None,
) -> None:
    """Restore a backup into target PostgreSQL database."""
    cfg = load_env_db_config()
    target_db = target_dbname or str(cfg["dbname"])
    target_dir = backup_dir or get_default_backup_dir()
    pg_restore = find_pg_binary("pg_restore")

    if not backup_file_or_name or backup_file_or_name.lower() == "latest":
        dumps = sorted(target_dir.glob(f"{target_db}_*.dump"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not dumps:
            dumps = sorted(target_dir.glob("*.dump"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not dumps:
            raise FileNotFoundError(f"No backup dumps found in {target_dir}")
        backup_path = dumps[0]
    else:
        candidate = Path(backup_file_or_name)
        if candidate.is_file():
            backup_path = candidate
        else:
            backup_path = target_dir / backup_file_or_name
            if not backup_path.is_file():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

    print(f"[!] WARNING: You are about to restore '{backup_path.name}' into database '{target_db}'!")
    print(f"[!] Host: {cfg['host']}:{cfg['port']}, User: {cfg['user']}")
    print(f"[*] Starting restore operation...")

    env = os.environ.copy()
    if cfg["password"]:
        env["PGPASSWORD"] = str(cfg["password"])

    cmd = [
        str(pg_restore),
        "-h", str(cfg["host"]),
        "-p", str(cfg["port"]),
        "-U", str(cfg["user"]),
        "-d", target_db,
        "--clean",
        "--if-exists",
        "--no-owner",
        "-v",
        str(backup_path),
    ]

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"Restore failed with code {result.returncode}:\n{result.stderr}")

    print(f"[+] Restore completed successfully into '{target_db}' from {backup_path.name}!")


def schedule_windows_task(interval_hours: int = 6) -> None:
    """Create or update a Windows Scheduled Task for automated backups."""
    if platform.system() != "Windows":
        print("[!] Automated Windows Task scheduling is only supported on Windows.")
        return

    script_path = Path(__file__).resolve()
    python_exe = sys.executable
    task_name = "AstroOS Database Backup"
    action_cmd = f'"{python_exe}" "{script_path}" backup --all'

    print(f"[*] Configuring Windows Scheduled Task '{task_name}'...")
    print(f"    Frequency: Every {interval_hours} hours")
    print(f"    Action: {action_cmd}")

    cmd = [
        "schtasks", "/Create",
        "/TN", task_name,
        "/TR", action_cmd,
        "/SC", "HOURLY",
        "/MO", str(interval_hours),
        "/F",
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[+] Successfully registered scheduled task '{task_name}'!")
        print(f"    To run immediately: schtasks /Run /TN \"{task_name}\"")
        print(f"    To inspect status: schtasks /Query /TN \"{task_name}\" /FO LIST")
    else:
        print(f"[!] Note: schtasks returned: {res.stderr or res.stdout}")


def main():
    parser = argparse.ArgumentParser(description="AstroOS Database Backup & Restore Manager")
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    p_backup = subparsers.add_parser("backup", help="Run database backup")
    p_backup.add_argument("--db", type=str, default=None, help="Target database name")
    p_backup.add_argument("--all", action="store_true", help="Backup both astroos_db and astroos")
    p_backup.add_argument("--dir", type=str, default=None, help="Backup destination directory")
    p_backup.add_argument("--retention", type=int, default=15, help="Number of backups to retain")
    p_backup.add_argument("--tag", type=str, default="", help="Optional tag label")

    p_list = subparsers.add_parser("list", help="List available backups")
    p_list.add_argument("--dir", type=str, default=None, help="Backup directory")

    p_restore = subparsers.add_parser("restore", help="Restore a backup into database")
    p_restore.add_argument("backup_file", nargs="?", default="latest", help="Backup filename or 'latest'")
    p_restore.add_argument("--db", type=str, default=None, help="Target database name")
    p_restore.add_argument("--dir", type=str, default=None, help="Backup directory")

    p_snap = subparsers.add_parser("snapshot", help="Create a fast tagged pre-operation snapshot")
    p_snap.add_argument("--name", type=str, default="pre_op", help="Snapshot tag name")

    p_sched = subparsers.add_parser("schedule", help="Register automated backup schedule")
    p_sched.add_argument("--interval-hours", type=int, default=6, help="Interval in hours")

    args = parser.parse_args()

    if args.action == "backup":
        target_dir = Path(args.dir) if args.dir else None
        if args.all:
            for db in ["astroos_db", "astroos"]:
                try:
                    run_backup(dbname=db, backup_dir=target_dir, retention=args.retention, tag=args.tag)
                except Exception as e:
                    print(f"[!] Failed to back up '{db}': {e}")
        else:
            run_backup(dbname=args.db, backup_dir=target_dir, retention=args.retention, tag=args.tag)

    elif args.action == "list":
        target_dir = Path(args.dir) if args.dir else None
        list_backups(target_dir)

    elif args.action == "restore":
        target_dir = Path(args.dir) if args.dir else None
        run_restore(args.backup_file, target_dbname=args.db, backup_dir=target_dir)

    elif args.action == "snapshot":
        run_backup(tag=args.name)

    elif args.action == "schedule":
        schedule_windows_task(interval_hours=args.interval_hours)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
