"""
WebSocket Router — RTCollab
Provides peer-to-peer WebSocket sync layer for local-network collaboration.
"""

import asyncio
import threading
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from prometheus_client import Counter, Gauge

from apps.api.services.collab_crypto import (
    decrypt_json,
    encrypt_json,
    generate_session_key,
    is_encrypted_envelope,
    key_to_b64,
)
from apps.api.services.collab_discovery import get_discovery
from apps.api.services.ot_engine import (
    Operation,
    get_ot_engine,
    clear_session_engine,
)
from apps.api.services.worker_pool import JobPriority

router = APIRouter()

# ── Metrics (observability/SLO.md — WebSocket connection health SLI) ─────────
rtcollab_active_connections = Gauge(
    "rtcollab_active_connections", "Currently connected RTCollab WS peers"
)
rtcollab_operations_total = Counter(
    "rtcollab_operations_total", "RTCollab operations by outcome",
    ["outcome"],  # applied | quota_rejected | error
)

# Sandbox per-device CPU quota (ADR-RTC-001, Milestone 4): each peer may have
# at most this many operations in flight on the shared "cpu" WorkerPool at
# once. Concurrent OT application still happens on that pool (so it benefits
# from its autoscaling/backpressure), but no single device can flood it.
MAX_PENDING_OPS_PER_PEER = 5
OPERATION_TIMEOUT_SECONDS = 5.0

_peer_job_counts: dict[str, int] = {}
_peer_job_counts_lock = threading.Lock()


def _try_acquire_quota(peer_id: str) -> bool:
    with _peer_job_counts_lock:
        count = _peer_job_counts.get(peer_id, 0)
        if count >= MAX_PENDING_OPS_PER_PEER:
            return False
        _peer_job_counts[peer_id] = count + 1
        return True


def _release_quota(peer_id: str) -> None:
    with _peer_job_counts_lock:
        if peer_id in _peer_job_counts:
            _peer_job_counts[peer_id] = max(0, _peer_job_counts[peer_id] - 1)


def _clear_quota(peer_id: str) -> None:
    with _peer_job_counts_lock:
        _peer_job_counts.pop(peer_id, None)


