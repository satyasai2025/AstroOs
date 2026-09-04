"""
AstroOS — Chesta Bala (SHADBALA-CHESTA)

REPLACES an earlier from-scratch approximation that compared a planet's
raw instantaneous speed against an assumed "mean speed" constant and
clamped to 0 whenever direct motion exceeded it. That was confirmed
wrong: classically, FASTER-than-mean direct motion (Chara) scores
HIGHER than average motion (Sama = 7.5), not lower — the old formula's
core assumption was backwards, which is why Mercury/Jupiter/Saturn were
all incorrectly showing exactly 0.

Classical formula (Chesta Kendra method — confirmed via BPHS-derived
summaries and cross-checked structurally against PyJHora's
jhora.horoscope.chart.strength._cheshta_bala_new()):

    Chesta Kendra = shorter-arc angular distance between a planet's
                    TRUE longitude and its "Seeghrocha" (fastest-motion
                    reference point):
      - Superior planets (Mars, Jupiter, Saturn): Seeghrocha = Sun's
        mean longitude (their retrograde motion is driven by Earth's
        orbit, classically modeled via the Sun's mean position).
      - Inferior planets (Mercury, Venus): Seeghrocha = the planet's
        OWN mean longitude (they have their own epicyclic anomaly);
        the Sun's mean longitude takes the "mean longitude" reference
        role instead.
    ave_long = midpoint of true longitude and the mean-longitude
               reference (per the same Seeghrocha/Manda pairing above).
    Chesta Bala = Chesta Kendra(seeghrocha, ave_long) / 3   (0-60 Shashtiamsas)

Sun and Moon are not scored (same classical exclusion as before — they
don't have a Seeghrocha in this sense).

**Known caveat**: mean longitudes here come from standard MODERN
secular mean-orbital-element formulas (Meeus/VSOP87 low-precision
terms), not the ancient Kali-Yuga epoch table PyJHora's own
implementation uses — cross-checking against PyJHora's `_cheshta_
bala_new()` for the reference chart showed the same order of magnitude
and no more false-zero results, but not a byte-exact match (a few
Shashtiamsas' difference per planet), because ancient vs modern mean-
motion calibrations diverge slightly by design. PyJHora's own module
docstring flags its ancient-table Mars result as unreliable ("TODO:
Mars not matching close to Drik"), so an exact match to that specific
implementation was not the goal — getting the FORMULA STRUCTURE right
(Chesta Kendra, not raw speed-vs-constant) was.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult
from packages.shared.degrees import shorter_arc_distance as _shorter_arc_distance

_COMPONENT_ID = "SHADBALA-CHESTA"
_COMPONENT_NAME = "Chesta Bala"
_RULE_VERSION = "1.0"

_SUPERIOR_PLANETS = {"mars", "jupiter", "saturn"}
_INFERIOR_PLANETS = {"mercury", "venus"}
_SCOPED_PLANETS = _SUPERIOR_PLANETS | _INFERIOR_PLANETS

# Standard low-precision secular mean-longitude elements (Meeus,
# "Astronomical Algorithms"): L = L0 + n*T, degrees, T = Julian
# centuries since J2000.0 (JD 2451545.0). Earth's own mean longitude +
# 180° gives the Sun's (geocentric) mean longitude.
_MEAN_LONGITUDE_L0_N: dict[str, tuple[float, float]] = {
    "earth":   (100.466457, 35999.3728565),
    "mercury": (252.250906, 149472.6746358),
    "venus":   (181.979801, 58517.8156760),
    "mars":    (355.433000, 19140.2993039),
    "jupiter": (34.351484, 3034.9056746),
    "saturn":  (50.077471, 1222.1137943),
}


def _tropical_mean_longitude(jd: float, planet: str) -> float:
    l0, n = _MEAN_LONGITUDE_L0_N[planet]
    t = (jd - 2451545.0) / 36525.0
    return (l0 + n * t) % 360.0


def _sidereal_mean_longitude(jd: float, ayanamsa_deg: float, planet: str) -> float:
    return (_tropical_mean_longitude(jd, planet) - ayanamsa_deg) % 360.0


class ChestaBalaCalculator:
    """Stateless — needs a planet's true sidereal longitude, the birth JD, and the ayanamsa (for mean-longitude reconstruction)."""

    def calculate(self, position: SiderealPosition, jd: float, ayanamsa_deg: float) -> BalaComponentResult:
        planet = position.planet
        if planet not in _SCOPED_PLANETS:
            raise ValueError(
                f"Chesta Bala applies only to Mars/Mercury/Jupiter/Venus/Saturn "
                f"(Sun/Moon use different classical treatment; Rahu/Ketu are excluded), got {planet!r}"
            )

        sun_mean = _sidereal_mean_longitude(jd, ayanamsa_deg, "earth")
        sun_mean = (sun_mean + 180.0) % 360.0  # Earth's heliocentric mean long -> Sun's geocentric mean long
        own_mean = _sidereal_mean_longitude(jd, ayanamsa_deg, planet)

        if planet in _SUPERIOR_PLANETS:
            seeghrocha = sun_mean
            mean_ref = own_mean
            trace_rule = f"{planet} (superior): Seeghrocha = Sun's mean longitude ({sun_mean:.4f}°)"
        else:
            seeghrocha = own_mean
            mean_ref = sun_mean
            trace_rule = f"{planet} (inferior): Seeghrocha = own mean longitude ({own_mean:.4f}°)"

        true_long = position.sidereal_longitude
        ave_long = ((true_long + mean_ref) / 2.0) if abs(true_long - mean_ref) < 180.0 else \
            (((true_long + mean_ref) / 2.0 + 180.0) % 360.0)
        kendra = _shorter_arc_distance(seeghrocha, ave_long)
        value = kendra / 3.0

        trace = (
            f"Step 1: {trace_rule}",
            f"Step 2: true longitude = {true_long:.4f}°, mean-longitude reference = {mean_ref:.4f}°",
            f"Step 3: average longitude = {ave_long:.4f}°",
            f"Step 4: Chesta Kendra = shorter-arc({seeghrocha:.4f}°, {ave_long:.4f}°) = {kendra:.4f}°",
            f"Step 5: value = {kendra:.4f} / 3 = {value:.4f} Shashtiamsas",
        )

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(value, 4), trace=trace,
        )

    def calculate_all(self, planets: list[SiderealPosition], jd: float, ayanamsa_deg: float) -> list[BalaComponentResult]:
        by_name = {p.planet: p for p in planets}
        return [
            self.calculate(by_name[planet], jd, ayanamsa_deg)
            for planet in ["mars", "mercury", "jupiter", "venus", "saturn"]
            if planet in by_name
        ]
