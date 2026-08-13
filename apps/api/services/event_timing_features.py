"""
AstroOS — Event Timing Feature Extraction

Turns an already-computed TimingSnapshot (birth chart + dasha chain + transit
read + varga availability) into a flat map of CALCULATED features that the
rule engine consumes (spec §11). It does NOT invent astrological rules — it
only normalises values the existing Core engines already produced:

  Dasha     → md_lord, ad_lord, pd_lord
  Transit   → saturn_house, jupiter_house, retrograde states, sade_sati
  Natal     → moon_rashi, venus_rashi, house lords, 7th-house occupants
  Varga     → varga.available
  (derived) → house numbers of Jupiter/Saturn from natal Venus — pure cyclic
              arithmetic over already-known rashis, matching the documented
              MarriageTimingEngine activation vocabulary (1/5/7/9, 1/3/7/10)

The output is a `FeatureMap` — a dict (keyed by dotted feature name) plus the
ordered `Tuple[TimingFeature, ...]` carried on a TimingPrediction for display.
The rule engine (event_timing_rules.evaluate_rule) reads `values`.
"""

from __future__ import annotations

from datetime import date

from apps.api.domain.dasha import DashaPeriod
from apps.api.domain.event_timing import TimingFeature
from apps.api.domain.horoscope import D1Chart
from packages.shared.enums import Rashi
from packages.shared.rashi_offset import house_offset

_RASHI_LIST = [r.value for r in Rashi]

# Houses whose lord we surface as natal features (spec §11 example uses 7th).
_HOUSE_LORD_FEATURES = {
    4: "natal.fourth_lord",
    5: "natal.fifth_lord",
    7: "natal.seventh_lord",
    10: "natal.tenth_lord",
    11: "natal.eleventh_lord",
}


class FeatureMap:
    """The extracted feature set: a dotted-path dict + ordered feature list."""

    __slots__ = ("values", "features")

    def __init__(self) -> None:
        self.values: dict = {}
        self.features: list[TimingFeature] = []

    def add(self, category: str, name: str, value) -> None:
        self.values[name] = value
        self.features.append(
            TimingFeature(feature_name=name, feature_value=value, feature_category=category)
        )


def _house_from_rashi(from_rashi: str, to_rashi: str) -> int:
    """House number (1–12) of `to_rashi` counted cyclically from `from_rashi`.
    Pure modular arithmetic over rashi indices — not astrology."""
    i = _RASHI_LIST.index(from_rashi)
    j = _RASHI_LIST.index(to_rashi)
    return house_offset(i, j)


def _rashi_by_house(chart: D1Chart) -> dict[int, str]:
    return {h.house_number: h.rashi for h in chart.houses if getattr(h, "rashi", None)}


def _planet_rashi(chart: D1Chart, planet: str) -> str | None:
    for p in chart.planets:
        if p.planet == planet:
            return p.rashi
    return None


def _planet_house(chart: D1Chart, planet: str) -> int | None:
    for p in chart.planets:
        if p.planet == planet:
            return p.house_number
    return None


def extract_features(
    natal_chart: D1Chart,
    dasha_chain: tuple[DashaPeriod, ...],
    transits,
    varga_available: bool = False,
    house_lord_lookup=None,
) -> FeatureMap:
    """Normalise a TimingSnapshot into features.

    Args:
        natal_chart: the natal D1Chart (HoroscopeEngine).
        dasha_chain: active chain (a `TimingDashaPeriod`-like tuple or
            `DashaPeriod` tuple — anything exposing .lord / .level).
        transits: an iterable of `TimingTransit`-like objects exposing
            .planet / .transit_rashi / .house_from_natal_moon / .is_retrograde
            / .is_sade_sati.
        varga_available: whether the selected technique's varga was computed.
        house_lord_lookup: callable rashi->lord, defaulting to the SIGN_LORDS
            map via HouseEngine.get_house_lord.
    """
    fm = FeatureMap()

    # ── Dasha ──
    if dasha_chain:
        fm.add("dasha", "dasha.mahadasha_lord", dasha_chain[0].lord)
        if len(dasha_chain) > 1:
            fm.add("dasha", "dasha.antardasha_lord", dasha_chain[1].lord)
            if len(dasha_chain) > 2:
                fm.add("dasha", "dasha.pratyantardasha_lord", dasha_chain[2].lord)

    # ── Natal (house lords + key rashis + 7th-house occupants) ──
    houses = _rashi_by_house(natal_chart)
    lookup = house_lord_lookup
    if lookup is None:
        from apps.api.services.house_engine import HouseEngine
        lookup = HouseEngine().get_house_lord
    for house_no, feature_name in _HOUSE_LORD_FEATURES.items():
        rashi = houses.get(house_no)
        if rashi:
            fm.add("natal", feature_name, lookup(rashi))

    moon_rashi = _planet_rashi(natal_chart, "moon")
    venus_rashi = _planet_rashi(natal_chart, "venus")
    if moon_rashi:
        fm.add("natal", "natal.moon_rashi", moon_rashi)
    if venus_rashi:
        fm.add("natal", "natal.venus_rashi", venus_rashi)

    seventh_house = houses.get(7)
    if seventh_house:
        occupants = sorted(p.planet for p in natal_chart.planets if p.house_number == 7)
        if occupants:
            fm.add("natal", "natal.seventh_house_planets", tuple(occupants))

    # ── Transit: capture each graha's read, then derive house-from-Venus ──
    saturn_house = jupiter_house = None
    saturn_transit_rashi = jupiter_transit_rashi = None
    saturn_retro = jupiter_retro = None
    is_sade_sati = False
    for t in transits:
        if t.planet == "saturn":
            saturn_house = t.house_from_natal_moon
            saturn_transit_rashi = t.transit_rashi
            saturn_retro = t.is_retrograde
            is_sade_sati = bool(getattr(t, "is_sade_sati", False))
        elif t.planet == "jupiter":
            jupiter_house = t.house_from_natal_moon
            jupiter_transit_rashi = t.transit_rashi
            jupiter_retro = t.is_retrograde

    if saturn_house is not None:
        fm.add("transit", "transit.saturn_house", saturn_house)
        fm.add("transit", "transit.saturn_retrograde", saturn_retro)
        if venus_rashi and saturn_transit_rashi:
            fm.add("transit", "transit.saturn_house_from_venus",
                   _house_from_rashi(venus_rashi, saturn_transit_rashi))
    if jupiter_house is not None:
        fm.add("transit", "transit.jupiter_house", jupiter_house)
        fm.add("transit", "transit.jupiter_retrograde", jupiter_retro)
        if venus_rashi and jupiter_transit_rashi:
            fm.add("transit", "transit.jupiter_house_from_venus",
                   _house_from_rashi(venus_rashi, jupiter_transit_rashi))
    fm.add("transit", "transit.is_sade_sati", is_sade_sati)

    # ── Varga ──
    fm.add("varga", "varga.available", bool(varga_available))

    return fm