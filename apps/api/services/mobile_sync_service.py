"""
AstroOS — Local-First Mobile Sync Service (Module 21, Priority 6)

Core orchestration service managing:
1. Ephemeral LAN Pairing & QR Token Handshake
2. Device Identity & Revocation
3. Bidirectional Pull/Push Synchronizations with Checkpoints & Checksums
4. Idempotency Tracking & Conflict Ledger Archiving
"""

from __future__ import annotations

import hashlib
import json
import random
import secrets
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from apps.api.domain.sync import (
    PAIRING_TTL_SECONDS,
    PROTOCOL_VERSION,
    CanonicalSyncEntityType,
    PairedDevice,
    PairingSession,
    SyncConflictRecord,
    SyncEntityRecord,
    SyncStatusReport,
    compute_payload_hash,
)
from apps.api.services.sync_conflict_engine import SyncConflictResolutionEngine


class MobileSyncService:
    """
    Thread-safe in-memory synchronized store and orchestrator.
    Persists durable sync entities and handles pairing handshakes.
    """
    _instance: Optional[MobileSyncService] = None
    _lock = threading.Lock()

    def __init__(self):
        self._pairing_sessions: dict[str, PairingSession] = {}
        self._paired_devices: dict[str, PairedDevice] = {}
        self._entity_store: dict[str, SyncEntityRecord] = {}
        self._conflict_ledger: list[SyncConflictRecord] = []
        self._idempotency_cache: dict[str, dict[str, Any]] = {}
        self._server_cursor_seq: int = 0
        self._mutex = threading.RLock()
        self._seed_default_test_data()

    @classmethod
    def get_instance(cls) -> MobileSyncService:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── 1. Pairing Handshake ──────────────────────────────────────────────────

    def generate_pairing_session(
        self,
        lan_host: Optional[str] = None,
        lan_port: Optional[int] = None,
    ) -> PairingSession:
        with self._mutex:
            session_id = str(uuid.uuid4())
            secret = secrets.token_urlsafe(32)
            pin = f"{random.randint(100000, 999999):06d}"
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=PAIRING_TTL_SECONDS)
            host = lan_host or "127.0.0.1"
            port = lan_port or 8000

            session = PairingSession(
                session_id=session_id,
                ephemeral_secret=secret,
                pin_code=pin,
                expires_at=expires_at,
                lan_host=host,
                lan_port=port,
            )
            self._pairing_sessions[session_id] = session
            return session

    def verify_pairing(
        self,
        session_id: str,
        ephemeral_secret: Optional[str] = None,
        pin_code: Optional[str] = None,
        device_name: str = "Mobile Client",
        device_type: str = "mobile",
    ) -> tuple[Optional[PairedDevice], Optional[str], Optional[str]]:
        """
        Verifies pairing session and issues persistent device identity.
        Returns: (device, secret_token, error_message)
        """
        with self._mutex:
            session = self._pairing_sessions.get(session_id)
            if not session:
                return None, None, "Invalid or expired pairing session ID."

            if session.is_claimed:
                return None, None, "Pairing session has already been claimed (Single-Use Violation)."

            if session.is_expired:
                del self._pairing_sessions[session_id]
                return None, None, "Pairing session has expired."

            if session.is_locked:
                return None, None, "Pairing session locked due to excessive failed PIN attempts (Rate Limited)."

            # Match secret or PIN
            valid_secret = ephemeral_secret and secrets.compare_digest(session.ephemeral_secret, ephemeral_secret)
            valid_pin = pin_code and secrets.compare_digest(session.pin_code, pin_code)

            if not (valid_secret or valid_pin):
                session.failed_pin_attempts += 1
                return None, None, f"Invalid pairing credentials. {3 - session.failed_pin_attempts} attempt(s) remaining."

            # Mark claimed immediately
            session.is_claimed = True

            # Generate high-entropy permanent device secret token
            raw_device_token = secrets.token_hex(32)
            token_hash = hashlib.sha256(raw_device_token.encode("utf-8")).hexdigest()
            device_id = f"dev_{uuid.uuid4().hex[:12]}"

            device = PairedDevice(
                device_id=device_id,
                device_name=device_name,
                device_type=device_type,
                device_token_hash=token_hash,
            )
            self._paired_devices[device_id] = device
            return device, raw_device_token, None

    # ── 2. Device Identity & Authentication ───────────────────────────────────

    def authenticate_device(self, device_id: str, device_secret_token: str) -> bool:
        with self._mutex:
            device = self._paired_devices.get(device_id)
            if not device or not device.is_active:
                return False

            claimed_hash = hashlib.sha256(device_secret_token.encode("utf-8")).hexdigest()
            if secrets.compare_digest(device.device_token_hash, claimed_hash):
                device.last_seen_at = datetime.now(timezone.utc)
                return True
            return False

    def list_devices(self) -> list[PairedDevice]:
        with self._mutex:
            return list(self._paired_devices.values())

    def revoke_device(self, device_id: str) -> bool:
        with self._mutex:
            device = self._paired_devices.get(device_id)
            if device:
                device.revoked_at = datetime.now(timezone.utc)
                return True
            return False

    # ── 3. Pull Synchronizations (Delta Stream) ───────────────────────────────

    def pull_deltas(self, device_id: str, last_known_cursor: int = 0) -> tuple[list[SyncEntityRecord], int]:
        with self._mutex:
            device = self._paired_devices.get(device_id)
            if device:
                device.last_sync_at = datetime.now(timezone.utc)

            # Filter entities where server_cursor > last_known_cursor
            deltas = [
                record for record in self._entity_store.values()
                if record.server_cursor > last_known_cursor
            ]
            deltas.sort(key=lambda r: r.server_cursor)
            return deltas, self._server_cursor_seq

    # ── 4. Push Mutations (Idempotent + Conflict Resolution) ──────────────────

    def push_mutations(
        self,
        device_id: str,
        mutations: list[dict[str, Any]],
    ) -> tuple[list[str], list[str], list[SyncConflictRecord], int]:
        with self._mutex:
            accepted_ids: list[str] = []
            rejected_ids: list[str] = []
            conflicts_generated: list[SyncConflictRecord] = []

            for mut in mutations:
                mut_id = mut.get("mutation_id", "")
                
                # Idempotency check: If mutation_id was already processed, replay cached result
                if mut_id in self._idempotency_cache:
                    cached = self._idempotency_cache[mut_id]
                    if cached["status"] == "accepted":
                        accepted_ids.append(mut_id)
                    else:
                        rejected_ids.append(mut_id)
                    continue

                entity_id = mut.get("entity_id", "")
                entity_type_str = mut.get("entity_type", "")
                payload = mut.get("payload", {})
                revision = int(mut.get("revision", 1))
                claimed_hash = mut.get("payload_hash", "")
                created_iso = mut.get("created_at_iso", datetime.now(timezone.utc).isoformat())
                updated_iso = mut.get("updated_at_iso", datetime.now(timezone.utc).isoformat())
                deleted_iso = mut.get("deleted_at_iso")
                schema_ver = mut.get("schema_version", "1.0")

                # Validate Entity Type
                canonical_type = SyncConflictResolutionEngine.validate_entity_type(entity_type_str)
                if not canonical_type:
                    rejected_ids.append(mut_id)
                    self._idempotency_cache[mut_id] = {"status": "rejected", "reason": f"Unauthorized entity type '{entity_type_str}'"}
                    continue

                # Verify SHA-256 Checksum
                if not SyncConflictResolutionEngine.verify_payload_integrity(payload, claimed_hash):
                    rejected_ids.append(mut_id)
                    self._idempotency_cache[mut_id] = {"status": "rejected", "reason": "SHA-256 Checksum mismatch"}
                    continue

                created_dt = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
                updated_dt = datetime.fromisoformat(updated_iso.replace("Z", "+00:00"))
                deleted_dt = datetime.fromisoformat(deleted_iso.replace("Z", "+00:00")) if deleted_iso else None

                incoming_record = SyncEntityRecord(
                    entity_id=entity_id,
                    entity_type=canonical_type,
                    payload=payload,
                    revision=revision,
                    originating_device_id=device_id,
                    created_at=created_dt,
                    updated_at=updated_dt,
                    deleted_at=deleted_dt,
                    payload_hash=claimed_hash,
                    schema_version=schema_ver,
                )

                # Check if entity already exists on server
                existing_record = self._entity_store.get(entity_id)

                if existing_record is None:
                    # New Entity -> Directly accept
                    self._server_cursor_seq += 1
                    object.__setattr__(incoming_record, "server_cursor", self._server_cursor_seq)
                    self._entity_store[entity_id] = incoming_record
                    accepted_ids.append(mut_id)
                    self._idempotency_cache[mut_id] = {"status": "accepted"}
                else:
                    # Conflict Resolution
                    incoming_wins, conflict_rec, reason = SyncConflictResolutionEngine.resolve_conflict(
                        existing_record, incoming_record
                    )

                    if conflict_rec:
                        self._conflict_ledger.append(conflict_rec)
                        conflicts_generated.append(conflict_rec)

                    if incoming_wins:
                        self._server_cursor_seq += 1
                        object.__setattr__(incoming_record, "server_cursor", self._server_cursor_seq)
                        self._entity_store[entity_id] = incoming_record
                        accepted_ids.append(mut_id)
                        self._idempotency_cache[mut_id] = {"status": "accepted", "conflict": True}
                    else:
                        # Existing record won -> incoming mutation rejected/subsumed
                        accepted_ids.append(mut_id)  # Marked processed to clear client queue
                        self._idempotency_cache[mut_id] = {"status": "accepted", "conflict": True, "winner": "existing"}

            device = self._paired_devices.get(device_id)
            if device:
                device.last_sync_at = datetime.now(timezone.utc)

            return accepted_ids, rejected_ids, conflicts_generated, self._server_cursor_seq

    # ── 5. Status & Ledger Queries ────────────────────────────────────────────

    def get_conflict_ledger(self) -> list[SyncConflictRecord]:
        with self._mutex:
            return list(self._conflict_ledger)

    def get_sync_status(self) -> SyncStatusReport:
        with self._mutex:
            total_tombstones = sum(1 for e in self._entity_store.values() if e.is_tombstone)
            active_devices = sum(1 for d in self._paired_devices.values() if d.is_active)
            return SyncStatusReport(
                server_cursor=self._server_cursor_seq,
                total_entities=len(self._entity_store),
                total_tombstones=total_tombstones,
                active_paired_devices=active_devices,
                total_conflicts_recorded=len(self._conflict_ledger),
                protocol_version=PROTOCOL_VERSION,
                supported_entity_types=[t.value for t in CanonicalSyncEntityType],
            )

    def _seed_default_test_data(self):
        """Pre-populates a canonical birth chart so initial pull yields data."""
        self._server_cursor_seq += 1
        default_chart = {
            "name": "Dr. B.V. Raman (Canonical)",
            "birth_date": "1912-08-08",
            "birth_time": "19:35",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "ayanamsa": "raman",
        }
        chart_id = "chart_canonical_001"
        rec = SyncEntityRecord(
            entity_id=chart_id,
            entity_type=CanonicalSyncEntityType.BIRTH_CHART,
            payload=default_chart,
            revision=1,
            originating_device_id="desktop_primary",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            server_cursor=self._server_cursor_seq,
        )
        self._entity_store[chart_id] = rec
