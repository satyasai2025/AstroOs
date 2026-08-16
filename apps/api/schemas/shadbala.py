"""
AstroOS — Shadbala API Schemas

Pydantic request/response models for the Shadbala endpoints. Mirrors
the request body shape used by divisional/dasha endpoints
(birth_datetime_utc, latitude, longitude, ayanamsa, house_system) since
ShadbalaEngine operates on the same D1Chart those engines build from
that data, and its cross-varga / sunrise-search sub-components
(Saptavargaja, Ojayugmarasyamsa, Tribhaga, Nathonnata, Dina-Hora Bala)
need exactly that same birth data again.

ShadbalaEngine deliberately does not expose a "total Shadbala" sum —
see services/shadbala_engine.py's module docstring: with some
sub-components still out of scope (Varsha/Masa lord), a sum would
misrepresent an incomplete result as complete. These schemas mirror
that: every component group is returned separately, never summed.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput


# ── Request ───────────────────────────────────────────────────────────────────


class ShadbalaRequest(BirthDataInput):
    """Request body for computing Shadbala components from birth data."""


# ── Response pieces ───────────────────────────────────────────────────────────


class BalaComponentResponse(BaseModel):
    """One Shadbala component's contribution for one planet."""

    component_id: str
    component_name: str
    rule_version: str
    planet: str
    value_shashtiamsas: float = Field(description="Value in Shashtiamsas (60ths of a Rupa).")
    trace: list[str] = Field(default_factory=list)


class Phase1ComponentsResponse(BaseModel):
    """Naisargika + Dig + Drik Bala."""

    naisargika_bala: list[BalaComponentResponse]
    dig_bala: list[BalaComponentResponse]
    drik_bala: list[BalaComponentResponse]


class Phase2ComponentsResponse(BaseModel):
    """Chesta + Paksha + Ayana + Yuddha Bala (Kala Bala sub-components)."""

    chesta_bala: list[BalaComponentResponse]
    paksha_bala: list[BalaComponentResponse]
    ayana_bala: list[BalaComponentResponse]
    yuddha_bala: list[BalaComponentResponse]


class SthanaBalaComponentsResponse(BaseModel):
    """Uchcha + Kendradi + Drekkana Bala (3 of Sthana Bala's 5 sub-components)."""

    uchcha_bala: list[BalaComponentResponse]
    kendradi_bala: list[BalaComponentResponse]
    drekkana_bala: list[BalaComponentResponse]


class SubBalaCheckResponse(BaseModel):
    """Pass/fail status of an individual sub-bala criteria."""

    bala_key: str
    bala_name: str
    obtained_virupas: float
    required_virupas: float
    passed: bool


class SaravaliPlanetSummaryResponse(BaseModel):
    """Complete Saravali Shadbala summary for a single planet."""

    planet: str
    planet_display_name: str

    # 6 Main Balas (Virupas)
    sthana_bala_virupas: float
    dig_bala_virupas: float
    kala_bala_virupas: float
    chesta_bala_virupas: float
    naisargika_bala_virupas: float
    drig_bala_virupas: float

    # Sthana Sub-components
    uchcha_bala_virupas: float
    saptavargaja_bala_virupas: float
    ojayugmarasyamsa_bala_virupas: float
    kendradi_bala_virupas: float
    drekkana_bala_virupas: float

    # Kala Sub-components
    nathonnata_bala_virupas: float
    paksha_bala_virupas: float
    tribhaga_bala_virupas: float
    dina_hora_bala_virupas: float
    ayana_bala_virupas: float
    yuddha_bala_virupas: float

    # Total Shadbala Pinda
    total_virupas: float
    total_rupas: float
    required_virupas: float
    required_rupas: float
    strength_ratio: float
    percentage: float
    is_strong: bool
    status_label: str
    rank: int

    # Ishta / Kashta
    ishta_bala_virupas: float
    kashta_bala_virupas: float

    # Individual Sub-Bala Checks
    sub_bala_checks: list[SubBalaCheckResponse]
    all_sub_balas_passed: bool


class SaravaliShadbalaReportResponse(BaseModel):
    """Complete aggregated Saravali Shadbala Report for all 7 classical grahas."""

    planets: list[SaravaliPlanetSummaryResponse]
    strongest_planet: str
    weakest_planet: str
    average_strength_ratio: float
    chart_strength_score: float


class AllShadbalaResponse(BaseModel):
    """
    Every implemented Shadbala component/sub-component, grouped exactly
    as ShadbalaEngine's compute_*() methods group them, plus full Saravali
    evaluation summary.
    """

    phase1: Phase1ComponentsResponse
    phase2: Phase2ComponentsResponse
    sthana_bala: SthanaBalaComponentsResponse
    saptavargaja_bala: list[BalaComponentResponse]
    ojayugmarasyamsa_bala: list[BalaComponentResponse]
    tribhaga_bala: list[BalaComponentResponse]
    nathonnata_bala: list[BalaComponentResponse]
    dina_hora_bala: list[BalaComponentResponse]
    ishta_bala: list[BalaComponentResponse] = Field(default_factory=list)
    kashta_bala: list[BalaComponentResponse] = Field(default_factory=list)
    implemented_components: list[str]
    not_yet_implemented_components: list[str]
    summary: SaravaliShadbalaReportResponse | None = None

