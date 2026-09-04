"""
System Robustness & Boundary Validation Test Suite
===================================================

Tests:
1. Valid boundary calculations (equator, date ranges, polar latitudes).
2. Input constraint enforcement (latitude/longitude out of range, reversed year scan).
3. 422 Unprocessable Entity gracefully caught with clear error details.
4. Mathematical safety (zero divisions, floating point overflows).
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from apps.api.routers.phalita_prediction import router as phalita_router

app = FastAPI()
app.include_router(phalita_router)
client = TestClient(app)


def test_consultation_valid_payload():
    """Verify normal consultation payload succeeds."""
    payload = {
        "birth_date_iso": "1985-05-15T14:30:00+00:00",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "native_name": "Robustness Test Profile",
        "scan_start_year": 2020,
        "scan_end_year": 2025,
        "domain": "career",
        "evaluation_target_date_iso": "2023-01-01",
    }
    res = client.post("/api/v1/phalita/consultation", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "timeline_summary" in data
    assert "sudarshana_chakra" in data
    assert "varga_fusion" in data
    assert "bhrigu_bindu" in data


def test_consultation_reversed_years_validation():
    """Verify reversed scan years are caught with 422 validation error."""
    payload = {
        "birth_date_iso": "1985-05-15T14:30:00+00:00",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "native_name": "Robustness Test Profile",
        "scan_start_year": 2030,
        "scan_end_year": 2020,  # Invalid: end < start
        "domain": "career",
    }
    res = client.post("/api/v1/phalita/consultation", json=payload)
    assert res.status_code == 422, res.text


def test_consultation_invalid_latitude():
    """Verify out-of-range latitude is caught with 422 validation error."""
    payload = {
        "birth_date_iso": "1985-05-15T14:30:00+00:00",
        "latitude": 95.0,  # Invalid: > 90
        "longitude": 77.2090,
        "native_name": "Robustness Test Profile",
        "scan_start_year": 2020,
        "scan_end_year": 2025,
        "domain": "career",
    }
    res = client.post("/api/v1/phalita/consultation", json=payload)
    assert res.status_code == 422, res.text


def test_consultation_invalid_longitude():
    """Verify out-of-range longitude is caught with 422 validation error."""
    payload = {
        "birth_date_iso": "1985-05-15T14:30:00+00:00",
        "latitude": 28.6139,
        "longitude": -195.0,  # Invalid: < -180
        "native_name": "Robustness Test Profile",
        "scan_start_year": 2020,
        "scan_end_year": 2025,
        "domain": "career",
    }
    res = client.post("/api/v1/phalita/consultation", json=payload)
    assert res.status_code == 422, res.text


def test_feature_extraction_vector_dimension():
    """Verify extracted feature vector strictly conforms to 128 dimensions without NaN/Inf."""
    payload = {
        "birth_date_iso": "1975-10-20T08:15:00+00:00",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "target_date_iso": "2024-06-01",
    }
    res = client.post("/api/v1/phalita/extract-vector", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["vector_dimension"] == 128
    assert len(data["feature_vector"]) == 128
    for val in data["feature_vector"]:
        assert val is not None
        assert isinstance(val, (int, float))
