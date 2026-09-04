"""
AstroOS — Phase 14 Production Hardening & Release Verification Tests
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_liveness_probe(client):
    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json()["status"] == "alive"


def test_readiness_probe(client):
    res = client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert "database" in data["checks"]


def test_system_healthz_endpoint(client):
    res = client.get("/api/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["ephemeris"]["mode"] == "swiss_ephemeris"
    assert data["ephemeris"]["official_data"] is True


def test_prometheus_metrics_endpoint(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "api_request_duration_seconds" in res.text or "python_info" in res.text or "process_virtual_memory_bytes" in res.text