async def _apply_operation_quota_checked(
    websocket: WebSocket, ot_engine, op: Operation, peer_id: str
) -> Operation:
    """
    Apply an OT operation on the shared "cpu" WorkerPool so it benefits from
    the pool's autoscaling/retry machinery instead of running inline on the
    event loop. Falls back to inline application if no pool is configured
    (e.g. minimal test apps that skip the lifespan startup).

    Bridges the worker thread back to this coroutine with an asyncio.Future
    completed via `call_soon_threadsafe` — not a `threading.Event` awaited
    through `asyncio.to_thread`, which burns an extra thread from the loop's
    default executor per operation and can stall under load.
    """
    manager = getattr(websocket.app.state, "worker_pool_manager", None)
    if manager is None:
        return ot_engine.apply(op, peer_id)

    cpu_pool = manager.pool("cpu")
    loop = asyncio.get_running_loop()
    future: "asyncio.Future[Operation]" = loop.create_future()

    def _complete(exc: Optional[BaseException], result: Optional[Operation]) -> None:
        if future.done():
            return
        if exc is not None:
            future.set_exception(exc)
        else:
            future.set_result(result)

    def _job(job):
        try:
            result = ot_engine.apply(op, peer_id)
        except Exception as exc:  # surfaced on the awaiting coroutine below
            loop.call_soon_threadsafe(_complete, exc, None)
        else:
            loop.call_soon_threadsafe(_complete, None, result)

    cpu_pool.submit(
        _job, priority=JobPriority.INTERACTIVE, job_id=f"rtcollab-op-{uuid.uuid4().hex}"
    )

    try:
        return await asyncio.wait_for(future, timeout=OPERATION_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise RuntimeError(
            "CPU quota exceeded: operation timed out waiting for worker pool capacity"
        )


# In-memory session registry
class Session:
    def __init__(self, session_id: str, host_peer_id: str, host_name: str):
        self.session_id = session_id
        self.host_peer_id = host_peer_id
        self.host_name = host_name
        self.peers: dict[str, dict] = {}  # peer_id -> {connected: bool, name: str, websocket: WebSocket}
        self.document: dict = {}
        # AES-256-GCM key (ADR-RTC-001, Milestone 5): generated once per
        # session and handed to each peer in the plaintext "welcome"
        # message; every message after that is sealed with it.
        self.encryption_key: bytes = generate_session_key()


# Global registry
session_registry: dict[str, Session] = {}
active_connections: dict[str, dict[str, WebSocket]] = {}


async def _send(websocket: WebSocket, session: Session, message: dict) -> None:
    await websocket.send_json(encrypt_json(session.encryption_key, message))


async def _broadcast(session: Session, message: dict, exclude_peer_id: Optional[str] = None):
    envelope = encrypt_json(session.encryption_key, message)
    for pid, ws in active_connections.get(session.session_id, {}).items():
        if pid == exclude_peer_id:
            continue
        try:
            await ws.send_json(envelope)
        except Exception:
            pass


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

    ot_engine = get_ot_engine(session_id)

    # Register peer
    if peer_id is None:
        peer_id = f"peer-{uuid.uuid4().hex[:8]}"
    session.peers[peer_id] = {"connected": True, "name": f"peer-{peer_id}", "websocket": websocket}
    active_connections.setdefault(session_id, {})[peer_id] = websocket
    rtcollab_active_connections.inc()

    # Send welcome message — the only message ever sent unencrypted, since
    # it's how the peer receives the session's AES-256-GCM key in the first
    # place. Everything after this is sealed with that key.
    await websocket.send_json({
        "type": "welcome",
        "session_id": session_id,
        "host_peer_id": session.host_peer_id,
        "host_name": session.host_name,
        "peer_id": peer_id,
        "peers": {pid: info["name"] for pid, info in session.peers.items()},
        "document": session.document,
        "encryption_key": key_to_b64(session.encryption_key),
    })
    await _broadcast(
        session,
        {"type": "presence", "peer_id": peer_id, "status": "joined"},
        exclude_peer_id=peer_id,
    )

    # Main message loop
    try:
        while True:
            raw = await websocket.receive_json()
            if is_encrypted_envelope(raw):
                try:
                    data = decrypt_json(session.encryption_key, raw)
                except Exception:
                    await websocket.send_json({"type": "error", "detail": "decryption failed"})
                    continue
            else:
                data = raw
            msg_type = data.get("type")

            if msg_type == "ping":
                await _send(websocket, session, {"type": "pong"})

            elif msg_type == "operation":
                try:
                    op = Operation.from_dict(data["operation"])
                except (KeyError, ValueError) as exc:
                    await _send(websocket, session, {"type": "error", "detail": str(exc)})
                    continue

                if not _try_acquire_quota(peer_id):
                    rtcollab_operations_total.labels(outcome="quota_rejected").inc()
                    await _send(websocket, session, {
                        "type": "error",
                        "detail": "CPU quota exceeded: too many operations in flight for this device",
                    })
                    continue

                try:
                    applied = await _apply_operation_quota_checked(websocket, ot_engine, op, peer_id)
                except Exception as exc:
                    rtcollab_operations_total.labels(outcome="error").inc()
                    await _send(websocket, session, {"type": "error", "detail": str(exc)})
                    continue
                finally:
                    _release_quota(peer_id)

                try:
                    session.document = ot_engine.merge_document(session.document, [applied])
                except Exception as exc:
                    rtcollab_operations_total.labels(outcome="error").inc()
                    await _send(websocket, session, {"type": "error", "detail": str(exc)})
                    continue

                rtcollab_operations_total.labels(outcome="applied").inc()
                await _broadcast(
                    session,
                    {"type": "operation", "operation": applied.to_dict()},
                    exclude_peer_id=peer_id,
                )

            elif msg_type == "sync_request":
                since_version = data.get("since_version", 0)
                ops = ot_engine.get_operations_since(peer_id, since_version)
                await _send(websocket, session, {
                    "type": "sync_response",
                    "operations": [op.to_dict() for op in ops],
                    "document": session.document,
                })

            elif msg_type == "presence":
                await _broadcast(
                    session,
                    {"type": "presence", "peer_id": peer_id, "status": data.get("status", "active")},
                    exclude_peer_id=peer_id,
                )

    except WebSocketDisconnect:
        pass
    finally:
        # Cleanup on disconnect
        session.peers.pop(peer_id, None)
        active_connections.get(session_id, {}).pop(peer_id, None)
        _clear_quota(peer_id)
        rtcollab_active_connections.dec()
        await _broadcast(
            session,
            {"type": "presence", "peer_id": peer_id, "status": "left"},
        )
        if not session.peers:
            session_registry.pop(session_id, None)
            active_connections.pop(session_id, None)
            clear_session_engine(session_id)
            await get_discovery().stop_advertising(session_id)
