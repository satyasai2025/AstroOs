"""
AstroOS — Drik Bala (SHADBALA-DRIK)

Aspectual strength — contribution from aspects RECEIVED from other
planets: benefic aspects add, malefic aspects subtract, graded by orb
closeness.

**Explicitly a simplified approximation, not a verified classical
formula.** BPHS's precise Drik Bala uses a "Virupa" aspect-strength
table with specific coefficients per aspect type that this
implementation has not verified against a primary source — the same
judgment call made for Nabhasa Yoga's Dala/Akriti/Sankhya sub-categories
and Kemadruma/Shakata's incomplete cancellation sets: better to be
honest about an approximation than assert unverified precision. This
uses `AspectEngine`'s existing orb data with a straightforward linear
falloff (full strength at 0° orb, zero at the aspect orb limit) and a
placeholder per-aspect maximum (15 Shashtiamsas — order-of-magnitude
reasonable for a quarter-Rupa single-aspect contribution, not verified
against BPHS's exact table). Revisit before relying on this for
research requiring classical-text-exact Drik Bala values.

Benefic/malefic classification reused directly from
`yoga_predicates.NATURAL_BENEFICS`/`NATURAL_MALEFICS` (Mercury/Moon
simplified as static, same caveat as there).
"""

from __future__ import annotations

from apps.api.domain.horoscope import AspectInfo
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.aspect_engine import ASPECT_ORB
from apps.api.services.yoga_predicates import is_natural_benefic, is_natural_malefic

_COMPONENT_ID = "SHADBALA-DRIK"
_COMPONENT_NAME = "Drik Bala"
_RULE_VERSION = "1.0"

_MAX_CONTRIBUTION_PER_ASPECT = 15.0  # Shashtiamsas — see module docstring caveat

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


class DrikBalaCalculator:
    """Stateless — needs only AspectEngine's already-computed aspect list."""

    def calculate(self, planet: str, aspects: list[AspectInfo]) -> BalaComponentResult:
        if planet not in _CLASSICAL_SEVEN:
            raise ValueError(
                f"Drik Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        received = [a for a in aspects if a.to_planet == planet]
        trace = [f"Step 1: aspects received by {planet} → {len(received)}"]

        total = 0.0
        for aspect in received:
            strength_fraction = max(0.0, (ASPECT_ORB - aspect.orb_degrees) / ASPECT_ORB)
            is_benefic = is_natural_benefic(aspect.from_planet)
            sign = 1.0 if is_benefic else -1.0
            contribution = _MAX_CONTRIBUTION_PER_ASPECT * strength_fraction * sign
            total += contribution
            trace.append(
                f"Step: {aspect.from_planet} ({'benefic' if is_benefic else 'malefic'}) "
                f"aspects {planet} at orb {aspect.orb_degrees:.2f}° → "
                f"contribution {contribution:+.4f} Shashtiamsas"
            )

        trace.append(f"Final: total Drik Bala = {total:.4f} Shashtiamsas")

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(total, 4), trace=tuple(trace),
        )

    def calculate_all(self, aspects: list[AspectInfo]) -> list[BalaComponentResult]:
        return [self.calculate(planet, aspects) for planet in _CLASSICAL_SEVEN]
