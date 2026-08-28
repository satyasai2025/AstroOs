"""
Unit tests for Forward Predictions API Router (POST /api/v1/predictions/forward-scan).
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_forward_scan_endpoint_success():
    payload = {
        "birth_datetime_utc": "1990-01-01T12:00:00Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "target_start_date": "2026-01-01",
        "target_end_date": "2027-01-01",
        "event_types": ["marriage", "job_change", "financial_gain"],
        "min_confidence": 0.0,
    }

    # API requests authenticated via test token/dependency override
    response = client.post("/api/v1/predictions/forward-scan", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "chart_id" in data
    assert data["target_start"] == "2026-01-01"
    assert data["target_end"] == "2027-01-01"
    assert "uncertainty_disclosure" in data
    assert "scan_version" in data
    assert isinstance(data["candidates"], list)
    assert isinstance(data["event_types_evaluated"], list)


def test_forward_scan_endpoint_defaults():
    response = client.post("/api/v1/predictions/forward-scan", json={})
    assert response.status_code == 200
    data = response.json()
    assert "candidates" in data
    assert data["scan_version"] == "forward_v1"
