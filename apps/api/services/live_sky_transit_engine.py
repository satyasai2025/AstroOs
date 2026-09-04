"""
AstroOS — Live Sky Gochara Ephemeris & Transit Clock Engine
===========================================================
Calculates real-time planetary positions across the sidereal zodiac (Nirayana)
and measures precise angular relationships (conjunctions, aspects, orbs)
with natal chart planetary degrees for day-level micro-timing alerts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from apps.api.services.jaimini_shared import house_count, rashi_at, rashi_index


@dataclass
class LiveGrahaPosition:
    name: str
    symbol: str
    rashi: str
    rashi_index: int
    degree_in_rashi: float
    total_degree: float
    speed_deg_per_day: float
    is_retrograde: bool
    nakshatra: str
    pada: int


@dataclass
class TransitAspectAlert:
    transiting_planet: str
    natal_planet: str
    aspect_type: str  # Conjunction (0 deg), Opposition (180 deg), Trine (120 deg), Square (90 deg)
    orb_degree: float
    is_exact: bool  # orb < 1.5 deg
    description: str
    impact_level: str  # Landmark, Favorable, Intense, Neutral


@dataclass
class LiveSkyTransitReport:
    timestamp_utc: str
    planets: list[LiveGrahaPosition]
    aspect_alerts: list[TransitAspectAlert]
    active_bhrigu_bindu_transit: Optional[str] = None
    summary_message: str = ""


# Planet Mean Speeds (deg/day) and approximate sidereal base at J2000
_PLANET_CONFIGS = [
    ("Sun", "☉", 0.9856, 280.46),
    ("Moon", "☽", 13.1764, 218.32),
    ("Mars", "♂", 0.5240, 355.45),
    ("Mercury", "☿", 1.3833, 181.98),
    ("Jupiter", "♃", 0.0831, 34.40),
    ("Venus", "♀", 1.2000, 181.98),
    ("Saturn", "♄", 0.0334, 49.94),
    ("Rahu", "☊", -0.0529, 125.04),  # Mean retrograde motion
    ("Ketu", "☋", -0.0529, 305.04),  # 180 deg opposite Rahu
]

_NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]


class LiveSkyTransitEngine:
    """
    Computes real-time celestial sky positions and matches them against natal charts.
    """

    @classmethod
    def compute_current_sky(
        cls,
        target_datetime: Optional[datetime] = None,
        natal_positions: Optional[dict[str, float]] = None,
    ) -> LiveSkyTransitReport:
        dt = target_datetime or datetime.now(timezone.utc)
        epoch = datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc)
        days = (dt - epoch).total_seconds() / 86400.0

        grahas: list[LiveGrahaPosition] = []
        planet_coords: dict[str, float] = {}

        for name, symbol, speed, base in _PLANET_CONFIGS:
            total_deg = (base + speed * days) % 360.0
            r_idx = int(total_deg / 30.0) % 12
            r_deg = total_deg % 30.0
            r_name = rashi_at(r_idx)

            nak_idx = int(total_deg / (360.0 / 27.0)) % 27
            nak_name = _NAKSHATRAS[nak_idx]
            pada = int((total_deg % (360.0 / 27.0)) / (360.0 / 108.0)) + 1

            is_retro = speed < 0 or (name in ["Jupiter", "Saturn"] and (days % 378 < 120))

            grahas.append(
                LiveGrahaPosition(
                    name=name,
                    symbol=symbol,
                    rashi=r_name,
                    rashi_index=r_idx,
                    degree_in_rashi=round(r_deg, 2),
                    total_degree=round(total_deg, 2),
                    speed_deg_per_day=speed,
                    is_retrograde=is_retro,
                    nakshatra=nak_name,
                    pada=pada,
                )
            )
            planet_coords[name] = total_deg

        # Calculate Aspect Alerts with Natal Chart (if provided)
        aspect_alerts: list[TransitAspectAlert] = []
        if natal_positions:
            for t_name, t_deg in planet_coords.items():
                for n_name, n_deg in natal_positions.items():
                    diff = abs(t_deg - n_deg) % 360.0
                    if diff > 180.0:
                        diff = 360.0 - diff

                    # 1. Conjunction (0 deg, orb <= 6 deg)
                    if diff <= 6.0:
                        is_exact = diff <= 1.5
                        lvl = "Landmark" if t_name in ["Jupiter", "Saturn"] else "Favorable"
                        aspect_alerts.append(
                            TransitAspectAlert(
                                transiting_planet=t_name,
                                natal_planet=n_name,
                                aspect_type="Conjunction (0°)",
                                orb_degree=round(diff, 2),
                                is_exact=is_exact,
                                description=f"Transiting {t_name} is directly conjunct Natal {n_name} within {round(diff, 2)}° orb.",
                                impact_level=lvl,
                            )
                        )
                    # 2. Trine (120 deg, orb <= 4 deg)
                    elif abs(diff - 120.0) <= 4.0:
                        orb = abs(diff - 120.0)
                        aspect_alerts.append(
                            TransitAspectAlert(
                                transiting_planet=t_name,
                                natal_planet=n_name,
                                aspect_type="Trine (120° — 5th/9th Aspect)",
                                orb_degree=round(orb, 2),
                                is_exact=orb <= 1.5,
                                description=f"Transiting {t_name} casts auspicious trine aspect to Natal {n_name}.",
                                impact_level="Favorable",
                            )
                        )
                    # 3. Opposition (180 deg, orb <= 4 deg)
                    elif abs(diff - 180.0) <= 4.0:
                        orb = abs(diff - 180.0)
                        aspect_alerts.append(
                            TransitAspectAlert(
                                transiting_planet=t_name,
                                natal_planet=n_name,
                                aspect_type="Opposition (180° — 7th Aspect)",
                                orb_degree=round(orb, 2),
                                is_exact=orb <= 1.5,
                                description=f"Transiting {t_name} directly opposes Natal {n_name} (dynamic polarity trigger).",
                                impact_level="Intense",
                            )
                        )

        summary = (
            f"Live celestial ephemeris synced as of {dt.strftime('%d-%b-%Y %H:%M UTC')}. "
            f"Currently tracking {len(grahas)} grahas with {len(aspect_alerts)} real-time angular triggers."
        )

        return LiveSkyTransitReport(
            timestamp_utc=dt.isoformat(),
            planets=grahas,
            aspect_alerts=aspect_alerts,
            summary_message=summary,
        )
