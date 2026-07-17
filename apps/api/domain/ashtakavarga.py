"""
AstroOS — Ashtakavarga Domain Objects (Module 10)

Structurally distinct from both Yoga (boolean presence) and Shadbala
(continuous Shashtiamsa scores) — Ashtakavarga is a discrete bindu
(point) count per RASHI, built from 8 independent contributors.

Deliberately indexed by absolute rashi (1=Aries..12=Pisces), NOT by
"house number" from a specific house system (Placidus, Equal, etc.).
Classical Ashtakavarga bindu rules count signs cyclically from each
contributor's own sign — a rashi-counting rule, entirely independent of
which house system a chart uses for its cusps. Conflating "house" with
"rashi" here would silently make results depend on the house system
selected for the chart, which is not how classical Ashtakavarga works.
`bindus_from_lagna()` below is the explicit, opt-in conversion for
callers who want a lagna-relative "house" reading.
"""

from __future__ import annotations

from dataclasses import dataclass

_RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


@dataclass(frozen=True)
class BhinnashtakavargaResult:
    """
    One target graha's individual Ashtakavarga — a 12-rashi bindu table
    (0-8 bindus per rashi) built by summing all 8 contributors' marks.
    """
    target_planet: str
    bindus_by_rashi: tuple[int, ...]  # 12 values, index 0 = Aries, ..., index 11 = Pisces
    total_bindus: int
    rule_version: str = "1.0"

    def bindus_in_rashi(self, rashi: str) -> int:
        return self.bindus_by_rashi[_RASHI_LIST.index(rashi)]

    def bindus_from_lagna(self, lagna_rashi: str, house_number: int) -> int:
        """
        Convenience: bindus in the rashi that is `house_number` houses
        from the lagna's rashi (whole-sign convention — house N is
        simply the Nth rashi counted from the lagna's rashi). This is
        the conventional way Bhinnashtakavarga is *read* against a
        specific chart, but the underlying table itself is rashi-based,
        not house-system-based — see module docstring.
        """
        lagna_index = _RASHI_LIST.index(lagna_rashi)
        target_index = (lagna_index + house_number - 1) % 12
        return self.bindus_by_rashi[target_index]


@dataclass(frozen=True)
class SarvashtakavargaResult:
    """
    The combined Ashtakavarga — sum of all 7 planetary Bhinnashtakavargas
    (Lagna's own Bhinnashtakavarga is excluded from this sum, per
    classical convention). Classically checksums to 337 across the 12
    rashis on any correctly computed chart.
    """
    bindus_by_rashi: tuple[int, ...]  # 12 values
    total_bindus: int
    rule_version: str = "1.0"

    def bindus_in_rashi(self, rashi: str) -> int:
        return self.bindus_by_rashi[_RASHI_LIST.index(rashi)]

    def bindus_from_lagna(self, lagna_rashi: str, house_number: int) -> int:
        lagna_index = _RASHI_LIST.index(lagna_rashi)
        target_index = (lagna_index + house_number - 1) % 12
        return self.bindus_by_rashi[target_index]
