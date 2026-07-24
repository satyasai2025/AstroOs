"""
AstroOS — Nakshatra Knowledge API Schemas

Pydantic response models for the nakshatra reference-catalogue endpoints
(GET /knowledge/nakshatras, GET /knowledge/nakshatras/{id}). Mirrors the
style of schemas/conflict.py — see routers/knowledge.py's /conflicts
routes for the precedent this was built from.
"""

from __future__ import annotations

from pydantic import BaseModel


class NakshatraDeityResponse(BaseModel):
    name: str = ""
    description: str = ""
    attributes: list[str] = []


class NakshatraShaktiResponse(BaseModel):
    name: str = ""
    meaning: str = ""
    power: str = ""


class NakshatraPadaResponse(BaseModel):
    pada: int
    degrees: str = ""
    rashi: str = ""
    navamsha_rashi: str = ""


class NakshatraNatureResponse(BaseModel):
    temperament: str = ""
    guna: str = ""
    gana: str = ""
    yoni: str = ""
    nadi: str = ""


class NakshatraSourceResponse(BaseModel):
    ref: str = ""
    claim: str = ""
    confidence: str = "high"


class NakshatraSummaryResponse(BaseModel):
    """Lightweight entry for the 27-nakshatra grid (Level 6)."""
    id: str
    name: str
    sequential: int
    ruler: str = ""
    classical_name: str = ""


class NakshatraListResponse(BaseModel):
    nakshatras: list[NakshatraSummaryResponse]
    total: int


class NakshatraDetailResponse(BaseModel):
    """Full classical reference entry for one nakshatra (Level 2)."""
    id: str
    name: str
    sequential: int
    aliases: list[str] = []
    classical_name: str = ""
    devanagari: str = ""
    meaning: str = ""
    ruler: str = ""
    starting_degree: float = 0.0
    ending_degree: float = 0.0
    rashi_span: list[str] = []
    padas: list[NakshatraPadaResponse] = []
    deity: NakshatraDeityResponse | None = None
    shakti: NakshatraShaktiResponse | None = None
    nature: NakshatraNatureResponse | None = None
    karakatvas: list[str] = []
    compatible_nakshatras: list[str] = []
    incompatible_nakshatras: list[str] = []
    sources: list[NakshatraSourceResponse] = []
    notes: str = ""
