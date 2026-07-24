"""
WebSocket Router — Minimal Working Version
Provides peer-to-peer WebSocket sync layer for local-network collaboration.
"""

import uuid
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, status
from fastapi.responses import JSONResponse

router = APIRouter()

# In-memory session registry
class Session:
    def __init__(self, session_id: str, host_peer_id: str, host_name: str):
        self.session_id = session_id
        self.host_peer_id = host_peer_id
        self.host_name = host_name
        self.peers: dict[str, dict] = {}  # peer_id -> {connected: bool, name: str, websocket: WebSocket}

# Global registry
session_registry: dict[str, Session] = {}
active_connections: dict[str, dict[str, WebSocket]] = {}


@router.websocket("/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, peer_id: Optional[str] = None):
    """WebSocket endpoint for collaboration sessions."""
    await websocket.accept()

    # Get or create session
    session = session_registry.get(session_id)
    if session is None:
        host_peer_id = getattr(Request, "host_peer_id", "default-host") or "default-host"
        host_name = getattr(Request, "host_name", "Unknown Host") or "Unknown Host"
        session = Session(session_id, host_peer_id, host_name)
        session_registry[session_id] = session

    # Register peer
    if peer_id is None:
        peer_id = f"peer-{uuid.uuid4().hex[:8]}"
    session.peers[peer_id] = {"connected": True, "name": f"peer-{peer_id}", "websocket": websocket}
    active_connections.setdefault(session_id, {})[peer_id] = websocket

    # Send welcome message
    await websocket.send_json({
        "type": "welcome",
        "session_id": session_id,
        "host_peer_id": session.host_peer_id,
        "host_name": session.host_name,
        "peer_id": peer_id,
        "peers": {pid: info["name"] for pid, info in session.peers.items()},
    })

    # Main message loop
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            # TODO: Handle "operation" messages with OT engine
    except WebSocketDisconnect:
        pass
    finally:
        # Cleanup on disconnect
        session.peers.pop(peer_id, None)
        active_connections.get(session_id, {}).pop(peer_id, None)
        # Optional: broadcast disconnect to other peers