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


class AllShadbalaResponse(BaseModel):
    """
    Every implemented Shadbala component/sub-component, grouped exactly
    as ShadbalaEngine's compute_*() methods group them. No total sum is
    provided — see module docstring.
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
