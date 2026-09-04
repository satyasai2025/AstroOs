"""
AstroOS — Local-First Mobile Sync Schemas (Module 21, Priority 6)

Pydantic models for:
  POST /api/v1/sync/pairing/generate
  POST /api/v1/sync/pairing/verify
  POST /api/v1/sync/pull
  POST /api/v1/sync/push
  GET /api/v1/sync/devices
  DELETE /api/v1/sync/devices/{device_id}
  GET /api/v1/sync/status
  GET /api/v1/sync/conflicts
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Pairing Schemas ───────────────────────────────────────────────────────────

class PairingGenerateRequest(BaseModel):
    lan_host: Optional[str] = None
    lan_port: Optional[int] = None


class PairingGenerateResponse(BaseModel):
    session_id: str
    pin_code: str
    qr_payload: str
    expires_at_iso: str
    ttl_seconds: int
    protocol_version: str


class PairingVerifyRequest(BaseModel):
    session_id: str
    ephemeral_secret: Optional[str] = None
    pin_code: Optional[str] = None
    device_name: str
    device_type: str = "mobile"  # "ios" | "android" | "tablet" | "desktop_peer"


class PairingVerifyResponse(BaseModel):
    device_id: str
    device_secret_token: str
    protocol_version: str
    paired_at_iso: str


# ── Device Schemas ────────────────────────────────────────────────────────────

class PairedDeviceResponse(BaseModel):
    device_id: str
    device_name: str
    device_type: str
    paired_at_iso: str
    last_seen_at_iso: str
    last_sync_at_iso: Optional[str] = None
    revoked_at_iso: Optional[str] = None
    is_active: bool
    protocol_version: str


class PairedDeviceListResponse(BaseModel):
    devices: list[PairedDeviceResponse]
    total_active: int


# ── Sync Entity & Mutation Schemas ────────────────────────────────────────────

class SyncEntityPayload(BaseModel):
    entity_id: str
    entity_type: str
    payload: dict[str, Any]
    revision: int
    originating_device_id: str
    created_at_iso: str
    updated_at_iso: str
    deleted_at_iso: Optional[str] = None
    payload_hash: str
    schema_version: str = "1.0"
    server_cursor: int = 0


class SyncPullRequest(BaseModel):
    device_id: str
    device_secret_token: str
    last_known_cursor: int = 0
    protocol_version: str = "2.0"


class SyncPullResponse(BaseModel):
    entities: list[SyncEntityPayload]
    new_cursor: int
    has_more: bool
    server_cursor_timestamp_iso: str
    protocol_version: str


class SyncMutationItem(BaseModel):
    mutation_id: str
    entity_id: str
    entity_type: str
    payload: dict[str, Any]
    revision: int
    originating_device_id: str
    created_at_iso: str
    updated_at_iso: str
    deleted_at_iso: Optional[str] = None
    payload_hash: str
    schema_version: str = "1.0"


class SyncPushRequest(BaseModel):
    device_id: str
    device_secret_token: str
    mutations: list[SyncMutationItem]
    protocol_version: str = "2.0"


class SyncConflictItemResponse(BaseModel):
    conflict_id: str
    entity_id: str
    entity_type: str
    winning_revision: int
    losing_revision: int
    winning_device_id: str
    losing_device_id: str
    winning_payload_hash: str
    losing_payload_hash: str
    resolution_reason: str
    created_at_iso: str


class SyncPushResponse(BaseModel):
    accepted_mutation_ids: list[str]
    rejected_mutation_ids: list[str]
    conflicts: list[SyncConflictItemResponse]
    new_server_cursor: int
    protocol_version: str


# ── Status & Conflict Schemas ─────────────────────────────────────────────────

class SyncStatusResponse(BaseModel):
    server_cursor: int
    total_entities: int
    total_tombstones: int
    active_paired_devices: int
    total_conflicts_recorded: int
    protocol_version: str
    supported_entity_types: list[str]


class SyncConflictListResponse(BaseModel):
    conflicts: list[SyncConflictItemResponse]
    total_count: int
