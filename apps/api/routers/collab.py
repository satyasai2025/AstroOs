"""
AstroOS — RTCollab Session Discovery Router (Phase IV, ADR-RTC-001)

Endpoints
---------
POST   /collab/sessions              — create a session and advertise it on the LAN
DELETE /collab/sessions/{session_id} — stop advertising a session
GET    /collab/sessions/discovered   — list sessions discovered via mDNS

WebSocket connect/sync itself lives in apps/api/routers/ws.py; this router
only covers Milestone 1 (mDNS session discovery) of the ADR.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from apps.api.routers.ws import session_registry, Session
from apps.api.schemas.collab import (
    AdvertiseSessionRequest,
    AdvertiseSessionResponse,
    DiscoveredSessionListResponse,
    DiscoveredSessionResponse,
)
from apps.api.services.collab_discovery import get_discovery

router = APIRouter(prefix="/collab", tags=["Collaboration"])


@router.post(
    "/sessions",
    response_model=AdvertiseSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a collaboration session and advertise it on the LAN",
)
async def create_session(payload: AdvertiseSessionRequest) -> AdvertiseSessionResponse:
    session_id = uuid.uuid4().hex[:12]
    host_peer_id = f"peer-{uuid.uuid4().hex[:8]}"
    session_registry[session_id] = Session(session_id, host_peer_id, payload.host_name)

    discovery = get_discovery()
    await discovery.advertise(session_id, payload.host_name, payload.port)

    return AdvertiseSessionResponse(
        session_id=session_id, host_name=payload.host_name, port=payload.port
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Stop advertising a collaboration session",
)
async def stop_session(session_id: str) -> None:
    if session_id not in session_registry:
        raise HTTPException(status_code=404, detail="Session not found")
    await get_discovery().stop_advertising(session_id)
    session_registry.pop(session_id, None)


@router.get(
    "/sessions/discovered",
    response_model=DiscoveredSessionListResponse,
    summary="List collaboration sessions discovered on the LAN via mDNS",
)
async def list_discovered_sessions() -> DiscoveredSessionListResponse:
    sessions = get_discovery().list_discovered()
    return DiscoveredSessionListResponse(
        sessions=[
            DiscoveredSessionResponse(
                session_id=s.session_id,
                host_name=s.host_name,
                address=s.address,
                port=s.port,
            )
            for s in sessions
        ]
    )
