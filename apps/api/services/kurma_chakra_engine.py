"""
AstroOS — Kurma Chakra (Geopolitical & Geo-Seismic) Engine
Classical Reference: Brihat Samhita (Varahamihira, Ch. 14 Kurma Vibhaga).
Maps the 27 Nakshatras across the 9 cardinal sectors of the celestial tortoise (Kurma),
evaluating transiting malefic vedha, geopolitical tension zones, and seismic vulnerability.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from apps.api.domain.mundane import KurmaChakraState, KurmaDirection, KurmaSectorStatus
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.synastry_engine import _NAKSHATRA_ORDER

_KURMA_SECTORS: dict[KurmaDirection, tuple[tuple[str, ...], tuple[str, ...]]] = {
    KurmaDirection.CENTER: (
        ("krittika", "rohini", "mrigashira"),
        ("North-Central India", "Himalayan Belt", "Capital Regions", "Central Plains"),
    ),
    KurmaDirection.EAST: (
        ("ardra", "punarvasu", "pushya"),
        ("Eastern India", "Bengal", "Myanmar", "East Asia", "Pacific Rim"),
    ),
    KurmaDirection.SOUTH_EAST: (
        ("ashlesha", "magha", "purva_phalguni"),
        ("South-East Asia", "Bay of Bengal coastal zones", "Sundaland", "Maritime trade routes"),
    ),
    KurmaDirection.SOUTH: (
        ("uttara_phalguni", "hasta", "chitra"),
        ("Southern Peninsular territories", "Sri Lanka", "Indian Ocean islands", "Equatorial Africa"),
    ),
    KurmaDirection.SOUTH_WEST: (
        ("swati", "vishakha", "anuradha"),
        ("Arabian Peninsula", "Persian Gulf", "Levant", "South-West Asian corridor"),
    ),
    KurmaDirection.WEST: (
        ("jyeshtha", "mula", "purva_ashadha"),
        ("Western maritime zones", "Mediterranean basin", "Europe", "The Americas"),
    ),
    KurmaDirection.NORTH_WEST: (
        ("uttara_ashadha", "shravana", "dhanishta"),
        ("Central Asian steppes", "North-West frontier", "Anatolia", "Caucasus"),
    ),
    KurmaDirection.NORTH: (
        ("shatabhisha", "purva_bhadrapada", "uttara_bhadrapada"),
        ("Northern Eurasia", "Siberian belt", "Scandinavia", "Arctic zones"),
    ),
    KurmaDirection.NORTH_EAST: (
        ("revati", "ashwini", "bharani"),
        ("Tibetan Plateau", "North-East Himalayas", "Far-East Siberia", "High plateaus"),
    ),
}

_MALEFICS = {"saturn", "mars", "rahu", "ketu", "sun"}
_BENEFICS = {"jupiter", "venus", "mercury", "moon"}


class KurmaChakraEngine:
    """
    Evaluates global geographic vulnerabilities using the 9-sector Kurma Chakra.
    """

    def __init__(self, wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")

    def evaluate_state(self, dt: datetime, ayanamsa: str = "lahiri") -> KurmaChakraState:
        res = self._wrapper.calculate(dt, 0.0, 0.0, ayanamsa)
        planets = res.planet_positions

        # Map each planet to its Nakshatra
        planet_nakshatras: dict[str, str] = {}
        for p in planets:
            nak_idx = int(p.sidereal_longitude / (360.0 / 27.0)) % 27
            planet_nakshatras[p.planet.lower()] = _NAKSHATRA_ORDER[nak_idx]

        sector_statuses: list[KurmaSectorStatus] = []
        highest_risk_dirs: list[KurmaDirection] = []

        for direction, (nakshatras, regions) in _KURMA_SECTORS.items():
            nak_set = set(nakshatras)

            malefics_in_sector: list[str] = []
            benefics_in_sector: list[str] = []

            for p_name, nak in planet_nakshatras.items():
                if nak in nak_set:
                    if p_name in _MALEFICS:
                        malefics_in_sector.append(f"{p_name.capitalize()} in {nak.capitalize()}")
                    elif p_name in _BENEFICS:
                        benefics_in_sector.append(f"{p_name.capitalize()} in {nak.capitalize()}")

            is_afflicted = len(malefics_in_sector) > len(benefics_in_sector)

            if len(malefics_in_sector) >= 2:
                severity = "Severe"
                highest_risk_dirs.append(direction)
                risk_summary = f"High alert: Multiple malefics ({', '.join(malefics_in_sector)}) aspecting or occupying sector. Elevated geopolitical / seismic stress."
            elif len(malefics_in_sector) == 1:
                severity = "Moderate" if not benefics_in_sector else "Low"
                risk_summary = f"Moderate transit activity: {malefics_in_sector[0]}."
            else:
                severity = "None"
                risk_summary = "Harmonious / Peaceful sector under benefic or neutral transit rays."

            sector_statuses.append(KurmaSectorStatus(
                direction=direction,
                nakshatras=nakshatras,
                traditional_regions=regions,
                transiting_malefics=tuple(malefics_in_sector),
                transiting_benefics=tuple(benefics_in_sector),
                is_afflicted=is_afflicted,
                severity=severity,
                risk_summary=risk_summary,
            ))

        summary = (
            f"Kurma Chakra evaluated at {dt.isoformat()}: "
            f"{len(highest_risk_dirs)} sector(s) on high alert ({', '.join([d.value.upper() for d in highest_risk_dirs]) or 'None'}). "
            "Classical Reference: Brihat Samhita, Ch. 14 (Kurma Vibhaga)."
        )

        return KurmaChakraState(
            evaluated_at=dt,
            sectors=tuple(sector_statuses),
            highest_risk_directions=tuple(highest_risk_dirs),
            summary=summary,
        )
