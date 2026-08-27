"""AstroOS — Payment & Pricing Schemas (Phase 6 & 8)"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

PaymentStatusLiteral = Literal["pending", "succeeded", "failed", "refunded", "cancelled"]
PaymentProviderLiteral = Literal["mock", "stripe", "razorpay"]
BillingCycleLiteral = Literal["monthly", "yearly"]


# ── Requests ──────────────────────────────────────────────────────────────────


class CheckoutSessionRequest(BaseModel):
    """Request to initiate a checkout session for subscribing to a plan."""
    plan_code: str = Field(min_length=2, max_length=50, description="Target plan code, e.g. 'PRO', 'RESEARCH'")
    billing_cycle: BillingCycleLiteral = Field(default="monthly", description="Billing cycle frequency")
    currency: Optional[str] = Field(default="INR", description="Payment currency: 'INR' (India-first ₹) or 'USD'")
    success_url: Optional[str] = Field(default=None, description="URL redirect on checkout success")
    cancel_url: Optional[str] = Field(default=None, description="URL redirect on checkout cancel")


class CustomerPortalRequest(BaseModel):
    """Request to generate a customer billing portal session URL."""
    return_url: Optional[str] = Field(default=None, description="URL redirect upon exiting customer portal")


class RefundRequest(BaseModel):
    """Admin request to trigger/record a refund."""
    amount: Optional[int] = Field(default=None, description="Amount in lowest denomination to refund, or None for full refund")
    reason: Optional[str] = Field(default=None, max_length=500, description="Reason for refund")


# ── Responses ────────────────────────────────────────────────────────────────


class PricingPlanDetail(BaseModel):
    """Authoritative backend pricing and tax breakdown for a plan."""
    plan_code: str
    name: str
    description: str
    currency: str
    currency_symbol: str
    tax_rate: float
    tax_name: str
    monthly_base_amount: int
    monthly_base_formatted: str
    monthly_tax_amount: int
    monthly_tax_formatted: str
    monthly_total_amount: int
    monthly_total_formatted: str
    yearly_base_amount: int
    yearly_base_formatted: str
    yearly_tax_amount: int
    yearly_tax_formatted: str
    yearly_total_amount: int
    yearly_total_formatted: str
    saved_horoscopes_limit: Optional[int] = None
    research_projects_monthly_limit: Optional[int] = None
    features: list[str] = []


class PricingCatalogResponse(BaseModel):
    """Complete backend-driven pricing catalog with tax breakdowns."""
    currency: str
    currency_symbol: str
    supported_currencies: list[str]
    tax_rate: float
    tax_name: str
    plans: list[PricingPlanDetail]


class CheckoutSessionResponse(BaseModel):
    """Result of checkout session creation with detailed tax breakdown."""
    session_id: str
    checkout_url: str
    provider: PaymentProviderLiteral
    plan_code: str
    currency: str
    amount: int
    base_amount: Optional[int] = None
    tax_amount: Optional[int] = None
    tax_rate: Optional[float] = None
    total_amount: Optional[int] = None

    def model_post_init(self, __context: Any) -> None:
        if self.total_amount is None:
            self.total_amount = self.amount
        if self.base_amount is None:
            self.base_amount = self.amount
        if self.tax_amount is None:
            self.tax_amount = 0
        if self.tax_rate is None:
            self.tax_rate = 0.0


class CustomerPortalResponse(BaseModel):
    """Result of customer portal link creation."""
    portal_url: str
    provider: PaymentProviderLiteral


class PaymentResponse(BaseModel):
    """Payment record details including tax breakdown."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    subscription_id: Optional[uuid.UUID] = None
    plan_id: Optional[uuid.UUID] = None
    provider: PaymentProviderLiteral
    provider_payment_id: Optional[str] = None
    provider_order_id: Optional[str] = None
    amount: int  # Total payable amount
    base_amount: Optional[int] = None
    tax_amount: Optional[int] = None
    tax_rate: Optional[float] = None
    currency: str
    status: PaymentStatusLiteral
    payment_method: Optional[str] = None
    receipt_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaymentHistoryResponse(BaseModel):
    """List of payment records for a user."""
    items: list[PaymentResponse]
    total: int


class PaymentConfigResponse(BaseModel):
    """Public gateway configuration for client/frontend."""
    active_provider: PaymentProviderLiteral
    publishable_key: Optional[str] = None
    default_currency: str = "INR"
    supported_currencies: list[str] = ["INR", "USD"]
    tax_rate_inr: float = 18.0
    tax_rate_usd: float = 0.0
    supported_providers: list[str] = ["mock", "stripe", "razorpay"]


class WebhookProcessingResult(BaseModel):
    """Outcome of processing an incoming webhook."""
    status: Literal["processed", "ignored", "failed"]
    provider: str
    event_id: str
    event_type: str
    message: Optional[str] = None
