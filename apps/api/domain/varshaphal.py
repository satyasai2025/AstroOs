from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

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
    deeptamsha_orb_limit: float = 12.0  # Average Deeptamsha of the two planets
    within_deeptamsha: bool = True     # current_orb_deg <= deeptamsha_orb_limit


@dataclass(frozen=True)
class PanchavargiyaBala:
    """
    Classical 5-fold Tajika planetary strength (*Panchavargiya Bala*).
    Max raw points = 30 + 20 + 15 + 10 + 5 = 80 points.
    Visheshika Bala = Total Points / 4 (Max 20 units).
    """
    planet: str
    kshetra_bala: float       # 0–30 (Sign position: Own 30, Friend 22.5, Neutral 15, Enemy 7.5)
    uchcha_bala: float        # 0–20 (Distance from deep debilitation point)
    hadda_bala: float         # 0–15 (Hadda / Terms position: Own 15, Friend 11.25, Neutral 7.5, Enemy 3.75)
    drekkana_bala: float      # 0–10 (Decanate position: Own 10, Friend 7.5, Neutral 5, Enemy 2.5)
    navamsha_bala: float      # 0–5  (Navamsha position: Own 5, Friend 3.75, Neutral 2.5, Enemy 1.25)
    total_score: float        # 0–80 raw total score
    visheshika_bala: float    # 0–20 Visheshika points (total_score / 4)
    strength_category: str    # "POORNA" (>15) | "MADHYA" (10-15) | "ALPA" (5-10) | "HEENA" (<5)
    hadda_lord: str = ""
    drekkana_lord: str = ""
    navamsha_lord: str = ""


@dataclass(frozen=True)
class TajikaYoga:
    """One of the 16 Classical Tajika Yogas (Shodasha Tajika Yogas)."""
    yoga_name: str           # e.g., "Ithasala", "Isharpha", "Nakta", "Yamaya", "Kamboola", "Ikabala", etc.
    category: str            # "BENEFIC" | "MALEFIC" | "NEUTRAL"
    planets: tuple[str, ...] # Participating Grahas
    is_formed: bool          # Whether the yoga criteria are fully satisfied
    description: str         # Classical textual description and interpretation
    details: dict[str, Any]  # Key attributes (orb, intermediary planet, strength, etc.)


@dataclass(frozen=True)
class MuddaDashaPeriod:
    """Vimshottari Mudda Dasha annual planetary period (365.2425 days)."""
    planet: str
    start_jd: float
    end_jd: float
    duration_days: float
    start_date: str
    end_date: str
    antardashas: tuple[MuddaDashaPeriod, ...] = ()


@dataclass(frozen=True)
class PatyayiniDashaPeriod:
    """Patyayini Dasha annual planetary period (based on planetary longitudes / Krishnamsha)."""
    planet: str
    start_jd: float
    end_jd: float
    duration_days: float
    krishnamsha_deg: float
    start_date: str
    end_date: str


@dataclass(frozen=True)
class MasaPraveshChart:
    """Monthly solar return chart (Masa Pravesh) for month N of the Varsha year."""
    month_number: int              # 1 to 12
    solar_longitude_target: float  # natal_sun + (month_number - 1) * 30.0 mod 360
    solar_return_jd: float
    solar_return_date: str
    chart: EphemerisResult
    muntha_rashi: str
    masa_lord: str


@dataclass(frozen=True)
class YearLordInfo:
    """Panchadhikari (5-candidate) Year Lord selection for the Varsha chart."""
    candidates: tuple[str, ...]     # the (deduped) up-to-5 candidate planets, in priority order
    selected: str                    # the chosen Year Lord (Varsheshwara)
    selection_method: str             # "panchavargiya_bala" | "benefic_aspect" | "malefic_aspect" | "fallback_first_candidate"
    candidate_balas: dict[str, float] = None  # Panchavargiya Visheshika Bala for each candidate


@dataclass(frozen=True)
class SahamInfo:
    """A Tajika sensitive point (Saham), computed as a longitude via A - B + C."""
    name: str
    sidereal_longitude: float
    rashi: str


@dataclass(frozen=True)
class VarshaphalResult:
    """Annual chart for one solar-return year with full Classical Tajika components."""
    varsha_year: int         # the Nth solar return since birth (1 = first birthday)
    solar_return_jd: float    # exact moment Sun returns to its natal sidereal longitude
    varsha_chart: EphemerisResult
    muntha: MunthaInfo
    tajika_aspects: tuple[TajikaAspect, ...]
    year_lord: YearLordInfo
    sahams: tuple[SahamInfo, ...]
    panchavargiya_bala: tuple[PanchavargiyaBala, ...] = ()
    tajika_yogas: tuple[TajikaYoga, ...] = ()
    mudda_dasha: tuple[MuddaDashaPeriod, ...] = ()
    patyayini_dasha: tuple[PatyayiniDashaPeriod, ...] = ()
