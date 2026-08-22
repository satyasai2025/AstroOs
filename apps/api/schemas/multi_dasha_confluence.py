"""
AstroOS — Priority 12: Pydantic Schemas for Multi-Dasha Confluence API
"""

from __future__ import annotations

from datetime import date
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ConfluenceEvaluateRequest(BaseModel):
    objective: str = Field(default="marriage", description="Event objective, e.g. marriage, career, relocation")
    target_start_date: date = Field(..., description="Start date for confluence evaluation")
    target_end_date: date = Field(..., description="End date for confluence evaluation")


class DashaIntervalSchema(BaseModel):
    system_name: str
    lord_or_rashi: str
    level: str
    start_date: date
    end_date: date
    houses_activated: List[int]
    promise_score: float


class ConfluenceWindowSchema(BaseModel):
    window_id: str
    start_date: date
    end_date: date
    duration_days: int
    overlapping_systems: List[str]
    system_count: int
    confluence_density_score: float
    activated_houses: List[int]
    primary_objective: str


class ConfluenceMatrixResponse(BaseModel):
    chart_id: str
    target_start_date: date
    target_end_date: date
    objective: str
    total_intervals_evaluated: int
    total_confluence_windows: int
    confluence_windows: List[ConfluenceWindowSchema]
    peak_confluence_window: Optional[ConfluenceWindowSchema]
    consensus_profile_used: str
