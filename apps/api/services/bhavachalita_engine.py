"""
AstroOS — Vishamabhava Bhaavachalita Engine
============================================
Implements the canonical classical Unequal House Division (Vishamabhava)
described in BPHS (Ch. 29) and SSS (Surya Siddhanta) principles:

  1. Independent computation of Madhya-Lagna (10th house middle) and
     Lagna-Madhya (1st house middle) using spherical ecliptic geometry.
  2. Tri-section of quadrants (Kendra arc division) producing true
     latitude-dependent unequal house spans.
  3. Bhava-Sandhi computation (midpoint boundaries between adjacent house middles).
  4. Multi-Sign house analysis ("राशि-द्वय-गते भावे तद्-राशि-अधिपतेः क्रिया" - BPHS Ch.29):
     - Primary Lord = Ruler of the Rasi containing Bhava-Madhya (majority sign).
     - Secondary Lord = Ruler of the minority Rasi within the house span.
  5. Bhāva-heena planet detection: planets whose Rasis contain zero Bhava-Madhyas
     due to house contraction, acting as functional malefics during dasha.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.constants import SIGN_LORDS

RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def normalize_degrees(deg: float) -> float:
    """Normalize angle into [0, 360) range."""
    return deg % 360.0




@dataclass(frozen=True)
class BhavaSpan:
    """Represents a single Vishamabhava house with unequal boundaries."""
    house_number: int            # 1 to 12
    start_sandhi: float          # Start boundary in degrees [0, 360)
    madhya: float                # Bhava-Madhya (house middle) in degrees [0, 360)
    end_sandhi: float            # End boundary in degrees [0, 360)
    total_span_deg: float        # Total span in degrees (e.g. 25.4° or 34.2°)
    primary_rashi: str           # Rasi containing the Bhava-Madhya
    primary_lord: str            # Lord of majority sign
    secondary_rashi: Optional[str] = None  # Intersecting minority Rasi (if multi-sign)
    secondary_lord: Optional[str] = None   # Lord of minority sign (if multi-sign)
    multi_sign: bool = False


@dataclass(frozen=True)
class VishamabhavaChart:
    """Complete Vishamabhava Bhaavachalita Chart."""
    lagna_madhya: float
    madhya_lagna: float          # 10th house cusp (MC)
    houses: Tuple[BhavaSpan, ...]
    bhavaheena_planets: Tuple[str, ...]    # Lords with zero Bhava-Madhya ownership
    bhavaheena_rashis: Tuple[str, ...]     # Signs containing zero Bhava-Madhyas
    planet_bhava_placements: Dict[str, int] = field(default_factory=dict)  # Planet -> House (1-12)


def _arc_distance(from_deg: float, to_deg: float) -> float:
    """Returns forward angular distance from -> to in [0, 360) degrees."""
    return (to_deg - from_deg) % 360.0


def _midpoint_deg(deg1: float, deg2: float) -> float:
    """Computes the exact forward midpoint between two longitudes."""
    arc = _arc_distance(deg1, deg2)
    return normalize_degrees(deg1 + arc / 2.0)


def _deg_to_rashi_name(deg: float) -> str:
    """Maps sidereal longitude to canonical rashi name."""
    rashi_idx = int(normalize_degrees(deg) / 30.0) % 12
    return RASHI_LIST[rashi_idx]



class VishamabhavaEngine:
    """Canonical Vishamabhava (Unequal Bhaavachalita) computation engine."""

    def __init__(
        self,
        ephemeris_wrapper: Optional[EphemerisWrapper] = None,
        ephemeris_path: str = "data/ephemeris",
    ):
        self.wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)


    def compute_bhavachalita(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
    ) -> VishamabhavaChart:
        """
        Computes the 12 Vishamabhava houses and detects multi-sign & bhāva-heena conditions.
        """
        result = self.wrapper.calculate(
            dt=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system="W",
        )

        lagna_deg = result.ascendant.sidereal_longitude

        
        # MC (Madhya-Lagna / 10th house cusp)
        # In Indian spherical astronomy, MC is calculated directly via swiss ephemeris houses_ex
        # We fetch the exact MC from swiss ephemeris
        import swisseph as swe
        jd_ut = swe.julday(
            birth_datetime.year, birth_datetime.month, birth_datetime.day,
            birth_datetime.hour + birth_datetime.minute / 60.0 + birth_datetime.second / 3600.0
        )
        ayan_val = swe.get_ayanamsa_ut(jd_ut) if ayanamsa.lower() == "lahiri" else 0.0
        # P = Placidus computes exact MC (cusp 10 is identical in all quadrant systems)
        cusps, ascmc = swe.houses(jd_ut, latitude, longitude, b'P')
        mc_deg = normalize_degrees(ascmc[1] - ayan_val)


        # ── 1. Calculate the 12 Bhava-Madhyas (House Middles) ─────────────────
        # H1 = Lagna, H10 = MC, H7 = Lagna + 180, H4 = MC + 180
        h1_mid = lagna_deg
        h10_mid = mc_deg
        h7_mid = normalize_degrees(h1_mid + 180.0)
        h4_mid = normalize_degrees(h10_mid + 180.0)

        # Quadrant 4 (H10 -> H1): Arc length / 3
        arc_10_to_1 = _arc_distance(h10_mid, h1_mid)
        step_10_to_1 = arc_10_to_1 / 3.0
        h11_mid = normalize_degrees(h10_mid + step_10_to_1)
        h12_mid = normalize_degrees(h10_mid + 2.0 * step_10_to_1)

        # Quadrant 1 (H1 -> H4): Arc length / 3
        arc_1_to_4 = _arc_distance(h1_mid, h4_mid)
        step_1_to_4 = arc_1_to_4 / 3.0
        h2_mid = normalize_degrees(h1_mid + step_1_to_4)
        h3_mid = normalize_degrees(h1_mid + 2.0 * step_1_to_4)

        # Quadrant 2 (H4 -> H7) and Quadrant 3 (H7 -> H10) are exact 180° opposites
        h5_mid = normalize_degrees(h11_mid + 180.0)
        h6_mid = normalize_degrees(h12_mid + 180.0)
        h8_mid = normalize_degrees(h2_mid + 180.0)
        h9_mid = normalize_degrees(h3_mid + 180.0)

        madhyas = [
            h1_mid, h2_mid, h3_mid, h4_mid, h5_mid, h6_mid,
            h7_mid, h8_mid, h9_mid, h10_mid, h11_mid, h12_mid,
        ]

        # ── 2. Calculate Bhava-Sandhis (Boundaries) ───────────────────────────
        sandhis = []
        for i in range(12):
            prev_idx = (i - 1) % 12
            sandhi_start = _midpoint_deg(madhyas[prev_idx], madhyas[i])
            sandhis.append(sandhi_start)

        # ── 3. Construct BhavaSpans & Multi-Sign Detection ─────────────────────
        spans: List[BhavaSpan] = []
        rashi_madhya_counts: Dict[str, int] = {r.lower(): 0 for r in RASHI_LIST}

        for i in range(12):
            h_num = i + 1
            start_s = sandhis[i]
            end_s = sandhis[(i + 1) % 12]
            madhya = madhyas[i]
            total_span = _arc_distance(start_s, end_s)

            pri_rashi = _deg_to_rashi_name(madhya).lower()
            pri_lord = SIGN_LORDS.get(pri_rashi, "mars")
            rashi_madhya_counts[pri_rashi] += 1

            start_rashi = _deg_to_rashi_name(start_s).lower()
            end_rashi = _deg_to_rashi_name(end_s).lower()

            multi = False
            sec_rashi = None
            sec_lord = None

            # If start boundary or end boundary is in a different rashi from the madhya
            if start_rashi != pri_rashi:
                multi = True
                sec_rashi = start_rashi
                sec_lord = SIGN_LORDS.get(sec_rashi, "mars")
            elif end_rashi != pri_rashi:
                multi = True
                sec_rashi = end_rashi
                sec_lord = SIGN_LORDS.get(sec_rashi, "mars")

            spans.append(
                BhavaSpan(
                    house_number=h_num,
                    start_sandhi=round(start_s, 4),
                    madhya=round(madhya, 4),
                    end_sandhi=round(end_s, 4),
                    total_span_deg=round(total_span, 4),
                    primary_rashi=pri_rashi,
                    primary_lord=pri_lord.capitalize(),
                    secondary_rashi=sec_rashi,
                    secondary_lord=sec_lord.capitalize() if sec_lord else None,
                    multi_sign=multi,
                )
            )

        # ── 4. Detect Bhāva-heena Rashis & Planets ────────────────────────────
        bhavaheena_rashis = tuple(r for r, count in rashi_madhya_counts.items() if count == 0)
        bhavaheena_planets_set = set()
        for r in bhavaheena_rashis:
            lord = SIGN_LORDS.get(r)
            # A planet is truly bhavaheena if ALL signs it owns have zero bhava-madhyas
            owned_rashis = [k for k, v in SIGN_LORDS.items() if v == lord]
            if all(rashi_madhya_counts.get(k, 0) == 0 for k in owned_rashis):
                if lord:
                    bhavaheena_planets_set.add(lord.capitalize())

        # ── 5. Map Planets into Vishamabhava Houses ───────────────────────────
        placements: Dict[str, int] = {}
        for p in result.planet_positions:
            p_lon = p.sidereal_longitude
            # Find which house span contains p_lon
            assigned_h = 1
            for span in spans:
                # Point is in span if arc(start -> p_lon) < span.total_span_deg
                if _arc_distance(span.start_sandhi, p_lon) <= span.total_span_deg:
                    assigned_h = span.house_number
                    break
            placements[p.planet.capitalize()] = assigned_h


        return VishamabhavaChart(
            lagna_madhya=round(lagna_deg, 4),
            madhya_lagna=round(mc_deg, 4),
            houses=tuple(spans),
            bhavaheena_planets=tuple(sorted(bhavaheena_planets_set)),
            bhavaheena_rashis=bhavaheena_rashis,
            planet_bhava_placements=placements,
        )

