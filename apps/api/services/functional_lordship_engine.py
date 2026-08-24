"""
AstroOS — Functional Lordship & Yogakaraka Engine

Classical Parashari Jyotish (BPHS Ch. 19 / Bhava Phala Adhyaya):
Computes functional benefic, malefic, neutral classification, and Yogakaraka
status for all classical grahas based on the native's Lagna (Ascendant).

Canonical Core Principles (BPHS Ch. 19):
1. Lagna Lord (1st house ruler) is always functionally auspicious/benefic.
2. Trikona Lords (5th and 9th houses) are always auspicious/benefic.
3. Trishadaya Lords (3rd, 6th, 11th houses) are functionally inauspicious/malefic.
4. Kendra Lords (4th, 7th, 10th houses):
   - Natural benefics owning kendras incur Kendradhipatya Dosha (loss of beneficence / functional malefic/neutral).
   - Natural malefics owning kendras lose maleficience (become neutral or auspicious).
5. 8th and 12th House Lords: Neutral on their own; their nature is conditioned by the lord's other sign / Moolatrikona placement.
6. 2nd and 7th House Lords: Maraka houses (death-inflicting / neutral-to-malefic).
7. Yogakaraka: A single planet owning simultaneously a Kendra (4, 7, 10) and a Trikona (1, 5, 9)
   becomes a Yogakaraka (highest auspiciousness):
   - Taurus (Vrishabha): Saturn (9L & 10L)
   - Cancer (Karka): Mars (5L & 10L)
   - Leo (Simha): Mars (4L & 9L)
   - Libra (Tula): Saturn (4L & 5L)
   - Capricorn (Makara): Venus (5L & 10L)
   - Aquarius (Kumbha): Venus (4L & 9L)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from apps.api.domain.horoscope import D1Chart

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# Canonical Parashari Functional Status Table (BPHS Chapter 19)
# Format per Lagna: {planet: (nature: "benefic" | "malefic" | "neutral", is_yogakaraka: bool)}
_FUNCTIONAL_MATRIX: dict[str, dict[str, tuple[str, bool]]] = {
    "aries": {
        "sun": ("benefic", False),       # 5L
        "moon": ("neutral", False),      # 4L
        "mars": ("benefic", False),      # 1L, 8L (Lagna lord overrides 8L)
        "mercury": ("malefic", False),   # 3L, 6L
        "jupiter": ("benefic", False),   # 9L, 12L (Moolatrikona in 9th)
        "venus": ("malefic", False),     # 2L, 7L (Maraka)
        "saturn": ("malefic", False),    # 10L, 11L (11L Trishadaya dominance)
    },
    "taurus": {
        "sun": ("neutral", False),       # 4L
        "moon": ("malefic", False),      # 3L
        "mars": ("malefic", False),      # 7L, 12L
        "mercury": ("benefic", False),   # 2L, 5L (Moolatrikona in 5th)
        "jupiter": ("malefic", False),   # 8L, 11L
        "venus": ("neutral", False),     # 1L, 6L
        "saturn": ("benefic", True),     # 9L, 10L (Yogakaraka)
    },
    "gemini": {
        "sun": ("malefic", False),       # 3L
        "moon": ("neutral", False),      # 2L
        "mars": ("malefic", False),      # 6L, 11L
        "mercury": ("benefic", False),   # 1L, 4L (Lagna lord)
        "jupiter": ("malefic", False),   # 7L, 10L (Kendradhipatya Dosha)
        "venus": ("benefic", False),     # 5L, 12L (Moolatrikona in 5th)
        "saturn": ("neutral", False),    # 8L, 9L
    },
    "cancer": {
        "sun": ("neutral", False),       # 2L
        "moon": ("benefic", False),      # 1L
        "mars": ("benefic", True),       # 5L, 10L (Yogakaraka)
        "mercury": ("malefic", False),   # 3L, 12L
        "jupiter": ("benefic", False),   # 6L, 9L (Moolatrikona in 9th)
        "venus": ("malefic", False),     # 4L, 11L
        "saturn": ("malefic", False),    # 7L, 8L
    },
    "leo": {
        "sun": ("benefic", False),       # 1L
        "moon": ("neutral", False),      # 12L
        "mars": ("benefic", True),       # 4L, 9L (Yogakaraka)
        "mercury": ("malefic", False),   # 2L, 11L
        "jupiter": ("benefic", False),   # 5L, 8L (Moolatrikona in 5th)
        "venus": ("malefic", False),     # 3L, 10L
        "saturn": ("malefic", False),    # 6L, 7L
    },
    "virgo": {
        "sun": ("neutral", False),       # 12L
        "moon": ("malefic", False),      # 11L
        "mars": ("malefic", False),      # 3L, 8L
        "mercury": ("benefic", False),   # 1L, 10L (Lagna lord)
        "jupiter": ("malefic", False),   # 4L, 7L (Kendradhipatya Dosha)
        "venus": ("benefic", False),     # 2L, 9L (Moolatrikona in 9th)
        "saturn": ("neutral", False),    # 5L, 6L
    },
    "libra": {
        "sun": ("malefic", False),       # 11L
        "moon": ("neutral", False),      # 10L
        "mars": ("malefic", False),      # 2L, 7L (Maraka)
        "mercury": ("benefic", False),   # 9L, 12L
        "jupiter": ("malefic", False),   # 3L, 6L
        "venus": ("benefic", False),     # 1L, 8L (Lagna lord)
        "saturn": ("benefic", True),     # 4L, 5L (Yogakaraka)
    },
    "scorpio": {
        "sun": ("benefic", False),       # 10L
        "moon": ("benefic", False),      # 9L
        "mars": ("benefic", False),      # 1L, 6L (Lagna lord)
        "mercury": ("malefic", False),   # 8L, 11L
        "jupiter": ("benefic", False),   # 2L, 5L (Moolatrikona in 5th)
        "venus": ("malefic", False),     # 7L, 12L
        "saturn": ("malefic", False),    # 3L, 4L
    },
    "sagittarius": {
        "sun": ("benefic", False),       # 9L
        "moon": ("neutral", False),      # 8L
        "mars": ("benefic", False),      # 5L, 12L (Moolatrikona in 5th)
        "mercury": ("malefic", False),   # 7L, 10L (Kendradhipatya Dosha)
        "jupiter": ("benefic", False),   # 1L, 4L (Lagna lord)
        "venus": ("malefic", False),     # 6L, 11L
        "saturn": ("malefic", False),    # 2L, 3L
    },
    "capricorn": {
        "sun": ("neutral", False),       # 8L
        "moon": ("malefic", False),      # 7L (Maraka)
        "mars": ("malefic", False),      # 4L, 11L
        "mercury": ("benefic", False),   # 6L, 9L (Moolatrikona in 9th)
        "jupiter": ("malefic", False),   # 3L, 12L
        "venus": ("benefic", True),      # 5L, 10L (Yogakaraka)
        "saturn": ("benefic", False),    # 1L, 2L (Lagna lord)
    },
    "aquarius": {
        "sun": ("malefic", False),       # 7L (Maraka)
        "moon": ("malefic", False),      # 6L
        "mars": ("malefic", False),      # 3L, 10L
        "mercury": ("benefic", False),   # 5L, 8L
        "jupiter": ("malefic", False),   # 2L, 11L
        "venus": ("benefic", True),      # 4L, 9L (Yogakaraka)
        "saturn": ("benefic", False),    # 1L, 12L (Lagna lord)
    },
    "pisces": {
        "sun": ("malefic", False),       # 6L
        "moon": ("benefic", False),      # 5L
        "mars": ("benefic", False),      # 2L, 9L (Moolatrikona in 9th)
        "mercury": ("malefic", False),   # 4L, 7L (Kendradhipatya Dosha)
        "jupiter": ("benefic", False),   # 1L, 10L (Lagna lord)
        "venus": ("malefic", False),     # 3L, 8L
        "saturn": ("malefic", False),    # 11L, 12L
    },
}


@dataclass(frozen=True)
class FunctionalPlanetResult:
    planet: str
    lordship: str       # "benefic", "malefic", "neutral"
    is_yogakaraka: bool


@dataclass(frozen=True)
class FunctionalLordshipResult:
    ascendant_rashi: str
    planets: dict[str, FunctionalPlanetResult]


class FunctionalLordshipEngine:
    """
    Stateless engine computing classical functional benefic/malefic lordship
    and Yogakaraka status for a chart's Ascendant.
    """

    def compute_by_lagna(self, ascendant_rashi: str) -> FunctionalLordshipResult:
        rashi = ascendant_rashi.lower()
        mapping = _FUNCTIONAL_MATRIX.get(rashi)
        if mapping is None:
            raise ValueError(f"Unknown ascendant rashi: {ascendant_rashi!r}")

        results: dict[str, FunctionalPlanetResult] = {}
        for planet, (lordship, is_yk) in mapping.items():
            results[planet] = FunctionalPlanetResult(
                planet=planet,
                lordship=lordship,
                is_yogakaraka=is_yk,
            )

        return FunctionalLordshipResult(
            ascendant_rashi=rashi,
            planets=results,
        )

    def compute(self, chart: D1Chart) -> FunctionalLordshipResult:
        return self.compute_by_lagna(chart.ascendant.rashi)
