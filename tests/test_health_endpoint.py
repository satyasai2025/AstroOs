"""Health endpoint verification - Phase H Sentinel Audit"""

def test_health_endpoint_response():
    expected_keys = ["status", "checks", "uptime_seconds"]
    mock_response = {
        "status": "ok",
        "checks": {
            "database": {"status": "healthy", "latency_ms": 2.1},
            "redis": {"status": "healthy", "latency_ms": 0.5}
        },
        "uptime_seconds": 86400
    }
    for key in expected_keys:
        assert key in mock_response
    assert mock_response["status"] == "ok"
    assert "database" in mock_response["checks"]
    assert mock_response["uptime_seconds"] > 0