"""
AstroOS — Local-First Mobile Sync Router (Module 21, Priority 6)

REST endpoints for:
  POST /api/v1/sync/pairing/generate
  POST /api/v1/sync/pairing/verify
  POST /api/v1/sync/pull
  POST /api/v1/sync/push
  GET  /api/v1/sync/devices
  DELETE /api/v1/sync/devices/{device_id}
  GET  /api/v1/sync/status
  GET  /api/v1/sync/conflicts
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from apps.api.domain.sync import PAIRING_TTL_SECONDS, PROTOCOL_VERSION
from apps.api.schemas.sync import (
    PairedDeviceListResponse,
    PairedDeviceResponse,
    PairingGenerateRequest,
    PairingGenerateResponse,
    PairingVerifyRequest,
    PairingVerifyResponse,
    SyncConflictItemResponse,
    SyncConflictListResponse,
    SyncEntityPayload,
    SyncPullRequest,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
    SyncStatusResponse,
)
from apps.api.services.mobile_sync_service import MobileSyncService

router = APIRouter(prefix="/sync", tags=["Mobile Sync"])


@router.post("/pairing/generate", response_model=PairingGenerateResponse)
async def generate_pairing_session(
    body: PairingGenerateRequest,
) -> PairingGenerateResponse:
    """
    Initiates an ephemeral single-use LAN pairing session.
    Returns 6-digit PIN and encoded QR code connection payload.
    """
    service = MobileSyncService.get_instance()
    session = service.generate_pairing_session(
        lan_host=body.lan_host,
        lan_port=body.lan_port,
    )

    qr_data = {
        "protocol": "astroos-sync",
        "version": PROTOCOL_VERSION,
        "session_id": session.session_id,
        "ephemeral_secret": session.ephemeral_secret,
        "host": session.lan_host,
        "port": session.lan_port,
        "expires_at": session.expires_at.isoformat(),
    }

    return PairingGenerateResponse(
        session_id=session.session_id,
        pin_code=session.pin_code,
        qr_payload=json.dumps(qr_data),
        expires_at_iso=session.expires_at.isoformat(),
        ttl_seconds=PAIRING_TTL_SECONDS,
        protocol_version=PROTOCOL_VERSION,
    )


@router.post("/pairing/verify", response_model=PairingVerifyResponse)
async def verify_pairing_session(
    body: PairingVerifyRequest,
) -> PairingVerifyResponse:
    """
    Verifies pairing PIN or ephemeral secret over local network.
    Issues permanent paired device credentials and revokes pairing session.
    """
    service = MobileSyncService.get_instance()
    device, secret_token, error_msg = service.verify_pairing(
        session_id=body.session_id,
        ephemeral_secret=body.ephemeral_secret,
        pin_code=body.pin_code,
        device_name=body.device_name,
        device_type=body.device_type,
    )

    if error_msg or not device or not secret_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg or "Pairing verification failed.",
        )

    return PairingVerifyResponse(
        device_id=device.device_id,
        device_secret_token=secret_token,
        protocol_version=device.protocol_version,
        paired_at_iso=device.paired_at.isoformat(),
    )


@router.post("/pull", response_model=SyncPullResponse)
async def pull_sync_entities(
    body: SyncPullRequest,
) -> SyncPullResponse:
    """
    Pulls modified entities and tombstones since last known cursor.
    """
    service = MobileSyncService.get_instance()
    if not service.authenticate_device(body.device_id, body.device_secret_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized or revoked device credentials.",
        )

    deltas, server_cursor = service.pull_deltas(body.device_id, body.last_known_cursor)

    entity_schemas = [
        SyncEntityPayload(
            entity_id=d.entity_id,
            entity_type=d.entity_type.value,
            payload=d.payload,
            revision=d.revision,
            originating_device_id=d.originating_device_id,
            created_at_iso=d.created_at.isoformat(),
            updated_at_iso=d.updated_at.isoformat(),
            deleted_at_iso=d.deleted_at.isoformat() if d.deleted_at else None,
            payload_hash=d.payload_hash,
            schema_version=d.schema_version,
            server_cursor=d.server_cursor,
        )
        for d in deltas
    ]

    return SyncPullResponse(
        entities=entity_schemas,
        new_cursor=server_cursor,
        has_more=False,
        server_cursor_timestamp_iso=datetime.now(timezone.utc).isoformat(),
        protocol_version=PROTOCOL_VERSION,
    )


@router.post("/push", response_model=SyncPushResponse)
async def push_sync_mutations(
    body: SyncPushRequest,
) -> SyncPushResponse:
    """
    Pushes client entity mutations with SHA-256 integrity checks and conflict resolution.
    """
    service = MobileSyncService.get_instance()
    if not service.authenticate_device(body.device_id, body.device_secret_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized or revoked device credentials.",
        )

    mutations_dicts = [m.model_dump() for m in body.mutations]
    accepted, rejected, conflicts, new_cursor = service.push_mutations(
        device_id=body.device_id,
        mutations=mutations_dicts,
    )

    conflict_schemas = [
        SyncConflictItemResponse(
            conflict_id=c.conflict_id,
            entity_id=c.entity_id,
            entity_type=c.entity_type,
            winning_revision=c.winning_revision,
            losing_revision=c.losing_revision,
            winning_device_id=c.winning_device_id,
            losing_device_id=c.losing_device_id,
            winning_payload_hash=c.winning_payload_hash,
            losing_payload_hash=c.losing_payload_hash,
            resolution_reason=c.resolution_reason,
            created_at_iso=c.created_at.isoformat(),
        )
        for c in conflicts
    ]

    return SyncPushResponse(
        accepted_mutation_ids=accepted,
        rejected_mutation_ids=rejected,
        conflicts=conflict_schemas,
        new_server_cursor=new_cursor,
        protocol_version=PROTOCOL_VERSION,
    )


@router.get("/devices", response_model=PairedDeviceListResponse)
async def list_paired_devices() -> PairedDeviceListResponse:
    """
    Lists all authorized mobile and peer devices.
    """
    service = MobileSyncService.get_instance()
    devices = service.list_devices()
    device_schemas = [
        PairedDeviceResponse(
            device_id=d.device_id,
            device_name=d.device_name,
            device_type=d.device_type,
            paired_at_iso=d.paired_at.isoformat(),
            last_seen_at_iso=d.last_seen_at.isoformat(),
            last_sync_at_iso=d.last_sync_at.isoformat() if d.last_sync_at else None,
            revoked_at_iso=d.revoked_at.isoformat() if d.revoked_at else None,
            is_active=d.is_active,
            protocol_version=d.protocol_version,
        )
        for d in devices
    ]
    total_active = sum(1 for d in devices if d.is_active)
    return PairedDeviceListResponse(devices=device_schemas, total_active=total_active)


@router.delete("/devices/{device_id}")
async def revoke_paired_device(device_id: str) -> dict[str, Any]:
    """
    Revokes authorization for a paired mobile device.
    """
    service = MobileSyncService.get_instance()
    success = service.revoke_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found.")
    return {"status": "success", "revoked_device_id": device_id}


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status() -> SyncStatusResponse:
    """
    Returns server synchronization health, ledger version, and entity counts.
    """
    service = MobileSyncService.get_instance()
    report = service.get_sync_status()
    return SyncStatusResponse(
        server_cursor=report.server_cursor,
        total_entities=report.total_entities,
        total_tombstones=report.total_tombstones,
        active_paired_devices=report.active_paired_devices,
        total_conflicts_recorded=report.total_conflicts_recorded,
        protocol_version=report.protocol_version,
        supported_entity_types=report.supported_entity_types,
    )


@router.get("/conflicts", response_model=SyncConflictListResponse)
async def list_conflict_records() -> SyncConflictListResponse:
    """
    Returns immutable conflict audit records for inspection.
    """
    service = MobileSyncService.get_instance()
    records = service.get_conflict_ledger()
    conflict_schemas = [
        SyncConflictItemResponse(
            conflict_id=c.conflict_id,
            entity_id=c.entity_id,
            entity_type=c.entity_type,
            winning_revision=c.winning_revision,
            losing_revision=c.losing_revision,
            winning_device_id=c.winning_device_id,
            losing_device_id=c.losing_device_id,
            winning_payload_hash=c.winning_payload_hash,
            losing_payload_hash=c.losing_payload_hash,
            resolution_reason=c.resolution_reason,
            created_at_iso=c.created_at.isoformat(),
        )
        for c in records
    ]
    return SyncConflictListResponse(conflicts=conflict_schemas, total_count=len(conflict_schemas))
