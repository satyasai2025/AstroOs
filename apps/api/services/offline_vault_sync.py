"""
AstroOS — Offline SQLite Sync & Local Storage Engine
====================================================
Provides offline-first storage and reconciliation for chart profiles,
consultation dossiers, and research snapshots when running as a standalone
desktop (.exe / .dmg) or mobile/PWA without active network access.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_OFFLINE_DB_PATH = Path("data/astroos_offline.db")


@dataclass
class OfflineChartRecord:
    chart_id: str
    native_name: str
    birth_date_iso: str
    latitude: float
    longitude: float
    city_name: str = ""
    domain: str = "career"
    notes: str = ""
    consultation_payload_json: str = "{}"
    is_synced: bool = False
    created_at_iso: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at_iso: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


from contextlib import contextmanager

class OfflineVaultSyncManager:
    """
    Manages embedded SQLite storage and offline-to-cloud synchronization.
    """

    def __init__(self, db_path: Path = DEFAULT_OFFLINE_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS offline_charts (
                    chart_id TEXT PRIMARY KEY,
                    native_name TEXT NOT NULL,
                    birth_date_iso TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    city_name TEXT,
                    domain TEXT,
                    notes TEXT,
                    consultation_payload_json TEXT,
                    is_synced INTEGER DEFAULT 0,
                    created_at_iso TEXT,
                    updated_at_iso TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ephemeris_health (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    ephemeris_dir TEXT,
                    seas_exists INTEGER,
                    semo_exists INTEGER,
                    sepl_exists INTEGER,
                    last_verified_iso TEXT
                )
            """)
            conn.commit()

    def verify_ephemeris_bundle(self, ephemeris_dir: str = "data/ephemeris") -> Dict[str, Any]:
        """Verifies Swiss Ephemeris data files are present and valid locally."""
        p = Path(ephemeris_dir)
        seas = (p / "seas_18.se1").is_file()
        semo = (p / "semo_18.se1").is_file()
        sepl = (p / "sepl_18.se1").is_file()
        is_complete = seas and semo and sepl

        with self._connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ephemeris_health
                (id, ephemeris_dir, seas_exists, semo_exists, sepl_exists, last_verified_iso)
                VALUES (1, ?, ?, ?, ?, ?)
            """, (str(p), int(seas), int(semo), int(sepl), datetime.now(timezone.utc).isoformat()))
            conn.commit()

        return {
            "ephemeris_dir": str(p),
            "seas_18_present": seas,
            "semo_18_present": semo,
            "sepl_18_present": sepl,
            "is_fully_offline_ready": is_complete,
            "total_range": "600 BCE to 2400 CE" if is_complete else "Incomplete",
        }

    def save_offline_chart(
        self,
        chart_id: str,
        native_name: str,
        birth_date_iso: str,
        latitude: float,
        longitude: float,
        city_name: str = "",
        domain: str = "career",
        notes: str = "",
        consultation_payload: Optional[Dict[str, Any]] = None,
    ) -> OfflineChartRecord:
        """Saves or updates a chart profile in the local offline vault."""
        now = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(consultation_payload or {})

        with self._connection() as conn:
            conn.execute("""
                INSERT INTO offline_charts (
                    chart_id, native_name, birth_date_iso, latitude, longitude,
                    city_name, domain, notes, consultation_payload_json, is_synced,
                    created_at_iso, updated_at_iso
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                ON CONFLICT(chart_id) DO UPDATE SET
                    native_name = excluded.native_name,
                    birth_date_iso = excluded.birth_date_iso,
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    city_name = excluded.city_name,
                    domain = excluded.domain,
                    notes = excluded.notes,
                    consultation_payload_json = excluded.consultation_payload_json,
                    is_synced = 0,
                    updated_at_iso = excluded.updated_at_iso
            """, (
                chart_id, native_name, birth_date_iso, latitude, longitude,
                city_name, domain, notes, payload_str, now, now
            ))
            conn.commit()

        return OfflineChartRecord(
            chart_id=chart_id,
            native_name=native_name,
            birth_date_iso=birth_date_iso,
            latitude=latitude,
            longitude=longitude,
            city_name=city_name,
            domain=domain,
            notes=notes,
            consultation_payload_json=payload_str,
            is_synced=False,
            created_at_iso=now,
            updated_at_iso=now,
        )

    def get_offline_chart(self, chart_id: str) -> Optional[OfflineChartRecord]:
        """Retrieves a single chart record by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM offline_charts WHERE chart_id = ?", (chart_id,)
            ).fetchone()
            if not row:
                return None
            return OfflineChartRecord(
                chart_id=row["chart_id"],
                native_name=row["native_name"],
                birth_date_iso=row["birth_date_iso"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                city_name=row["city_name"] or "",
                domain=row["domain"] or "career",
                notes=row["notes"] or "",
                consultation_payload_json=row["consultation_payload_json"] or "{}",
                is_synced=bool(row["is_synced"]),
                created_at_iso=row["created_at_iso"],
                updated_at_iso=row["updated_at_iso"],
            )

    def list_offline_charts(self, limit: int = 100) -> List[OfflineChartRecord]:
        """Lists all local charts stored in the offline vault."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM offline_charts ORDER BY updated_at_iso DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                OfflineChartRecord(
                    chart_id=r["chart_id"],
                    native_name=r["native_name"],
                    birth_date_iso=r["birth_date_iso"],
                    latitude=r["latitude"],
                    longitude=r["longitude"],
                    city_name=r["city_name"] or "",
                    domain=r["domain"] or "career",
                    notes=r["notes"] or "",
                    consultation_payload_json=r["consultation_payload_json"] or "{}",
                    is_synced=bool(r["is_synced"]),
                    created_at_iso=r["created_at_iso"],
                    updated_at_iso=r["updated_at_iso"],
                )
                for r in rows
            ]

    def mark_charts_synced(self, chart_ids: List[str]) -> int:
        """Marks a batch of charts as successfully synchronized to cloud."""
        if not chart_ids:
            return 0
        with self._connection() as conn:
            cur = conn.cursor()
            placeholders = ",".join("?" for _ in chart_ids)
            cur.execute(
                f"UPDATE offline_charts SET is_synced = 1 WHERE chart_id IN ({placeholders})",
                chart_ids,
            )
            conn.commit()
            return cur.rowcount

    def get_pending_sync_queue(self) -> List[OfflineChartRecord]:
        """Returns all un-synced charts ready for cloud sync when online."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM offline_charts WHERE is_synced = 0 ORDER BY updated_at_iso ASC"
            ).fetchall()
            return [
                OfflineChartRecord(
                    chart_id=r["chart_id"],
                    native_name=r["native_name"],
                    birth_date_iso=r["birth_date_iso"],
                    latitude=r["latitude"],
                    longitude=r["longitude"],
                    city_name=r["city_name"] or "",
                    domain=r["domain"] or "career",
                    notes=r["notes"] or "",
                    consultation_payload_json=r["consultation_payload_json"] or "{}",
                    is_synced=False,
                    created_at_iso=r["created_at_iso"],
                    updated_at_iso=r["updated_at_iso"],
                )
                for r in rows
            ]
