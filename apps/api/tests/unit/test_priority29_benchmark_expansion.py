"""
AstroOS — Unit Tests for Priority 29: Research Benchmark Expansion Engine
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.benchmark_expansion import (
    ExpandedBenchmarkSuiteType,
    ExpandedResearchDomain,
    MANDATORY_BENCHMARK_EPISTEMIC_DISCLOSURE,
    MANDATORY_NON_MEDICAL_DISCLAIMER,
    PROHIBITED_HEALTH_TERMS,
)
from apps.api.main import app
from apps.api.services.benchmark_expansion_engine import BenchmarkExpansionEngine


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "p29_tester", "role": "researcher"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_governed_benchmark_cases_and_independent_ground_truth():
    """
    Verifies that benchmark cases have independently established ground truth references.
    """
    engine = BenchmarkExpansionEngine.get_instance()
    cases = engine.list_test_cases()

    assert len(cases) >= 6
    career_cases = [c for c in cases if c.domain == ExpandedResearchDomain.CAREER]
    wealth_cases = [c for c in cases if c.domain == ExpandedResearchDomain.WEALTH_FINANCE]
    vitality_cases = [c for c in cases if c.domain == ExpandedResearchDomain.HEALTH_VITALITY]

    assert len(career_cases) >= 2
    assert len(wealth_cases) >= 2
    assert len(vitality_cases) >= 2

    for c in cases:
        assert c.independent_reference_source is not None
        assert len(c.independent_reference_source) > 0
        assert c.expected_ground_truth_output is not None


def test_benchmark_suite_execution_and_epistemic_separation():
    """
    Verifies execution of Career, Wealth, and Vitality suites, verifying reproduction accuracy,
    and ensuring epistemic distinction between benchmark accuracy and real-world predictive validity.
    """
    engine = BenchmarkExpansionEngine.get_instance()

    report = engine.generate_cross_domain_report()

    assert report is not None
    assert report.total_suites_evaluated == 3
    assert report.total_test_cases_evaluated >= 6
    assert report.overall_mean_reproduction_accuracy >= 95.0
    assert report.non_medical_compliance_verified is True
    assert MANDATORY_BENCHMARK_EPISTEMIC_DISCLOSURE in report.epistemic_scope_statement

    for r in report.suite_results:
        assert r.reproduction_accuracy_percent >= 90.0
        assert r.mean_latency_microseconds > 0.0
        assert r.is_reference_verified is True
        assert MANDATORY_NON_MEDICAL_DISCLAIMER in r.non_medical_safety_declaration
        assert MANDATORY_BENCHMARK_EPISTEMIC_DISCLOSURE in r.epistemic_benchmark_disclosure


def test_strict_non_medical_safety_guardrails():
    """
    Verifies that health-related benchmark evaluations strictly prohibit diagnostic or clinical terms.
    """
    engine = BenchmarkExpansionEngine.get_instance()
    res = engine.run_benchmark_suite(ExpandedBenchmarkSuiteType.BM_HEALTH_VITALITY_TYPOLOGY)

    assert res.domain == ExpandedResearchDomain.HEALTH_VITALITY
    assert MANDATORY_NON_MEDICAL_DISCLAIMER in res.non_medical_safety_declaration

    combined_text = f"{res.non_medical_safety_declaration} {res.epistemic_benchmark_disclosure}".lower()
    for term in PROHIBITED_HEALTH_TERMS:
        assert f"predict {term}" not in combined_text
        assert f"diagnose {term}" not in combined_text


def test_benchmark_expansion_api_endpoints(api_client):
    """
    Verifies FastAPI endpoints for cases, suite execution, and cross-domain reports.
    """
    # GET /api/v1/research/benchmark-expansion/cases
    cases_resp = api_client.get("/api/v1/research/benchmark-expansion/cases")
    assert cases_resp.status_code == 200
    cases_data = cases_resp.json()
    assert len(cases_data) >= 6

    # POST /api/v1/research/benchmark-expansion/run
    run_resp = api_client.post(
        "/api/v1/research/benchmark-expansion/run",
        json={"suite_type": "BM_CAREER_D10_PROMOTION", "snapshot_id": None},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["suite_type"] == "BM_CAREER_D10_PROMOTION"
    assert run_data["reproduction_accuracy_percent"] == 100.0

    # POST /api/v1/research/benchmark-expansion/report
    rep_resp = api_client.post(
        "/api/v1/research/benchmark-expansion/report",
        json={},
    )
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert rep_data["total_suites_evaluated"] == 3
    assert rep_data["overall_mean_reproduction_accuracy"] == 100.0

    # GET /api/v1/research/benchmark-expansion/latest
    latest_resp = api_client.get("/api/v1/research/benchmark-expansion/latest")
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()
    assert latest_data["total_suites_evaluated"] == 3
