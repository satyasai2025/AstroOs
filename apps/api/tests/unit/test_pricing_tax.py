"""
AstroOS — Phase 8 Multi-Currency Pricing & Tax Calculation Tests

Verifies:
  - INR as primary first-class pricing currency (₹)
  - Monthly and Annual pricing
  - Backend-driven tax calculation (18% GST for INR, configurable)
  - Integer / smallest-denomination precision and rounding (paise / cents)
  - Total payable amount calculation (Base + Tax = Total)
  - Currency consistency and pricing catalog structure
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.config import get_settings
from apps.api.dependencies import get_current_user_from_bearer, get_db_session
from apps.api.domain.user import UserRole
from apps.api.main import app
from apps.api.repositories.plan_repository import PlanRepository
from apps.api.services.payment_service import PaymentService
from apps.api.tests.conftest import make_user


def test_inr_pricing_and_gst_calculation():
    settings = get_settings()
    assert settings.TAX_RATE_INR_PERCENT == 18.0

    # 1. PRO Monthly in INR
    pro_m = PaymentService.calculate_pricing("PRO", billing_cycle="monthly", currency="INR")
    assert pro_m["plan_code"] == "PRO"
    assert pro_m["currency"] == "INR"
    assert pro_m["currency_symbol"] == "₹"
    assert pro_m["base_amount"] == 199900  # ₹1,999.00 in paise
    assert pro_m["tax_rate"] == 18.0
    assert pro_m["tax_name"] == "GST"
    # 199900 * 0.18 = 35982 paise (₹359.82)
    assert pro_m["tax_amount"] == 35982
    # Total = 199900 + 35982 = 235882 paise (₹2,358.82)
    assert pro_m["total_amount"] == 235882
    assert "₹1,999.00" in pro_m["base_amount_formatted"]
    assert "₹359.82" in pro_m["tax_amount_formatted"]
    assert "₹2,358.82" in pro_m["total_amount_formatted"]

    # 2. PRO Yearly in INR
    pro_y = PaymentService.calculate_pricing("PRO", billing_cycle="yearly", currency="INR")
    assert pro_y["base_amount"] == 1999000  # ₹19,990.00
    # 1999000 * 0.18 = 359820 paise (₹3,598.20)
    assert pro_y["tax_amount"] == 359820
    assert pro_y["total_amount"] == 2358820
    assert "₹19,990.00" in pro_y["base_amount_formatted"]
    assert "₹23,588.20" in pro_y["total_amount_formatted"]

    # 3. RESEARCH Monthly in INR
    res_m = PaymentService.calculate_pricing("RESEARCH", billing_cycle="monthly", currency="INR")
    assert res_m["base_amount"] == 499900  # ₹4,999.00
    # 499900 * 0.18 = 89982 paise (₹899.82)
    assert res_m["tax_amount"] == 89982
    assert res_m["total_amount"] == 589882  # ₹5,898.82
    assert "₹4,999.00" in res_m["base_amount_formatted"]
    assert "₹5,898.82" in res_m["total_amount_formatted"]

    # 4. FREE Plan in INR
    free_m = PaymentService.calculate_pricing("FREE", billing_cycle="monthly", currency="INR")
    assert free_m["base_amount"] == 0
    assert free_m["tax_amount"] == 0
    assert free_m["total_amount"] == 0


def test_usd_pricing_and_tax_calculation():
    # PRO Monthly in USD (0% tax default)
    pro_usd = PaymentService.calculate_pricing("PRO", billing_cycle="monthly", currency="USD")
    assert pro_usd["currency"] == "USD"
    assert pro_usd["currency_symbol"] == "$"
    assert pro_usd["base_amount"] == 1900  # $19.00 in cents
    assert pro_usd["tax_amount"] == 0
    assert pro_usd["total_amount"] == 1900
    assert "$19.00" in pro_usd["total_amount_formatted"]


@pytest.mark.asyncio
async def test_get_pricing_catalog_inr(monkeypatch):
    class _FakeSession:
        pass

    svc = PaymentService(_FakeSession())
    catalog = await svc.get_pricing_catalog("INR")

    assert catalog.currency == "INR"
    assert catalog.currency_symbol == "₹"
    assert catalog.tax_rate == 18.0
    assert catalog.tax_name == "GST"
    assert len(catalog.plans) == 4

    plan_codes = [p.plan_code for p in catalog.plans]
    assert plan_codes == ["FREE", "PRO", "RESEARCH", "CUSTOM"]

    pro = next(p for p in catalog.plans if p.plan_code == "PRO")
    assert pro.monthly_base_amount == 199900
    assert pro.monthly_tax_amount == 35982
    assert pro.monthly_total_amount == 235882
    assert pro.saved_horoscopes_limit == 50


def test_api_get_pricing_endpoint():
    with TestClient(app) as client:
        # 1. Default INR
        res = client.get("/api/v1/payments/pricing")
        assert res.status_code == 200
        data = res.json()
        assert data["currency"] == "INR"
        assert data["currency_symbol"] == "₹"
        assert data["tax_rate"] == 18.0
        assert len(data["plans"]) == 4

        # 2. USD query
        res_usd = client.get("/api/v1/payments/pricing?currency=USD")
        assert res_usd.status_code == 200
        data_usd = res_usd.json()
        assert data_usd["currency"] == "USD"
        assert data_usd["currency_symbol"] == "$"
