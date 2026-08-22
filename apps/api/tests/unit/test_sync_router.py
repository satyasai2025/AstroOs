"""
Router tests for Local-First Mobile Sync Endpoints (Module 21, Priority 6)
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.services.mobile_sync_service import MobileSyncService


@pytest.fixture(autouse=True)
def clean_sync_service():
    service = MobileSyncService()
    MobileSyncService._instance = service
    return service


def test_sync_router_pairing_and_revocation_e2e():
    client = TestClient(app)

    # 1. Generate Pairing Session
    gen_resp = client.post("/api/v1/sync/pairing/generate", json={})
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert "session_id" in gen_data
    assert "pin_code" in gen_data
    assert "qr_payload" in gen_data

    session_id = gen_data["session_id"]
    pin_code = gen_data["pin_code"]

    # 2. Verify Pairing
    verify_resp = client.post(
        "/api/v1/sync/pairing/verify",
        json={
            "session_id": session_id,
            "pin_code": pin_code,
            "device_name": "Galaxy Tab S9",
            "device_type": "tablet",
        },
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    device_id = verify_data["device_id"]
    device_token = verify_data["device_secret_token"]

    # 3. Pull Entities
    pull_resp = client.post(
        "/api/v1/sync/pull",
        json={
            "device_id": device_id,
            "device_secret_token": device_token,
            "last_known_cursor": 0,
        },
    )
    assert pull_resp.status_code == 200
    pull_data = pull_resp.json()
    assert "entities" in pull_data
    assert len(pull_data["entities"]) >= 1

    # 4. List Devices
    dev_resp = client.get("/api/v1/sync/devices")
    assert dev_resp.status_code == 200
    dev_data = dev_resp.json()
    assert dev_data["total_active"] >= 1

    # 5. Revoke Device
    del_resp = client.delete(f"/api/v1/sync/devices/{device_id}")
    assert del_resp.status_code == 200

    # 6. Pull with Revoked Device MUST be Forbidden (403)
    pull_revoked = client.post(
        "/api/v1/sync/pull",
        json={
            "device_id": device_id,
            "device_secret_token": device_token,
            "last_known_cursor": 0,
        },
    )
    assert pull_revoked.status_code == 403
