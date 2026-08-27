"""AstroOS — Account & User Dashboard Schemas (Phase 9)"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from apps.api.schemas.payment import PaymentResponse


class DashboardSummaryResponse(BaseModel):
    """Aggregated dashboard summary for practitioner overview."""
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: str
    display_name: str
    role: str
    status: str
    plan_code: str
    plan_name: str
    subscription_status: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    is_in_grace_period: bool = False
    saved_horoscopes_count: int = 0
    saved_horoscopes_limit: Optional[int] = 5
    research_runs_used: int = 0
    research_runs_limit: Optional[int] = 0
    max_storage_mb: Optional[int] = 50
    recent_payments: list[PaymentResponse] = []
    total_payments_count: int = 0
