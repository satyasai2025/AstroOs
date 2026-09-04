"""
AstroOS — Avastha API Schemas

Pydantic response models for the Avastha (planetary state) endpoint.
Reuses ShadbalaRequest for the request body (same birth-data shape,
same compute-only pattern) rather than duplicating it.
"""

from __future__ import annotations

from pydantic import BaseModel


class AvasthaResponse(BaseModel):
    """Both computed Avasthas for one planet."""

    planet: str
    baladi_avastha: str
    baladi_trace: list[str] = []
    deeptadi_avastha: str
    deeptadi_trace: list[str] = []


class AvasthaListResponse(BaseModel):
    avasthas: list[AvasthaResponse]
    not_implemented: list[str] = [
        "jagradadi_avastha",
    ]
