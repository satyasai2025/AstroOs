"""
AstroOS — Sodhya Pinda Engine

Computes Rasi Pinda, Graha Pinda, and Sodhya Pinda for each of the 7
classical grahas from the Shodhita (reduced) Ashtakavarga — i.e. the
Bhinnashtakavarga AFTER both classical Shodhana passes (Trikona then
Ekadhipatya), which is exactly what AshtakavargaEngine.
compute_reduced_bhinnashtakavarga() already produces.

Formula and the two multiplier tables (Rasimana, Grahamana) cross-verified
against PyJHora's jhora.horoscope.chart.ashtakavarga.sodhaya_pindas() —
same algorithm, independently implemented against our own domain types.
Reference run for 1995-01-01 12:00 UTC, New Delhi (Lahiri) matched exactly:
Sun Rasi/Graha/Sodhya = 232/68/300, Mars = 229/85/314, etc.
"""

from __future__ import annotations

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult
from apps.api.domain.horoscope import D1Chart
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine

# Index 0 = Aries ... 11 = Pisces.
RASIMANA_MULTIPLIERS = [7, 10, 8, 4, 10, 6, 7, 8, 9, 5, 11, 12]

# Ordered Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn — paired
# with the rashi each of those 7 contributors occupies in the D1 chart.
_CONTRIBUTOR_ORDER = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
GRAHAMANA_MULTIPLIERS = [5, 5, 8, 5, 10, 7, 5]

_RASHI_TO_INDEX = {
    "aries": 0, "taurus": 1, "gemini": 2, "cancer": 3, "leo": 4, "virgo": 5,
    "libra": 6, "scorpio": 7, "sagittarius": 8, "capricorn": 9, "aquarius": 10, "pisces": 11,
}


class PindaResult:
    __slots__ = ("planet", "rasi_pinda", "graha_pinda", "sodhya_pinda")

    def __init__(self, planet: str, rasi_pinda: int, graha_pinda: int, sodhya_pinda: int) -> None:
        self.planet = planet
        self.rasi_pinda = rasi_pinda
        self.graha_pinda = graha_pinda
        self.sodhya_pinda = sodhya_pinda


class PindaEngine:
    """Stateless — needs only an already-built D1Chart."""

    def __init__(self, ashtakavarga_engine: AshtakavargaEngine | None = None) -> None:
        self._ashtakavarga_engine = ashtakavarga_engine or AshtakavargaEngine()

    def compute(
        self,
        chart: D1Chart,
        reduced_bhinna: list[BhinnashtakavargaResult] | None = None,
    ) -> list[PindaResult]:
        if reduced_bhinna is None:
            reduced_bhinna = self._ashtakavarga_engine.compute_reduced_bhinnashtakavarga(chart)
        bhinna_by_planet = {r.target_planet: r for r in reduced_bhinna}

        contributor_house_idx = [
            _RASHI_TO_INDEX[p.rashi]
            for name in _CONTRIBUTOR_ORDER
            for p in chart.planets
            if p.planet == name
        ]

        results = []
        for target in _CONTRIBUTOR_ORDER:
            bindus = bhinna_by_planet[target].bindus_by_rashi
            rasi_pinda = sum(b * m for b, m in zip(bindus, RASIMANA_MULTIPLIERS))
            graha_pinda = sum(
                GRAHAMANA_MULTIPLIERS[i] * bindus[house_idx]
                for i, house_idx in enumerate(contributor_house_idx)
            )
            results.append(PindaResult(
                planet=target,
                rasi_pinda=rasi_pinda,
                graha_pinda=graha_pinda,
                sodhya_pinda=rasi_pinda + graha_pinda,
            ))
        return results
