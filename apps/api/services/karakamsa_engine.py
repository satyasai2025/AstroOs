"""
AstroOS — Karakamsa Engine (Layer 6: Calculation Engine)

Stateless service computing Karakamsa and Swamsa from an already-built
D1Chart + D9 (Navamsa) VargaChart. No ephemeris/DB dependency — reuses
CharaKarakaEngine for the Atmakaraka rather than recomputing rankings.

Definitions:
  - Karakamsa: the Navamsa (D9) sign occupied by the Atmakaraka (the
    highest-ranked Chara Karaka — see jaimini_engine.py). The central
    object of Jaimini's Karakamsa analysis: where the soul's significator
    sits when the birth chart is viewed through the D9 lens.
  - Swamsa: the Navamsa sign occupied by the D1 Lagna itself — i.e. the
    D9 chart's own Ascendant sign (its "Navamsa Lagna"). Karakamsa and
    Swamsa are always analyzed as a pair (self via soul-significator vs.
    self via body/identity).
  - Relative houses: the Karakamsa "re-cast" as a Lagna — houses 1-12
    counted zodiacally from the Karakamsa sign, with each house's D9
    planetary occupants attached. This is the standard "Karakamsa chart"
    used to read D9 placements relative to the soul significator rather
    than the D1 ascendant.

"Atmakaraka Navamsa sign" (as distinct wording) is Karakamsa itself, by
definition — KarakamsaResult.karakamsa_rashi IS that value; there is no
second computation for it.
"""

from __future__ import annotations

from apps.api.domain.divisional import VargaChart, VargaPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import CharaKarakaScheme, KarakamsaHouseEntry, KarakamsaResult
from apps.api.services.jaimini_engine import CharaKarakaEngine
from apps.api.services.jaimini_shared import signs_from


class KarakamsaEngine:
    """Stateless Karakamsa/Swamsa calculator — operates on an
    already-computed D1Chart and D9 VargaChart, no ephemeris dependency."""

    def __init__(self, chara_karaka_engine: CharaKarakaEngine | None = None) -> None:
        self._chara_karaka_engine = chara_karaka_engine or CharaKarakaEngine()

    def compute(
        self,
        d1_chart: D1Chart,
        d9_chart: VargaChart,
        scheme: CharaKarakaScheme = "sapta_karaka",
    ) -> KarakamsaResult:
        if d9_chart.varga != "D9":
            raise ValueError(f"KarakamsaEngine requires a D9 chart, got {d9_chart.varga!r}.")

        karaka_result = self._chara_karaka_engine.compute(d1_chart, scheme=scheme)
        atmakaraka_karaka = karaka_result.atmakaraka
        atmakaraka = atmakaraka_karaka.planet

        d9_positions: dict[str, VargaPosition] = {p.planet: p for p in d9_chart.planet_positions}
        if atmakaraka not in d9_positions:
            raise ValueError(f"D9 chart is missing position data for Atmakaraka {atmakaraka!r}.")

        karakamsa_rashi = d9_positions[atmakaraka].varga_rashi
        swamsa_rashi = d9_chart.ascendant.varga_rashi

        relative_houses = tuple(
            self._house_entry(karakamsa_rashi, house_number, d9_positions)
            for house_number in range(1, 13)
        )

        return KarakamsaResult(
            scheme=scheme,
            atmakaraka=atmakaraka,
            karakamsa_rashi=karakamsa_rashi,
            swamsa_rashi=swamsa_rashi,
            d1_atmakaraka_rashi=atmakaraka_karaka.rashi,
            d1_lagna_rashi=d1_chart.ascendant.rashi,
            relative_houses=relative_houses,
        )

    @staticmethod
    def _house_entry(
        karakamsa_rashi: str, house_number: int, d9_positions: dict[str, VargaPosition]
    ) -> KarakamsaHouseEntry:
        rashi = signs_from(karakamsa_rashi, house_number - 1)
        planets = tuple(p.planet for p in d9_positions.values() if p.varga_rashi == rashi)
        return KarakamsaHouseEntry(house_number=house_number, rashi=rashi, planets=planets)
