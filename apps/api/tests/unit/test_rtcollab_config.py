"""
AstroOS — RTCollab Regression Tests (Phase IV, IV.4 Quality Gate)

Covers the three guarantees ASTROOS_PHASE_IV_V2_4_ROADMAP.md §IV.2/IV.4
require and that weren't exercised by any test until now:

  1. Default-off behavior — ENABLE_RTCOLLAB unset/false means the WS and
     mDNS-discovery routers aren't mounted at all (404, not just 401).
  2. Opt-in behavior — ENABLE_RTCOLLAB=true mounts them (401: route exists,
     auth-gated).
  3. Connection-limit (CPU quota) enforcement — a device is capped at
     MAX_PENDING_OPS_PER_PEER in-flight operations.
  4. LAN-only, no external service dependency — the collaboration modules
     never import a cloud SDK or reference a non-local network target;
     discovery uses local mDNS multicast (zeroconf), not a hosted service.
"""

from __future__ import annotations

import ast
import inspect

import pytest
from fastapi.testclient import TestClient

from apps.api.config import get_settings


@pytest.fixture(autouse=True)
def restore_settings(monkeypatch):
    get_settings.cache_clear()
    yield
    monkeypatch.delenv("ENABLE_RTCOLLAB", raising=False)
    get_settings.cache_clear()


# ── 1 & 2: default-off / opt-in mounting ──────────────────────────────────────


def test_rtcollab_default_is_off():
    assert get_settings().ENABLE_RTCOLLAB is False


def test_rtcollab_routes_absent_by_default():
    import apps.api.main as main_module

    app = main_module.create_app()
    with TestClient(app) as client:
        assert client.get("/api/v1/collab/sessions/discovered").status_code == 404
        # A plain GET to a websocket-only path also 404s when unmounted.
        assert client.get("/ws/session/test").status_code == 404


def test_rtcollab_routes_present_when_opted_in(monkeypatch):
    monkeypatch.setenv("ENABLE_RTCOLLAB", "true")
    get_settings.cache_clear()

    import apps.api.main as main_module

    monkeypatch.setattr(
        main_module, "_settings", main_module._settings.model_copy(update={"ENABLE_RTCOLLAB": True})
    )
    app = main_module.create_app()
    with TestClient(app) as client:
        # Route exists and is auth-gated (401), not missing (404).
        resp = client.get("/api/v1/collab/sessions/discovered")
        assert resp.status_code == 401


# ── 3: connection-limit (CPU quota) enforcement ───────────────────────────────


def test_quota_caps_pending_ops_per_peer():
    from apps.api.routers import ws as ws_router

    peer_id = "quota-test-peer"
    ws_router._clear_quota(peer_id)
    try:
        for _ in range(ws_router.MAX_PENDING_OPS_PER_PEER):
            assert ws_router._try_acquire_quota(peer_id) is True
        # One more than the cap must be rejected.
        assert ws_router._try_acquire_quota(peer_id) is False
    finally:
        ws_router._clear_quota(peer_id)


def test_quota_release_frees_a_slot():
    from apps.api.routers import ws as ws_router

    peer_id = "quota-release-test-peer"
    ws_router._clear_quota(peer_id)
    try:
        for _ in range(ws_router.MAX_PENDING_OPS_PER_PEER):
            ws_router._try_acquire_quota(peer_id)
        assert ws_router._try_acquire_quota(peer_id) is False

        ws_router._release_quota(peer_id)
        assert ws_router._try_acquire_quota(peer_id) is True
    finally:
        ws_router._clear_quota(peer_id)


def test_quota_clear_resets_a_peer_fully():
    from apps.api.routers import ws as ws_router

    peer_id = "quota-clear-test-peer"
    for _ in range(ws_router.MAX_PENDING_OPS_PER_PEER):
        ws_router._try_acquire_quota(peer_id)

    ws_router._clear_quota(peer_id)
    for _ in range(ws_router.MAX_PENDING_OPS_PER_PEER):
        assert ws_router._try_acquire_quota(peer_id) is True
    ws_router._clear_quota(peer_id)


# ── 4: LAN-only, no external/cloud service dependency ─────────────────────────

_CLOUD_SDK_MARKERS = (
    "boto3", "google.cloud", "azure.", "openai", "anthropic",
    "stripe", "twilio", "sendgrid", "aws_",
)

_RTCOLLAB_MODULES = (
    "apps.api.routers.ws",
    "apps.api.routers.collab",
    "apps.api.services.collab_discovery",
    "apps.api.services.collab_crypto",
    "apps.api.services.ot_engine",
)


def _imported_module_names(module) -> set[str]:
    """Every module name imported at the top level of `module`'s source."""
    tree = ast.parse(inspect.getsource(module))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_rtcollab_modules_import_no_cloud_sdk():
    import importlib

    for module_name in _RTCOLLAB_MODULES:
        module = importlib.import_module(module_name)
        imported = _imported_module_names(module)
        for marker in _CLOUD_SDK_MARKERS:
            offenders = [name for name in imported if name.startswith(marker)]
            assert not offenders, f"{module_name} imports a cloud SDK: {offenders}"


def test_rtcollab_connection_health_metrics_exist():
    """observability/SLO.md documents a WebSocket connection-health SLI
    backed by these two metrics — assert they're real, registered
    Prometheus collectors, not just a promise in the doc."""
    from apps.api.routers import ws as ws_router

    assert ws_router.rtcollab_active_connections._name == "rtcollab_active_connections"
    # prometheus_client's Counter strips the trailing "_total" from ._name
    # internally (it re-adds the suffix when exporting) — this is the
    # library's own convention, not a naming mistake here.
    assert ws_router.rtcollab_operations_total._name == "rtcollab_operations"
    assert list(ws_router.rtcollab_operations_total._labelnames) == ["outcome"]


def test_collab_discovery_uses_local_mdns_not_a_hosted_service():
    """zeroconf is a local mDNS/Bonjour implementation (RFC 6762/6763) —
    multicast on the LAN segment, never a request to any external host.
    Asserts the discovery service is actually built on it, not a stub
    that silently calls out to a hosted directory."""
    from apps.api.services import collab_discovery

    assert "zeroconf" in _imported_module_names(collab_discovery)
    # SERVICE_TYPE must be a private mDNS service type (".local." suffix is
    # the reserved, non-routable mDNS domain — RFC 6762 §3).
    assert collab_discovery.SERVICE_TYPE.endswith(".local.")
