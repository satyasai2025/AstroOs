"""
AstroOS — Chesta Bala (SHADBALA-CHESTA)

Motional strength — for the 5 non-luminary grahas (Mars, Mercury,
Jupiter, Venus, Saturn; Sun and Moon use different classical treatment
and are not scored here). Classically: retrograde/near-stationary motion
is treated as maximum strength ("struggling against natural motion");
unusually fast direct motion is treated as weaker.

**Explicitly a simplified approximation, not verified classical
fidelity — same honesty-over-precision judgment call as Drik Bala.**
True classical Chesta Bala is derived from the "Chesta Kendra" (Sighra
anomaly), which needs heliocentric longitude data this codebase does not
compute — a gap not caught by the original Module 9 Phase 0 audit, found
while implementing this component. Rather than fabricate a
Sighra-Kendra-shaped formula without that data, this uses
`SiderealPosition.speed_deg_per_day` (available since Phase 0) directly:
retrograde or near-stationary motion scores near maximum; speed at or
above each planet's approximate mean geocentric daily motion scores
near zero; linear in between. The per-planet mean-speed reference values
are commonly-cited approximate figures, not derived from this
implementation's own orbital mechanics — treat this component as a
reasonable stand-in, not a classical-text-exact value, until the
Sighra-Kendra approach is implemented.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult

_COMPONENT_ID = "SHADBALA-CHESTA"
_COMPONENT_NAME = "Chesta Bala"
_RULE_VERSION = "1.0"

# Approximate mean geocentric daily motion, degrees/day (magnitude).
# Commonly-cited reference figures, not classically-derived Sighra
# constants — see module docstring caveat.
_APPROX_MEAN_SPEED: dict[str, float] = {
    "mars": 0.524,
    "mercury": 1.383,
    "jupiter": 0.083,
    "venus": 1.2,
    "saturn": 0.034,
}

_STATIONARY_THRESHOLD = 0.01  # deg/day — below this, treated as stationary (max bala)


class ChestaBalaCalculator:
    """
    Stateless — needs only a planet's speed_deg_per_day and retrograde
    flag (both available on SiderealPosition since Module 9 Phase 0).
    """

    def calculate(self, position: SiderealPosition) -> BalaComponentResult:
        planet = position.planet
        if planet not in _APPROX_MEAN_SPEED:
            raise ValueError(
                f"Chesta Bala applies only to Mars/Mercury/Jupiter/Venus/Saturn "
                f"(Sun/Moon use different classical treatment; Rahu/Ketu are excluded), got {planet!r}"
            )

        speed = position.speed_deg_per_day
        abs_speed = abs(speed)
        mean_speed = _APPROX_MEAN_SPEED[planet]
        trace = [
            f"Step 1: {planet} speed = {speed:.4f} deg/day (retrograde={position.is_retrograde})",
            f"Step 2: approximate mean speed reference for {planet} = {mean_speed:.4f} deg/day",
        ]

        if position.is_retrograde or abs_speed < _STATIONARY_THRESHOLD:
            value = 60.0
            trace.append("Step 3: retrograde or near-stationary → maximum Chesta Bala (60)")
        else:
            ratio = min(1.0, abs_speed / mean_speed)
            value = 60.0 * (1.0 - ratio)
            trace.append(
                f"Step 3: direct motion, ratio = |speed|/mean = {ratio:.4f} → "
                f"value = 60 * (1 - {ratio:.4f}) = {value:.4f}"
            )

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(value, 4), trace=tuple(trace),
        )

    def calculate_all(self, planets: list[SiderealPosition]) -> list[BalaComponentResult]:
        planets_by_name = {p.planet: p for p in planets}
        return [
            self.calculate(planets_by_name[planet])
            for planet in _APPROX_MEAN_SPEED
            if planet in planets_by_name
        ]
