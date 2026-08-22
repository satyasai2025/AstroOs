"""
AstroOS — Local-First Mobile Sync Domain Models (Module 21, Priority 6)

Pure domain dataclasses for:
1. Ephemeral LAN Pairing Session & QR Handshake
2. Persistent Paired Device Identity & Revocation
3. Canonical Sync Entity Registry (10 Approved Entities)
4. Durable Sync Entity Record with Logical Revision & Tombstones
5. Immutable Conflict Ledger & Audit Trail
6. Monotonic Sync Cursor / Checkpoints
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


PROTOCOL_VERSION = "2.0"
DEFAULT_SCHEMA_VERSION = "1.0"
PAIRING_TTL_SECONDS = 180  # 3 minutes


class CanonicalSyncEntityType(str, Enum):
    BIRTH_CHART = "birth_chart"
    RECTIFICATION_RECORD = "rectification_record"
    RESEARCH_PROJECT = "research_project"
    RESEARCH_DATASET = "research_dataset"
    RESEARCH_HYPOTHESIS = "research_hypothesis"
    ASTROLOGICAL_NOTE = "astrological_note"
    ANNOTATION = "annotation"
    EVENT = "event"
    USER_PREFERENCE = "user_preference"
    CUSTOM_AYANAMSA = "custom_ayanamsa"


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Computes deterministic SHA-256 checksum over canonical JSON payload."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass
class PairingSession:
    """
    Ephemeral single-use pairing session initiated by Desktop.
    Carries short TTL and rate-limited PIN code verification.
    """
    session_id: str
    ephemeral_secret: str
    pin_code: str
    expires_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    failed_pin_attempts: int = 0
    is_claimed: bool = False
    lan_host: str = "127.0.0.1"
    lan_port: int = 8000
    protocol_version: str = PROTOCOL_VERSION

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_locked(self) -> bool:
        return self.failed_pin_attempts >= 3


@dataclass
class PairedDevice:
    """
    Durable record of an authorized mobile or peer device on the local network.
    """
    device_id: str
    device_name: str
    device_type: str  # "ios" | "android" | "tablet" | "desktop_peer"
    device_token_hash: str  # SHA-256 hash of device secret credential
    paired_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_sync_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    protocol_version: str = PROTOCOL_VERSION

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


@dataclass
class SyncEntityRecord:
    """
    Durable entity record in the server synchronization store.
    """
    entity_id: str
    entity_type: CanonicalSyncEntityType
    payload: dict[str, Any]
    revision: int
    originating_device_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None  # Tombstone state
    payload_hash: str = ""
    schema_version: str = DEFAULT_SCHEMA_VERSION
    server_cursor: int = 0

    def __post_init__(self):
        if not self.payload_hash:
            object.__setattr__(self, "payload_hash", compute_payload_hash(self.payload))

    @property
    def is_tombstone(self) -> bool:
        return self.deleted_at is not None


@dataclass(frozen=True)
class SyncConflictRecord:
    """
    Immutable audit ledger entry recording a resolved mutation conflict.
    Preserves the losing version for non-destructive inspection.
    """
    conflict_id: str
    entity_id: str
    entity_type: str
    winning_revision: int
    losing_revision: int
    winning_device_id: str
    losing_device_id: str
    winning_payload_hash: str
    losing_payload_hash: str
    losing_payload: dict[str, Any]
    resolution_reason: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class SyncStatusReport:
    """Server synchronization health and ledger summary."""
    server_cursor: int
    total_entities: int
    total_tombstones: int
    active_paired_devices: int
    total_conflicts_recorded: int
    protocol_version: str
    supported_entity_types: list[str]
