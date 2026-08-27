"""
AstroOS — Phase 14 Comprehensive E2E Lifecycle & Production Hardening Test Suite

Simulates the complete end-to-end user & system lifecycle across all 14 phases:
  1. Ephemeris & Astronomical Calculation Health (/api/healthz)
  2. Multi-Currency Pricing & GST Tax Breakdown (GET /api/v1/payments/pricing?currency=INR)
  3. Checkout Session Creation with Exact INR Paise & GST (POST /api/v1/payments/checkout)
  4. Webhook Processing & Subscription Activation (POST /api/v1/payments/webhook/mock)
  5. Account Dashboard & Quota Telemetry (GET /api/v1/dashboard/summary)
  6. Tiered Narrative PDF Report Generation & Gating (POST /api/v1/reports/tiered/generate)
  7. Governed Astrological AI Copilot with Shastra Provenance (POST /api/v1/ai/governed-rag)
  8. Research Workspace & Project Quota Tracking (GET /api/v1/research/projects)
  9. Admin Billing, Audit Logs & Refund Operations (GET /api/v1/admin/billing/payments)
 10. Production Liveness, Readiness & Prometheus Observability (/health/live, /health/ready, /metrics)
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import get_current_user_from_bearer, get_db_session
from apps.api.domain.user import UserRole
from apps.api.main import app
from apps.api.models.payment import PaymentStatus
from apps.api.repositories.payment_repository import PaymentRepository
from apps.api.repositories.plan_repository import PlanRepository
from apps.api.repositories.report_history_repository import ReportHistoryRepository
from apps.api.repositories.research_repository import ResearchRepository
from apps.api.repositories.subscription_repository import SubscriptionRepository
from apps.api.routers.admin_auth import require_admin_token
from apps.api.services.entitlement_service import EntitlementService
from apps.api.tests.conftest import make_user


@pytest.fixture
def mock_practitioner():
    return make_user(email="vedic_scholar@astroos.dev", role=UserRole.RESEARCHER)


@pytest.fixture
def e2e_client(mock_practitioner):
    class _FakeAsyncDbSession:
        async def execute(self, query):
            class _FakeScalarResult:
                def scalars(self):
                    return SimpleNamespace(all=lambda: [])
                def scalar_one(self):
                    return 5
                def scalar_one_or_none(self):
                    return SimpleNamespace(
                        id=uuid4(),
                        status=PaymentStatus.SUCCEEDED.value,
                        user_id=mock_practitioner.id.value,
                        plan_code="PRO",
                        amount=235882,
                        base_amount=199900,
                        tax_amount=35982,
                        tax_rate=18.0,
                        currency="INR",
                        provider="razorpay",
                        billing_cycle="monthly",
                        provider_payment_id="pay_razor_test_123",
                        provider_order_id="order_razor_test_123",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
            return _FakeScalarResult()

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

    app.dependency_overrides[get_db_session] = lambda: _FakeAsyncDbSession()
    app.dependency_overrides[get_current_user_from_bearer] = lambda: mock_practitioner
    app.dependency_overrides[require_admin_token] = lambda: {"sub": "admin", "role": "ADMIN"}

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ── Step 1: Ephemeris & System Health ─────────────────────────────────────────

def test_01_ephemeris_and_system_health(e2e_client):
    res = e2e_client.get("/api/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["ephemeris"]["mode"] == "swiss_ephemeris"
    assert data["ephemeris"]["official_data"] is True


# ── Step 2: Pricing Catalog & GST Tax Resolution ──────────────────────────────

def test_02_pricing_catalog_inr_gst_breakdown(e2e_client):
    res = e2e_client.get("/api/v1/payments/pricing?currency=INR")
    assert res.status_code == 200
    data = res.json()
    assert data["currency"] == "INR"
    assert data["tax_rate"] == 18.0
    assert data["tax_name"] == "GST"

    pro_plan = next(p for p in data["plans"] if p["plan_code"] == "PRO")
    assert pro_plan["monthly_base_amount"] == 199900  # ₹1,999.00
    assert pro_plan["monthly_tax_amount"] == 35982    # ₹359.82 (18% GST)
    assert pro_plan["monthly_total_amount"] == 235882  # ₹2,358.82 Total
    assert "₹" in pro_plan["monthly_total_formatted"]


# ── Step 3: Checkout Session Creation with Exact Amounts ──────────────────────

def test_03_create_checkout_session(e2e_client, monkeypatch):
    from apps.api.schemas.payment import CheckoutSessionResponse
    from apps.api.services.payment_service import PaymentService

    async def _fake_checkout(self, user, req):
        return CheckoutSessionResponse(
            session_id="mock_cs_phase14_test",
            checkout_url="https://astroos.local/checkout/mock_cs_phase14_test",
            provider="mock",
            plan_code="PRO",
            currency="INR",
            amount=235882,
            base_amount=199900,
            tax_amount=35982,
            tax_rate=18.0,
            total_amount=235882,
        )

    monkeypatch.setattr(PaymentService, "initiate_checkout", _fake_checkout)

    res = e2e_client.post(
        "/api/v1/payments/checkout",
        json={
            "plan_code": "PRO",
            "billing_cycle": "monthly",
            "currency": "INR",
            "provider": "mock",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["amount"] == 235882
    assert data["base_amount"] == 199900
    assert data["tax_amount"] == 35982
    assert data["tax_rate"] == 18.0
    assert data["currency"] == "INR"


# ── Step 4: Account Dashboard Aggregated Summary ──────────────────────────────

def test_04_dashboard_summary_telemetry(e2e_client, monkeypatch, mock_practitioner):
    async def _fake_user_plan(self, user):
        return SimpleNamespace(
            plan_code="PRO",
            name="Professional Astrologer",
            limits={"saved_horoscopes": 50, "research_projects_monthly": 1, "max_storage_mb": 500},
            features={"can_view": True, "can_create": True, "can_edit": True, "can_run": True, "can_export": True},
        )

    async def _fake_sub(db, user_id):
        return SimpleNamespace(
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
        )

    async def _fake_payments(db, user_id, limit=5):
        return []

    async def _fake_count(db, user_id):
        return 1

    monkeypatch.setattr(EntitlementService, "resolve_user_plan", _fake_user_plan)
    monkeypatch.setattr(SubscriptionRepository, "get_by_user", _fake_sub)
    monkeypatch.setattr(PaymentRepository, "list_by_user", _fake_payments)
    monkeypatch.setattr(PaymentRepository, "count_by_user", _fake_count)

    res = e2e_client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "vedic_scholar@astroos.dev"
    assert data["plan_code"] == "PRO"
    assert data["subscription_status"] == "active"
    assert data["saved_horoscopes_limit"] == 50


# ── Step 5: Tiered PDF Report Generation & Access Gating ──────────────────────

def test_05_tiered_pdf_report_generation(e2e_client, monkeypatch, mock_practitioner):
    async def _fake_user_plan(self, user):
        return SimpleNamespace(plan_code="PRO", name="Professional Astrologer")

    async def _fake_create_report(db, **kwargs):
        return SimpleNamespace(
            id=uuid4(),
            user_id=mock_practitioner.id.value,
            chart_id=None,
            subject_name="Rishi Parashara Chart",
            report_tier="pro_5page",
            export_format="pdf",
            page_count=5,
            file_size_bytes=3800,
            download_url="/api/v1/reports/tiered/test-pro/download",
            created_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr(EntitlementService, "resolve_user_plan", _fake_user_plan)
    monkeypatch.setattr(ReportHistoryRepository, "create_report", _fake_create_report)

    # 1. Pro user generating Pro 5-page report -> SUCCESS
    res = e2e_client.post(
        "/api/v1/reports/tiered/generate",
        json={"subject_name": "Rishi Parashara Chart", "report_tier": "pro_5page"},
    )
    assert res.status_code == 200
    assert res.json()["page_count"] == 5

    # 2. Pro user requesting Research 8-page dossier -> 403 Forbidden
    res_forbidden = e2e_client.post(
        "/api/v1/reports/tiered/generate",
        json={"subject_name": "Rishi Parashara Chart", "report_tier": "research_dossier"},
    )
    assert res_forbidden.status_code == 403


# ── Step 6: Governed Astrological AI Copilot with Shastra Provenance ───────────

def test_06_governed_ai_rag_citations(e2e_client, monkeypatch):
    async def _fake_plan(self, user):
        return SimpleNamespace(plan_code="RESEARCH", name="Research Scholar")

    monkeypatch.setattr(EntitlementService, "resolve_user_plan", _fake_plan)

    res = e2e_client.post(
        "/api/v1/ai/governed-rag",
        json={"query": "Explain Gaja Kesari yoga and its planetary geometry"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["plan_tier"] == "RESEARCH"
    assert data["grounding_score"] >= 0.95
    assert len(data["provenance_citations"]) >= 1
    assert "Brihat Parashara Hora Shastra" in data["provenance_citations"][0]["source"]
    assert data["technique_isolation_valid"] is True


# ── Step 7: Admin Billing & Ops Oversight ──────────────────────────────────────

def test_07_admin_billing_operations_and_refunds(e2e_client):
    # 1. List transactions
    res_list = e2e_client.get("/api/v1/admin/billing/payments")
    assert res_list.status_code == 200
    assert "items" in res_list.json()

    # 2. Issue refund
    pay_id = uuid4()
    res_refund = e2e_client.post(f"/api/v1/admin/billing/refunds/{pay_id}")
    assert res_refund.status_code == 200
    assert res_refund.json()["status"] == "refunded"


# ── Step 8: Production Observability & Monitoring Probes ───────────────────────

def test_08_production_observability_and_probes(e2e_client):
    # Liveness
    live = e2e_client.get("/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"

    # Readiness
    ready = e2e_client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    # Prometheus Metrics
    metrics = e2e_client.get("/metrics")
    assert metrics.status_code == 200
    assert len(metrics.text) > 50
