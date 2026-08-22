"""
Integration tests for Classical Rule Evidence FastAPI Router (Module 19, Phase 3)
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers import classical_rule_evidence


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(classical_rule_evidence.router, prefix="/api/v1")
    return TestClient(app)


class TestClassicalRuleEvidenceRouter:
    def test_explore_endpoint(self, client: TestClient):
        res = client.get("/api/v1/rules/explore")
        assert res.status_code == 200
        data = res.json()
        assert "total_rules" in data
        assert data["total_rules"] >= 8
        assert len(data["rules"]) >= 8

        # Verify first rule structure
        rule0 = data["rules"][0]
        assert "rule_id" in rule0
        assert "book_title" in rule0
        assert "author" in rule0
        assert "sanskrit_preview" in rule0
        assert rule0["is_verified"] is True

    def test_explore_with_filters(self, client: TestClient):
        # Filter by tradition Parashari
        res_p = client.get("/api/v1/rules/explore?tradition=Parashari")
        assert res_p.status_code == 200
        data_p = res_p.json()
        for r in data_p["rules"]:
            assert "Parashari" in r["tradition"]

        # Filter by category Raja Yoga
        res_ry = client.get("/api/v1/rules/explore?category=Raja%20Yoga")
        assert res_ry.status_code == 200
        data_ry = res_ry.json()
        for r in data_ry["rules"]:
            assert "Raja Yoga" in r["category"]

    def test_rule_details_endpoint(self, client: TestClient):
        res = client.get("/api/v1/rules/BPHS-YOGA-GAJAKESARI/details")
        assert res.status_code == 200
        data = res.json()
        assert data["rule_id"] == "BPHS-YOGA-GAJAKESARI"
        assert data["citation"]["book_title"] == "Brihat Parashara Hora Shastra"
        assert len(data["citation"]["sanskrit_iast"]) > 0
        assert len(data["citation"]["sanskrit_devanagari"]) > 0
        assert len(data["requirements"]) >= 1

    def test_evaluate_chart_endpoint(self, client: TestClient):
        payload = {
            "chart": {
                "id": "test-chart-001",
                "planets": [
                    {"planet": "Jupiter", "house_number": 1, "rashi": "Cancer", "dignity": "exalted", "is_combust": False},
                    {"planet": "Moon", "house_number": 4, "rashi": "Libra", "dignity": "neutral", "is_combust": False},
                    {"planet": "Sun", "house_number": 10, "rashi": "Aries", "dignity": "exalted", "is_combust": False},
                ]
            }
        }
        res = client.post("/api/v1/rules/evaluate-chart", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["total_rules_evaluated"] >= 8
        assert data["satisfied_rules_count"] >= 1
        assert len(data["evidence_chains"]) >= 8

        # Check Gajakesari chain
        gk = next((c for c in data["evidence_chains"] if c["rule_id"] == "BPHS-YOGA-GAJAKESARI"), None)
        assert gk is not None
        assert gk["status"] == "SATISFIED"
        assert gk["strength_score"] >= 90.0
        assert len(gk["actual_evidence"]) >= 1
        assert gk["citation"]["is_verified"] is True
