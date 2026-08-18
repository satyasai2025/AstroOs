"""
AstroOS — Statistical Reporting & Decision Domain Contracts

Defines domain models for production deployment recommendations, risk assessments,
and publication-ready statistical research reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ProductionDecisionStatus(str, Enum):
    PROMOTE_TO_PRODUCTION = "PROMOTE_TO_PRODUCTION"
    MAINTAIN_BASELINE = "MAINTAIN_BASELINE"
    INCONCLUSIVE_NEEDS_MORE_DATA = "INCONCLUSIVE_NEEDS_MORE_DATA"
    REJECT_REGRESSION = "REJECT_REGRESSION"


@dataclass(frozen=True)
class DecisionRecommendation:
    """Automated scientific decision on whether a candidate profile should be promoted."""

    status: ProductionDecisionStatus
    recommended_profile_id: str
    baseline_profile_id: str
    confidence_score: float         # 0.0 to 1.0
    key_evidence_drivers: tuple[str, ...]
    risk_factors: tuple[str, ...]
    sample_size_adequate: bool
    requires_human_signoff: bool


@dataclass(frozen=True)
class StatisticalResearchReport:
    """Full self-contained research report formatted for peer review and documentation."""

    experiment_id: str
    benchmark_id: str
    benchmark_version: str
    decision: DecisionRecommendation
    executive_summary: str
    markdown_content: str
    json_content: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now())