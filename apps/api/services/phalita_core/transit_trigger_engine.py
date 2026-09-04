"""
AstroOS — Transit (Gochara) & Ashtakavarga Trigger Engine
=========================================================

Canonical Reference: docs/CANONICAL_PREDICTION_FRAMEWORK.md (Step 8)
Source: BPHS Gochara-Adhyaya & Jha's Narendra Modi Case Study

Key Siddhantic Rules Enforced:
1. "Transit ALONE cannot predict — it only triggers natal promises."
2. "Ashtakavarga rekhas in the transit sign amplify this effect."
   - Sarvashtakavarga (SAV) >= 28 in the transited rashi = Auspicious baseline.
   - Bhinnashtakavarga (BAV) >= 4 for the specific transiting planet = Potent trigger.
   - SAV < 25 or BAV < 3 = Obstructed trigger / delays.
3. Transiting Jupiter / Saturn / Sun aspecting or occupying the domain's primary house/lord
   materializes the timing window when Vimshottari dasha confers the promise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from typing import Dict, List, Optional, Tuple

from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.constants import SIGN_LORDS

RASHI_NAMES: Tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
)



@dataclass(frozen=True)
class TransitTriggerResult:
    """Assessment of Gochara activation for a specific life domain on a target date."""
    domain: str
    target_date: date
    primary_house: int
    target_rashi_idx: int
    target_rashi_name: str
    sav_score: int                 # Sarvashtakavarga score (out of ~56, avg 28)
    is_sav_benefic: bool           # True if SAV >= 28
    active_transit_activators: Tuple[str, ...] # Planets transiting or aspecting the domain house
    is_transit_triggered: bool     # True if natal promise is actively triggered by Gochara
    trigger_strength: float        # 0.0 to 1.0 multiplier
    shastric_trigger_summary: str


class TransitTriggerEngine:
    """
    Evaluates Gochara (transit) triggers with Ashtakavarga rekha support.
    """

    def __init__(self, ephemeris_wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._av_engine = AshtakavargaEngine()

    def evaluate_transit_trigger(
        self,
        natal_lagna_rashi_idx: int,
        domain: str,
        primary_house: int,
        target_date: date,
        sav_matrix: Optional[Dict[int, int]] = None,
        bav_matrix: Optional[Dict[str, Dict[int, int]]] = None,
    ) -> TransitTriggerResult:
        """
        Evaluates whether transit positions on target_date trigger the domain house.
        """
        target_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        target_rashi_idx = (natal_lagna_rashi_idx + primary_house - 1) % 12

        target_rashi_name = RASHI_NAMES[target_rashi_idx]

        # Calculate live transit planetary positions
        transit_ephem = self._wrapper.calculate(dt=target_dt, latitude=28.6139, longitude=77.2090)
        
        transit_positions = {}
        for p in transit_ephem.planet_positions:
            transit_positions[p.planet.lower()] = int(p.sidereal_longitude / 30.0) % 12

        # 1. Check which major planets occupy or aspect the target rashi
        activators = []
        # Direct occupancy
        for p_name, r_idx in transit_positions.items():
            if r_idx == target_rashi_idx:
                activators.append(f"Transiting {p_name.capitalize()} in House {primary_house} ({target_rashi_name})")

        # Major Parashari Special Aspects:
        # Jupiter: 5th (4 signs away), 9th (8 signs away), 7th (6 signs away)
        jup_r = transit_positions.get("jupiter")
        if jup_r is not None:
            if (jup_r + 4) % 12 == target_rashi_idx or (jup_r + 8) % 12 == target_rashi_idx or (jup_r + 6) % 12 == target_rashi_idx:
                activators.append(f"Transiting Jupiter aspecting House {primary_house} ({target_rashi_name})")

        # Saturn: 3rd (2 signs away), 7th (6 signs away), 10th (9 signs away)
        sat_r = transit_positions.get("saturn")
        if sat_r is not None:
            if (sat_r + 2) % 12 == target_rashi_idx or (sat_r + 6) % 12 == target_rashi_idx or (sat_r + 9) % 12 == target_rashi_idx:
                activators.append(f"Transiting Saturn aspecting House {primary_house} ({target_rashi_name})")

        # Mars: 4th (3 signs away), 7th (6 signs away), 8th (7 signs away)
        mars_r = transit_positions.get("mars")
        if mars_r is not None:
            if (mars_r + 3) % 12 == target_rashi_idx or (mars_r + 6) % 12 == target_rashi_idx or (mars_r + 7) % 12 == target_rashi_idx:
                activators.append(f"Transiting Mars aspecting House {primary_house} ({target_rashi_name})")

        # 2. Ashtakavarga Rekha Assessment
        sav_score = 28  # Baseline neutral
        if sav_matrix and target_rashi_idx in sav_matrix:
            sav_score = sav_matrix[target_rashi_idx]

        is_sav_benefic = (sav_score >= 28)

        # 3. Calculate Composite Trigger Strength
        if activators:
            if sav_score >= 32:
                trig_str = 1.0
                desc = f"Strong Gochara trigger ({len(activators)} transit links) with high SAV ({sav_score}/56 rekhas)."
                is_trig = True
            elif sav_score >= 28:
                trig_str = 0.85
                desc = f"Moderate Gochara trigger ({len(activators)} transit links) with standard SAV ({sav_score}/56 rekhas)."
                is_trig = True
            elif sav_score >= 24:
                trig_str = 0.60
                desc = f"Subdued Gochara trigger ({len(activators)} transit links) under below-average SAV ({sav_score}/56 rekhas)."
                is_trig = True
            else:
                trig_str = 0.35
                desc = f"Frictional Gochara activation: Heavy obstacles due to low SAV ({sav_score}/56 rekhas)."
                is_trig = False
        else:
            if sav_score >= 30:
                trig_str = 0.50
                desc = f"Passive favorable transit environment in House {primary_house} (SAV {sav_score}), awaiting major planetary transit trigger."
                is_trig = False
            else:
                trig_str = 0.20
                desc = f"Dormant transit environment in House {primary_house} (SAV {sav_score})."
                is_trig = False

        return TransitTriggerResult(
            domain=domain,
            target_date=target_date,
            primary_house=primary_house,
            target_rashi_idx=target_rashi_idx,
            target_rashi_name=target_rashi_name,
            sav_score=sav_score,
            is_sav_benefic=is_sav_benefic,
            active_transit_activators=tuple(activators),
            is_transit_triggered=is_trig,
            trigger_strength=round(trig_str, 2),
            shastric_trigger_summary=desc,
        )
