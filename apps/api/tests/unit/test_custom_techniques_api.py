"""
AstroOS — Unit Tests for Custom Techniques Registry, Import/Export, & API Endpoints
"""

import json
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.main import app
from apps.api.services.custom_technique_service import CustomTechniqueRegistry


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "test_user"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_custom_technique_registry_singleton():
    registry = CustomTechniqueRegistry.get_instance()
    rules = registry.list_rules()

    assert len(rules) >= 2
    rule_ids = [r.rule_id for r in rules]
    assert "custom-gajakesari-01" in rule_ids


def test_custom_technique_registry_import_export():
    registry = CustomTechniqueRegistry.get_instance()
    bundle_json = registry.export_bundle()

    data = json.loads(bundle_json)
    assert data["format"] == "AstroOS_AstroDSL_Bundle"
    assert len(data["rules"]) >= 2

    # Clear and re-import
    imported = registry.import_bundle(bundle_json)
    assert len(imported) >= 2


def test_custom_technique_api_validate(api_client):
    response = api_client.post(
        "/api/v1/techniques/custom/dsl/validate",
        json={"dsl_source": 'PLANET("Jupiter").house IN [1, 4, 7, 10]'},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is True


def test_custom_technique_api_test_evaluate(api_client):
    chart_data = {
        "planets": [
            {"planet": "JUPITER", "house_number": 1, "is_combust": False},
        ],
        "planet_strengths": [],
    }

    response = api_client.post(
        "/api/v1/techniques/custom/dsl/test-evaluate",
        json={
            "dsl_source": 'PLANET("Jupiter").house == 1 AND PLANET("Jupiter").is_combust == FALSE',
            "chart_context": chart_data,
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res["is_satisfied"] is True
    assert res["execution_time_ms"] >= 0.0


def test_custom_technique_api_crud(api_client):
    # 1. Create rule
    create_resp = api_client.post(
        "/api/v1/techniques/custom/",
        json={
            "name": "Custom Sun Digbala Rule",
            "description": "Sun in 10th house",
            "dsl_source": 'PLANET("Sun").house == 10',
            "category": "custom_yoga",
            "tags": ["sun", "digbala"],
        },
    )
    assert create_resp.status_code == 201
    created_rule = create_resp.json()
    rule_id = created_rule["rule_id"]
    assert created_rule["name"] == "Custom Sun Digbala Rule"

    # 2. List rules
    list_resp = api_client.get("/api/v1/techniques/custom/")
    assert list_resp.status_code == 200
    rules = list_resp.json()
    assert any(r["rule_id"] == rule_id for r in rules)

    # 3. Export bundle
    export_resp = api_client.post(
        "/api/v1/techniques/custom/export",
        json={"rule_ids": [rule_id]},
    )
    assert export_resp.status_code == 200
    bundle_data = json.loads(export_resp.json()["bundle_json"])
    assert len(bundle_data["rules"]) == 1

    # 4. Delete rule
    del_resp = api_client.delete(f"/api/v1/techniques/custom/{rule_id}")
    assert del_resp.status_code == 200
