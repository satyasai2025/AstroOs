"""
AstroOS — Drik Bala (SHADBALA-DRIK)

Aspectual strength — REPLACES an earlier simplified orb-based linear
falloff model with the classical Parashari graded-aspect-strength
("Sputa Drishti") table, cross-verified against PyJHora's
jhora.horoscope.chart.strength.__drik_bala_calc_1()/_drik_bala().

For each pair of grahas, the angular separation (aspecting -> aspected,
0-360°) is graded through a piecewise table (not a simple orb falloff):
30° bands of increasing/decreasing strength, with EXTRA bonus virupas
when the aspecting planet is Mars (60-90° and 210-240°), Jupiter
(90-120° and 240-270°), or Saturn (60-90° and 270-300°) — the classical
"special aspects" (Mars' 4th/8th, Jupiter's 5th/9th, Saturn's 3rd/10th
drishti carry extra strength beyond the ordinary 7th-house aspect).

Final Drik Bala for a planet = (sum of virupas from all NATURAL BENEFIC
aspecting grahas) minus (sum from all NATURAL MALEFIC aspecting grahas),
divided by 4 — not the simple "each aspect contributes independently"
model used previously.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.yoga_predicates import is_natural_benefic, is_natural_malefic

_COMPONENT_ID = "SHADBALA-DRIK"
_COMPONENT_NAME = "Drik Bala"
_RULE_VERSION = "1.0"

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


def _piecewise_drishti_virupas(angle: float, aspecting_planet: str) -> float:
    """Angle is aspecting -> aspected, 0-360°. Ported from PyJHora's __drik_bala_calc_1()."""
    if 0.0 <= angle < 30.0:
        value = 0.0
    elif 30.0 <= angle < 60.0:
        value = 0.5 * (angle - 30.0)
    elif 60.0 <= angle < 90.0:
        value = (angle - 60.0) + 15.0
        if aspecting_planet == "saturn":
            value += 45.0
    elif 90.0 <= angle < 120.0:
        value = 0.5 * (120.0 - angle) + 30.0
        if aspecting_planet == "mars":
            value += 15.0
    elif 120.0 <= angle < 150.0:
        value = 150.0 - angle
        if aspecting_planet == "jupiter":
            value += 30.0
    elif 150.0 <= angle < 180.0:
        value = 2.0 * (angle - 150.0)
    elif 180.0 <= angle < 300.0:
        value = 0.5 * (300.0 - angle)
        if aspecting_planet == "mars" and 210.0 <= angle < 240.0:
            value += 15.0
        if aspecting_planet == "jupiter" and 240.0 <= angle < 270.0:
            value += 30.0
        if aspecting_planet == "saturn" and 270.0 <= angle < 300.0:
            value += 45.0
    else:
        value = 0.0
    return value


class DrikBalaCalculator:
    """Stateless — needs only the 7 classical grahas' sidereal longitudes."""

    def calculate_all(self, planets: list[SiderealPosition]) -> list[BalaComponentResult]:
        by_name = {p.planet: p for p in planets if p.planet in _CLASSICAL_SEVEN}
        results = []
        for aspected in _CLASSICAL_SEVEN:
            if aspected not in by_name:
                continue
            aspected_long = by_name[aspected].sidereal_longitude
            benefic_total = 0.0
            malefic_total = 0.0
            trace: list[str] = []
            for aspecting in _CLASSICAL_SEVEN:
                if aspecting not in by_name:
                    continue
                aspecting_long = by_name[aspecting].sidereal_longitude
                angle = (360.0 + aspected_long - aspecting_long) % 360.0
                virupas = _piecewise_drishti_virupas(angle, aspecting)
                if is_natural_benefic(aspecting):
                    benefic_total += virupas
                elif is_natural_malefic(aspecting):
                    malefic_total += virupas
                if virupas != 0.0:
                    trace.append(
                        f"{aspecting} at {angle:.2f}° from {aspected} -> {virupas:.2f} virupas "
                        f"({'benefic' if is_natural_benefic(aspecting) else 'malefic' if is_natural_malefic(aspecting) else 'neutral'})"
                    )

            total = (benefic_total - malefic_total) / 4.0
            trace.append(
                f"Final: (benefic {benefic_total:.2f} - malefic {malefic_total:.2f}) / 4 = {total:.4f} Shashtiamsas"
            )

            results.append(BalaComponentResult(
                component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
                rule_version=_RULE_VERSION, planet=aspected,
                value_shashtiamsas=round(total, 4), trace=tuple(trace),
            ))
        return results
