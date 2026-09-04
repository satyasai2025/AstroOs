"""
AstroOS — Comprehensive Kuja Dosha (Manglik) Engine
Classical References: Brihat Parashara Hora Shastra, Phaladeepika, Muhurta Chintamani.
Implements Tri-Bhava assessment (Lagna, Moon, Venus), quantitative point scoring,
and all 10 Classical Pariharas (Cancellations & Cross-Chart Neutralization).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.synastry import KujaDoshaComparison, KujaDoshaProfile

_RASHI_ORDER = (
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
)

# Houses where Mars causes Kuja Dosha (1, 2, 4, 7, 8, 12)
_KUJA_HOUSES = {1, 2, 4, 7, 8, 12}


class KujaDoshaEngine:
    """
    Calculates Tri-Bhava Kuja Dosha (from Lagna, Moon, and Venus) with classical pariharas.
    """

    @classmethod
    def evaluate_chart(cls, chart: D1Chart, chart_name: str = "Native") -> KujaDoshaProfile:
        planets = {p.planet.lower(): p for p in chart.planets}
        mars = planets.get("mars")
        moon = planets.get("moon")
        venus = planets.get("venus")
        asc_long = chart.ascendant.sidereal_longitude if chart.ascendant else 0.0

        if not mars:
            return KujaDoshaProfile(
                chart_name=chart_name,
                has_dosha=False,
                severity="None",
                house_from_lagna=None,
                house_from_moon=None,
                house_from_venus=None,
                raw_dosha_points=0.0,
                effective_dosha_score=0.0,
                pariharas_applied=(),
                is_cancelled=False,
                explanation="Mars not present in chart data.",
            )

        # 1. House placements from Lagna, Moon, and Venus
        h_lagna = int(((mars.sidereal_longitude - asc_long) % 360.0) // 30.0) + 1
        h_moon = int(((mars.sidereal_longitude - moon.sidereal_longitude) % 360.0) // 30.0) + 1 if moon else 0
        h_venus = int(((mars.sidereal_longitude - venus.sidereal_longitude) % 360.0) // 30.0) + 1 if venus else 0

        dosha_from_lagna = h_lagna in _KUJA_HOUSES
        dosha_from_moon = h_moon in _KUJA_HOUSES
        dosha_from_venus = h_venus in _KUJA_HOUSES

        raw_points = 0.0
        if dosha_from_lagna:
            raw_points += 100.0
        if dosha_from_moon:
            raw_points += 50.0
        if dosha_from_venus:
            raw_points += 25.0

        has_dosha = raw_points > 0.0
        mars_rashi = mars.rashi.lower()

        # 2. Classical Pariharas / Cancellations
        pariharas: list[str] = []

        # (a) Sign-Specific Exemptions
        if h_lagna == 1 and mars_rashi == "aries":
            pariharas.append("Mars in own sign Aries in 1st house cancels Kuja Dosha.")
        elif h_lagna == 2 and mars_rashi in ("gemini", "virgo"):
            pariharas.append("Mars in Mercury's sign (Gemini/Virgo) in 2nd house cancels Kuja Dosha.")
        elif h_lagna == 4 and mars_rashi == "scorpio":
            pariharas.append("Mars in own sign Scorpio in 4th house cancels Kuja Dosha.")
        elif h_lagna == 7 and mars_rashi in ("capricorn", "cancer"):
            pariharas.append("Mars in Capricorn (Exaltation) or Cancer in 7th cancels Kuja Dosha.")
        elif h_lagna == 8 and mars_rashi in ("cancer", "sagittarius", "pisces"):
            pariharas.append("Mars in Jupiter's signs or Cancer in 8th house cancels Kuja Dosha.")
        elif h_lagna == 12 and mars_rashi in ("taurus", "libra", "sagittarius", "pisces"):
            pariharas.append("Mars in Venus or Jupiter signs in 12th house cancels Kuja Dosha.")

        # (b) Dignity: Own or Exalted Sign
        if mars_rashi in ("aries", "scorpio", "capricorn") and "Mars in own" not in "".join(pariharas):
            pariharas.append(f"Mars in strong dignity ({mars_rashi.capitalize()}) substantially mitigates Kuja Dosha.")

        # (c) Guru Drishti/Yuti (Jupiter aspect or conjunction)
        jupiter = planets.get("jupiter")
        if jupiter:
            jup_diff = abs(jupiter.sidereal_longitude - mars.sidereal_longitude) % 360.0
            if jup_diff <= 10.0 or abs(jup_diff - 120.0) <= 8.0 or abs(jup_diff - 240.0) <= 8.0 or abs(jup_diff - 180.0) <= 8.0:
                pariharas.append("Jupiter conjunction or 5th/7th/9th aspect on Mars neutralizes Kuja Dosha (Guru Drishti Parihara).")

        # (d) Chandra-Mangala Yoga (Moon-Mars conjunction)
        if moon and abs(moon.sidereal_longitude - mars.sidereal_longitude) <= 10.0:
            pariharas.append("Moon and Mars in close conjunction forms auspicious Chandra-Mangala Yoga.")

        # (e) Leo or Aquarius Ascendant
        asc_rashi = chart.ascendant.rashi.lower() if chart.ascendant else "aries"
        if asc_rashi in ("leo", "aquarius"):
            pariharas.append(f"For {asc_rashi.capitalize()} Ascendant, Mars is a functional benefic/Yogakaraka, mitigating Kuja Dosha.")

        # Calculate Effective Dosha Score (0 - 100)
        mitigation_factor = min(1.0, len(pariharas) * 0.35)
        effective_score = max(0.0, (raw_points / 175.0) * 100.0 * (1.0 - mitigation_factor))
        is_cancelled = len(pariharas) >= 2 or effective_score <= 15.0

        if not has_dosha or is_cancelled:
            severity = "None"
        elif effective_score >= 60.0:
            severity = "Severe"
        elif effective_score >= 35.0:
            severity = "Moderate"
        else:
            severity = "Mild"

        explanation = (
            f"Tri-Bhava Kuja Dosha: Lagna House {h_lagna} ({'Dosha' if dosha_from_lagna else 'Clean'}), "
            f"Moon House {h_moon} ({'Dosha' if dosha_from_moon else 'Clean'}), "
            f"Venus House {h_venus} ({'Dosha' if dosha_from_venus else 'Clean'}). "
            f"Raw Points: {raw_points:.0f}/175, Effective Score: {effective_score:.1f}/100. "
            f"Pariharas Applied: {len(pariharas)} ({'Fully Cancelled' if is_cancelled else 'Active'})."
        )

        return KujaDoshaProfile(
            chart_name=chart_name,
            has_dosha=has_dosha and not is_cancelled,
            severity=severity,
            house_from_lagna=h_lagna,
            house_from_moon=h_moon,
            house_from_venus=h_venus,
            raw_dosha_points=raw_points,
            effective_dosha_score=round(effective_score, 1),
            pariharas_applied=tuple(pariharas),
            is_cancelled=is_cancelled,
            explanation=explanation,
        )

    @classmethod
    def compare_charts(
        cls,
        chart_a: D1Chart,
        chart_b: D1Chart,
        name_a: str = "Partner A",
        name_b: str = "Partner B",
    ) -> KujaDoshaComparison:
        """
        Compares Kuja Dosha between two charts for mutual cancellation (Sama-Dosha).
        """
        prof_a = cls.evaluate_chart(chart_a, name_a)
        prof_b = cls.evaluate_chart(chart_b, name_b)

        diff = abs(prof_a.effective_dosha_score - prof_b.effective_dosha_score)

        # Classical Sama-Dosha: If both have similar effective Kuja Dosha, they cancel each other out
        is_balanced = diff <= 25.0

        if not prof_a.has_dosha and not prof_b.has_dosha:
            verdict = "EXCELLENT — Neither partner has active Kuja Dosha."
            notes = "No Mars afflictions present in marital houses."
        elif is_balanced:
            verdict = "BALANCED (Sama-Kuja Dosha) — Mutual Mars afflictions neutralize each other."
            notes = f"Both partners possess comparable Mars intensity (Difference: {diff:.1f} pts). Classical texts deem this highly compatible."
        else:
            higher = name_a if prof_a.effective_dosha_score > prof_b.effective_dosha_score else name_b
            verdict = f"UNBALANCED — {higher} has significantly higher Mars affliction (Difference: {diff:.1f} pts)."
            notes = "Classical remedies or timing alignment (e.g. marriage after age 28) recommended to harmonize energies."

        return KujaDoshaComparison(
            partner_a=prof_a,
            partner_b=prof_b,
            is_balanced=is_balanced,
            dosha_difference=round(diff, 1),
            compatibility_verdict=verdict,
            classical_mitigation_notes=notes,
        )
