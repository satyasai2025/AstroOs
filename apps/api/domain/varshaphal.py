"""
AstroOS — Varshaphal (Tajika annual chart) domain models.

Stage 1: the Varsha Pravesh (solar-return) chart and Muntha.
Stage 2: Tajika aspects (Ithasala/Isharpha) between the 7 classical Grahas.

Stage 3: Year Lord (Panchadhikari) — the 5-candidate selection rule,
cross-checked against PyJHora (github.com/naturalstupid/PyJHora,
jhora/horoscope/transit/tajaka.py — a library verified against ~6800
tests from P.V.R. Narasimha Rao's book). One deliberate simplification:
the final tie-break there falls through to Panchvargiya Bala (a whole
separate 5-source planetary strength system not built here); this
implementation falls back directly to the first candidate (the Sun/Moon
sign lord) in that rare case instead. See YearLordInfo.selection_method.

Stage 4: Sahams (Punya, Vidya) — the classical A-B+C longitude formula,
cross-checked against PyJHora's jhora/horoscope/transit/saham.py (same
verified source as Stage 3). Only these two are built so far; PyJHora
lists 36 total, each with its own A/B/C planet triple.

Mudda / Patyayini annual dasha systems are a later stage, not yet built.
"""

from __future__ import annotations

from dataclasses import dataclass

from apps.api.domain.ephemeris import EphemerisResult


@dataclass(frozen=True)
class MunthaInfo:
    """Progressed point: natal Ascendant Rashi advanced by the varsha year number."""
    rashi: str
    rashi_index: int      # 0=Mesha … 11=Meena
    house_number: int      # 1–12, house of this Rashi in the Varsha chart (Whole Sign)


@dataclass(frozen=True)
class TajikaAspect:
    """
    A Tajika aspect relationship between two planets at one of the 5
    classical aspect angles (0=conjunction, 60=sextile, 90=square,
    120=trine, 180=opposition).
    """
    planet_a: str
    planet_b: str
    aspect_angle: int          # 0 | 60 | 90 | 120 | 180
    current_orb_deg: float      # |separation - aspect_angle|, always >= 0
    is_applying: bool            # separation is moving toward the aspect angle
    is_ithasala: bool            # applying AND perfects before either planet leaves its sign
    is_isharpha: bool             # separating, having perfected the aspect within the last day
    days_to_exact: float | None    # None if separating or aspect angle already exact


@dataclass(frozen=True)
class YearLordInfo:
    """Panchadhikari (5-candidate) Year Lord selection for the Varsha chart."""
    candidates: tuple[str, ...]     # the (deduped) up-to-5 candidate planets, in priority order
    selected: str                    # the chosen Year Lord
    selection_method: str             # "benefic_aspect" | "malefic_aspect" | "fallback_first_candidate"


@dataclass(frozen=True)
class SahamInfo:
    """A Tajika sensitive point (Saham), computed as a longitude via A - B + C."""
    name: str
    sidereal_longitude: float
    rashi: str


@dataclass(frozen=True)
class VarshaphalResult:
    """Annual chart for one solar-return year."""
    varsha_year: int         # the Nth solar return since birth (1 = first birthday)
    solar_return_jd: float    # exact moment Sun returns to its natal sidereal longitude
    varsha_chart: EphemerisResult
    muntha: MunthaInfo
    tajika_aspects: tuple[TajikaAspect, ...]
    year_lord: YearLordInfo
    sahams: tuple[SahamInfo, ...]
