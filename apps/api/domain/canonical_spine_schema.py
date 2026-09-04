"""
AstroOS — Canonical Integration Spine Schema
============================================
The single, authoritative JSON output schema connecting ALL platform calculation
engines for a living birth chart (Janma Kundali).

Architectural Invariant:
  One birth chart input -> Complete Shastric evaluation across all engines:
    1. Ephemeris & Rasi Chart (7 Dignities, Main Strength 1..256, Shadbala)
    2. Bhavachalita Chart (SSS Sripathi Bhava-midpoints & spans)
    3. Shodasha Vargas (D1..D60 with Shashtiamsa Deities)
    4. 5 Dasha Systems (Vimshottari, Ashtottari, Yogini, Kalachakra, Chara)
    5. Ashtakavarga Suite (SAV 337, Prastara, Shodhya Pinda v0.9, Gochara Rekha Filter)
    6. Canonical Drishti (Sphuta 0..60, Bhavesha 50% baseline, Maitri Filter)
    7. Maraka & Badhaka Confluence (5-tier distinct graha mortality risk)
    8. Cross-Engine Invariants & Dasharambha Alignment
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SpineBirthInput:
    native_id: str
    birth_datetime: datetime          # UTC / tz-aware
    latitude: float
    longitude: float
    altitude: float = 0.0
    ayanamsa: str = "lahiri_sss"
    target_query_datetime: Optional[datetime] = None  # defaults to now/birth


@dataclass(frozen=True)
class SpinePlanetPosition:
    planet: str
    sidereal_longitude: float
    rashi: str
    rashi_degree: float
    nakshatra: str
    pada: int
    is_retrograde: bool
    dignity_tier: int                 # 1 (Neecha) to 7 (Uchcha)
    main_strength_units: float        # 2^(tier - 1) -> 1.0 to 64.0 (or 256.0)
    bhava_number: int                 # In Bhavachalita


@dataclass(frozen=True)
class SpineBhavachalitaHouse:
    house_number: int
    rashi: str
    midpoint_deg: float
    span_start_deg: float
    span_end_deg: float
    lord: str
    occupants: list[str]


@dataclass(frozen=True)
class SpineActiveDashaSummary:
    system_name: str                  # "vimshottari", "ashtottari", "yogini", "kalachakra", "chara"
    active_levels: dict[str, str]     # {"MD": "venus", "AD": "mercury", "PD": "mars", ...}
    start_date: str
    end_date: str


@dataclass(frozen=True)
class SpineAshtakavargaSummary:
    sav_rashi_bindus: dict[str, int]  # Rashi -> SAV Bindus
    sav_grand_total: int              # Must be 337
    shodhya_pindas: dict[str, int]    # Planet -> Shodhya Pinda (v0.9-provisional)
    gochara_filter_tier: str          # "all_8_vargas", "seven_grahas", "six_slow_grahas"
    gochara_expected_bindus: int      # 386, 337, or 288


@dataclass(frozen=True)
class SpineDrishtiSummary:
    total_active_aspects: int
    bhavesha_protection_map: dict[int, float] # House -> effective protection virupas (min 30.0)
    total_benefic_transfer_virupas: float
    total_malefic_transfer_virupas: float


@dataclass(frozen=True)
class SpineMarakaBadhakaSummary:
    lagna_modality: str               # "chara", "sthira", "dvisvabhava"
    badhaka_house: int                # 11, 9, or 7
    badhakesh: str
    primary_marakas: list[str]
    active_5tier_maraka_count: int
    is_critical_mortality_risk: bool


@dataclass(frozen=True)
class SpineCrossEngineConsistency:
    sav_checksum_pass: bool           # Total == 337
    dasharambha_bhava_match: bool     # Dasha-Arambha bhava-phala aligns with natal Bhavachalita
    dasha_timeline_conservation: bool # Total Vimshottari == 120 years
    invariant_status: str             # "100% CANONICAL PASS"


@dataclass(frozen=True)
class CanonicalKundaliSpineResponse:
    """The Master Canonical Output containing the living synthesis of all engines."""
    input_params: SpineBirthInput
    planets: list[SpinePlanetPosition]
    bhavachalita_houses: list[SpineBhavachalitaHouse]
    active_dashas: list[SpineActiveDashaSummary]
    ashtakavarga: SpineAshtakavargaSummary
    drishti: SpineDrishtiSummary
    maraka_badhaka: SpineMarakaBadhakaSummary
    cross_engine_consistency: SpineCrossEngineConsistency
    generated_at_utc: str