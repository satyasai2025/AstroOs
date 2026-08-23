"""
AstroOS — Ayana Bala (SHADBALA-AYANA)

Kala Bala's declination-based sub-component. REPLACES an earlier
from-scratch implementation that scaled real astronomical declination
linearly against Earth's obliquity, grouped by a north/south-favoring
planet split — never independently verified, and confirmed wrong when
cross-checked against PyJHora's jhora.panchanga.drik.declination_of_
planets() / jhora.horoscope.chart.strength._ayana_bala() for 1995-01-01
12:00 UTC, New Delhi.

The classical method here is NOT real equatorial declination — it's
"Kranti" computed via inverse-Lagrange interpolation of the planet's
"bhuja" (longitude reduced to 0-90° by quadrant-folding) against a
fixed 7-point declination table (bd/bx below), i.e. simulating the
Sun's own declination curve for any planet's zodiacal position — a
known classical approximation technique (BPHS-style Kranti Sadhanam),
not a shortcut this port introduces.

  1. Tropical longitude = sidereal longitude + ayanamsa.
  2. North/south favoring: Sun/Mars/Jupiter/Venus score higher in the
     northern tropical half (0-180°), Moon/Saturn score higher in the
     southern half (180-360°) — Mercury is a fixed special case,
     always north-favoring regardless of position.
  3. Bhuja = tropical longitude folded into 0-90° (quadrant symmetry).
  4. Kranti (declination proxy) = inverse_lagrange interpolation of
     bhuja against the fixed table below.
  5. Ayana Bala = (24 + signed Kranti) * 1.25, DOUBLED for the Sun only
     (a genuine classical special dispensation for Ravi's Ayana Bala,
     not a bug — Sun's value can exceed the usual 60-Shashtiamsa cap).

Byte-for-byte cross-verified against PyJHora for the reference chart —
see varsha_masa_bala.py's docstring for the same verification pattern.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult

_COMPONENT_ID = "SHADBALA-AYANA"
_COMPONENT_NAME = "Ayana Bala"
_RULE_VERSION = "1.0"

_NORTH_FAVORING = {"sun", "mars", "jupiter", "venus"}
_SOUTH_FAVORING = {"moon", "saturn"}
# mercury: always north-favoring regardless of position (classical special case)

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# Kranti interpolation table: known declination (degrees) at bhuja
# angles 0/15/30/45/60/75/90. bd values are arcminutes/60 -> degrees.
_KRANTI_DECLINATIONS = [0.0, 362 / 60.0, 703 / 60.0, 1002 / 60.0, 1238 / 60.0, 1388 / 60.0, 1440 / 60.0]
_KRANTI_BHUJA_ANGLES = [0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0]


def _inverse_lagrange(x: list[float], y: list[float], ya: float) -> float:
    """Given (x[i], y[i]) pairs, find xa such that f(xa) = ya."""
    total = 0.0
    for i in range(len(x)):
        numer = 1.0
        denom = 1.0
        for j in range(len(x)):
            if j != i:
                numer *= (ya - y[j])
                denom *= (y[i] - y[j])
        total += numer * x[i] / denom
    return total


def _bhuja(tropical_long: float) -> float:
    tl = tropical_long % 360.0
    if 90.0 < tl < 180.0:
        return round(180.0 - tl, 2)
    elif 180.0 < tl < 270.0:
        return round(tl - 180.0, 2)
    elif 270.0 < tl < 360.0:
        return round(360.0 - tl, 2)
    return round(tl, 2)


class AyanaBalaCalculator:
    """Stateless — needs a planet's sidereal longitude plus the birth moment's ayanamsa (to recover tropical longitude)."""

    def calculate(self, position: SiderealPosition, ayanamsa_deg: float) -> BalaComponentResult:
        planet = position.planet
        if planet not in _CLASSICAL_SEVEN:
            raise ValueError(
                f"Ayana Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        tropical_long = position.sidereal_longitude + ayanamsa_deg
        tl_mod = tropical_long % 360.0
        is_north_half = 0.0 <= tl_mod < 180.0

        if planet == "mercury":
            sign = 1
            trace_rule = "mercury: fixed north-favoring special case"
        elif is_north_half:
            sign = 1 if planet in _NORTH_FAVORING else -1
            trace_rule = f"{planet} in northern tropical half -> {'favored' if sign > 0 else 'not favored'}"
        else:
            sign = 1 if planet in _SOUTH_FAVORING else -1
            trace_rule = f"{planet} in southern tropical half -> {'favored' if sign > 0 else 'not favored'}"

        bhuja = _bhuja(tropical_long)
        kranti = sign * _inverse_lagrange(_KRANTI_DECLINATIONS, _KRANTI_BHUJA_ANGLES, bhuja)

        value = (24.0 + kranti) * 1.25
        if planet == "sun":
            value *= 2.0  # classical special dispensation — may exceed 60

        trace = (
            f"Step 1: tropical longitude = {position.sidereal_longitude:.4f} + {ayanamsa_deg:.4f} = {tropical_long:.4f}°",
            f"Step 2: {trace_rule}",
            f"Step 3: bhuja (quadrant-folded 0-90°) = {bhuja:.2f}°",
            f"Step 4: Kranti (signed) = {kranti:.4f}°",
            f"Step 5: value = (24 + {kranti:.4f}) * 1.25{' * 2 (Sun)' if planet == 'sun' else ''} = {value:.4f} Shashtiamsas",
        )

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(value, 4), trace=trace,
        )

    def calculate_all(self, planets: list[SiderealPosition], ayanamsa_deg: float) -> list[BalaComponentResult]:
        return [self.calculate(p, ayanamsa_deg) for p in planets if p.planet in _CLASSICAL_SEVEN]
