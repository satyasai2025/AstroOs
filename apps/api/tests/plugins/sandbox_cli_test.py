import pytest
import asyncio
from httpx import AsyncClient
from fastapi import status
from apps.api.main import app
try:
    from astroos.client import AstroOSClient
except ImportError:
    from packages.python.astroos.client import AstroOSClient

@pytest.fixture
async def plugin_client():
    return AstroOSClient(base_url="http://localhost:8000")

@pytest.mark.asyncio
async def test_plugin_cli_basic_functionality(plugin_client):
    # Test basic plugin installation and CLI command
    # 1. Install sample plugin
    install_result = plugin_client._post("/api/v1/plugins/install", json={
        "plugin_path": "/path/to/sample_astronomy_plugin"
    })
    assert install_result.status_code == status.HTTP_202_ACCEPTED

    # 2. Run plugin calculation
    calc_result = plugin_client._post("/api/v1/plugins/calculate", json={
        "plugin_name": "sample-astronomy-plugin",
        "command": "calculate",
        "args": ["--heavy"]
    })
    assert calc_result.status_code == status.HTTP_200_OK

    # 3. Check resource limits in plugin sandbox
    sandbox_report = plugin_client._get("/api/v1/plugins/sandbox-report")
    assert sandbox_report.status_code == status.HTTP_200_OK
    # Verify CPU/Memory/Network limits were respected

@pytest.mark.asyncio
async def test_plugin_sandbox_limits(plugin_client):
    # Test CPU limit enforcement
    heavy_result = plugin_client._post("/api/v1/plugins/calculate", json={
        "plugin_name": "sample-astronomy-plugin",
        "command": "calculate",
        "args": ["--heavy"]
    })
    # Should fail or throttle if CPU exceeds 25%

    # Test memory limit
    memory_result = plugin_client._post("/api/v1/plugins/calculate", json={
        "plugin_name": "sample-astronomy-plugin",
        "command": "calculate",
        "args": ["--memory"]
    })
    # Should handle within 50MB cap

    # Test network limit (should be none in plugin metadata)
    network_result = plugin_client._post("/api/v1/plugins/calculate", json={
        "plugin_name": "sample-astronomy-plugin",
        "command": "calculate",
        "args": ["--network"]
    })
    # Should fail if network access isn't allowed