"""
AstroOS — Mundane Astrology (Medini Jyotisha / Samhita) Domain Models
Classical References: Brihat Samhita (Varahamihira), Bhavishya Phala Bhaskara, Narada Samhita.
Defines domain dataclasses for:
  - Mundane Ingresses (Chaitra Shukla Pratipada, 4 Cardinal Sankrantis, Aridra Pravesha)
  - Planetary Cabinet (Nava Nayakas / 9 Cosmic Ministers)
  - Standalone Mundane Eclipses (Grahanas) & Duration-Impact Models
  - Kurma Chakra (9-Directional Geopolitical & Seismic Sectors)
  - 12 Mundane Bhavas & Comprehensive National Forecasts
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Tuple

from apps.api.domain.horoscope import D1Chart


class IngressType(str, Enum):
    CHAITRA_SHUKLA_PRATIPADA = "chaitra_shukla_pratipada"
    MESHA_SANKRANTI = "mesha_sankranti"
    KARKA_SANKRANTI = "karka_sankranti"
    TULA_SANKRANTI = "tula_sankranti"
    MAKARA_SANKRANTI = "makara_sankranti"
    ARIDRA_PRAVESHA = "aridra_pravesha"


class EclipseType(str, Enum):
    SOLAR_TOTAL = "solar_total"
    SOLAR_ANNULAR = "solar_annular"
    SOLAR_PARTIAL = "solar_partial"
    LUNAR_TOTAL = "lunar_total"
    LUNAR_PARTIAL = "lunar_partial"


class KurmaDirection(str, Enum):
    CENTER = "center"               # Madhya Desha
    EAST = "east"                   # Purva
    SOUTH_EAST = "south_east"       # Agneya
    SOUTH = "south"                 # Dakshina
    SOUTH_WEST = "south_west"       # Nairritya
    WEST = "west"                   # Pashchima
    NORTH_WEST = "north_west"       # Vayavya
    NORTH = "north"                 # Uttara
    NORTH_EAST = "north_east"       # Ishanya


@dataclass(frozen=True)
class MundaneIngressMoment:
    """Calculated astronomical ingress moment."""
    ingress_type: IngressType
    timestamp_utc: datetime
    sun_longitude: float
    moon_longitude: float
    weekday: str
    weekday_lord: str


@dataclass(frozen=True)
class MundaneIngressChart:
    """Horoscope cast for a nation's capital at an exact ingress moment."""
    ingress_moment: MundaneIngressMoment
    country_name: str
    capital_city: str
    latitude: float
    longitude: float
    chart: D1Chart
    ascendant_rashi: str
    ascendant_lord: str
    tenth_house_rashi: str
    tenth_house_lord: str


@dataclass(frozen=True)
class CabinetMinister:
    """Individual portfolio in the 9-minister cosmic governance council (Nava Nayakas)."""
    portfolio: str  # e.g., 'Raja (King)', 'Mantri (Prime Minister)', 'Senadhipati (Defense)'
    planet: str
    basis_ingress: str
    is_benefic: bool
    impact_summary: str


@dataclass(frozen=True)
class PlanetaryCabinet:
    """Annual cosmic governance council (Nava Nayakas) for the astrological year."""
    year: int
    ministers: tuple[CabinetMinister, ...]
    raja: CabinetMinister
    mantri: CabinetMinister
    senadhipati: CabinetMinister
    meghadhipati: CabinetMinister
    overall_balance_score: float  # 0.0 to 100.0
    governance_climate: str
    classical_summary: str


@dataclass(frozen=True)
class MundaneEclipse:
    """Calculated solar or lunar eclipse and its geopolitical impact profile."""
    eclipse_type: EclipseType
    peak_utc: datetime
    eclipsed_rashi: str
    eclipsed_nakshatra: str
    node_involved: str  # 'Rahu' or 'Ketu'
    duration_hours: float
    impact_duration_months: float  # Classical rule: solar hours -> years (or 12*months), lunar hours -> months
    afflicted_directions: tuple[KurmaDirection, ...]
    impact_summary: str


@dataclass(frozen=True)
class KurmaSectorStatus:
    """State of a single directional sector in the 9-fold Kurma Chakra."""
    direction: KurmaDirection
    nakshatras: tuple[str, ...]
    traditional_regions: tuple[str, ...]
    transiting_malefics: tuple[str, ...]
    transiting_benefics: tuple[str, ...]
    is_afflicted: bool
    severity: str  # 'None', 'Low', 'Moderate', 'Severe'
    risk_summary: str


@dataclass(frozen=True)
class KurmaChakraState:
    """Global geographic affliction map across all 9 Kurma Chakra sectors."""
    evaluated_at: datetime
    sectors: tuple[KurmaSectorStatus, ...]
    highest_risk_directions: tuple[KurmaDirection, ...]
    summary: str


@dataclass(frozen=True)
class MundaneBhavaEvaluation:
    """Evaluation of a specific mundane house in a national chart."""
    house_number: int
    signification: str  # e.g., 'Public Health & Nation', 'Treasury & Economy', etc.
    rashi: str
    lord: str
    occupants: tuple[str, ...]
    strength_score: float  # 0.0 to 100.0
    outlook: str


@dataclass(frozen=True)
class NationalForecast:
    """Comprehensive annual mundane forecast for a specific nation."""
    country_name: str
    capital_city: str
    year: int
    chaitra_chart: MundaneIngressChart
    planetary_cabinet: PlanetaryCabinet
    active_eclipses: tuple[MundaneEclipse, ...]
    kurma_state: KurmaChakraState
    bhava_evaluations: tuple[MundaneBhavaEvaluation, ...]
    economic_index: float  # 0.0 to 100.0
    defense_security_index: float  # 0.0 to 100.0
    political_stability_index: float  # 0.0 to 100.0
    public_health_index: float  # 0.0 to 100.0
    executive_summary: str
