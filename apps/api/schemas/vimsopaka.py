"""
AstroOS — Vimsopaka Bala API Schemas

Pydantic request/response models for the Vimsopaka Bala endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from apps.api.schemas.shadbala import ShadbalaRequest


class VargaDignityScoreResponse(BaseModel):
    """Placement, dignity, and score for a planet in one divisional chart."""

    varga: str
    varga_rashi: str
    dignity: str
    weight: float
    base_points: float
    weighted_points: float


class VimsopakaSchemeResponse(BaseModel):
    """Vimsopaka Bala result for one planet in one Varga scheme."""

    scheme_name: str
    total_weight: float = 20.0
    vimsopaka_score: float
    category: str
    varga_breakdown: list[VargaDignityScoreResponse]


class VimsopakaPlanetResponse(BaseModel):
    """Vimsopaka Bala results across all 4 classical schemes for one planet."""

    planet: str
    shadvarga: VimsopakaSchemeResponse
    saptavarga: VimsopakaSchemeResponse
    dasavarga: VimsopakaSchemeResponse
    shodasavarga: VimsopakaSchemeResponse


class VimsopakaListResponse(BaseModel):
    """Response containing Vimsopaka Bala calculations for all grahas."""

    planets: list[VimsopakaPlanetResponse]


class VimsopakaRequest(ShadbalaRequest):
    """Request body for computing Vimsopaka Bala components from birth data."""
