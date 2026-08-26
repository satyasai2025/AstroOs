"""
AstroOS — Vaiseshikamsa Engine

Computes multi-varga dignity accumulation and assigns classical Parashari
Vaiseshikamsa honorific titles (BPHS Ch. 44).

Classical Schemes:
- Shadvarga (6 vargas): D1, D2, D3, D9, D12, D30
- Saptavarga (7 vargas): D1, D2, D3, D7, D9, D12, D30
- Dasavarga (10 vargas): D1, D2, D3, D7, D9, D10, D12, D16, D30, D60
- Shodasavarga (16 vargas): D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60

Vaiseshikamsa Titles (BPHS Ch. 44):
- 2 Vargas: Parijatamsa
- 3 Vargas: Uttamamsa
- 4 Vargas: Gopuramsa
- 5 Vargas: Simhasanamsa
- 6 Vargas: Paravatamsa
- 7 Vargas: Devalokamsa
- 8 Vargas: Kumkumamsa / Iravatamsa
- 9 Vargas: Brahmalokamsa / Vaiseshikamsa
- 10 Vargas: Airavatamsa
- 11 Vargas: Vaikunthamsa
- 12 Vargas: Golokamsa
- 13 Vargas: Sarvabhaumamsa
- 14 Vargas: Kalanidhamsa
- 15 Vargas: Sridhamamsa
- 16 Vargas: Bhedakamsa / Sridhama
"""

from __future__ import annotations

from typing import Mapping

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.vaiseshikamsa import (
    PlanetVaiseshikamsaResult,
    VaiseshikamsaChartResult,
    VaiseshikamsaScheme,
    VargaDignityPlacement,
)
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.dignity import compute_dignity_value

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

_SCHEME_VARGAS: dict[VaiseshikamsaScheme, tuple[str, ...]] = {
    "shadvarga": ("D1", "D2", "D3", "D9", "D12", "D30"),
    "saptavarga": ("D1", "D2", "D3", "D7", "D9", "D12", "D30"),
    "dasavarga": ("D1", "D2", "D3", "D7", "D9", "D10", "D12", "D16", "D30", "D60"),
    "shodasavarga": (
        "D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12",
        "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
    ),
}

_TITLES: dict[int, tuple[str, str]] = {
    2: ("Parijata", "Auspicious beginnings, good standing, and commendable character"),
    3: ("Uttama", "High intellect, wealth, virtues, and respect among scholars"),
    4: ("Gopura", "Landed property, leadership, wealth, vehicles, and honor"),
    5: ("Simhasana", "Regal status, high executive authority, royal/state patronage"),
    6: ("Paravata", "Great luxury, illustrious renown, elephants, horses, and renown"),
    7: ("Devaloka", "Divine grace, saintly wisdom, spiritual and worldly eminence"),
    8: ("Iravata", "Universal acclaim, sovereign prosperity, and extraordinary fortune"),
    9: ("Brahmaloka", "Supreme wisdom, spiritual realization, and universal veneration"),
    10: ("Airavata", "Paramount ruler status, commanding monarchs, supreme fame"),
    11: ("Vaikuntha", "Transcendental spiritual perfection and supreme piety"),
    12: ("Goloka", "Highest celestial abode, supreme righteousness, and eternal fame"),
    13: ("Sarvabhauma", "Universal emperor, unmatched sovereign authority"),
    14: ("Kalanidhi", "Treasury of all arts, sciences, and worldly accomplishments"),
    15: ("Sridhama", "Abode of Lakshmi, limitless wealth, virtue, and glory"),
    16: ("Bhedaka", "Supreme Parashari pinnacle across all 16 divisional realms"),
}

_AUSPICIOUS_DIGNITIES = {"exalted", "moolatrikona", "own", "friendly"}
_SWAVARGA_DIGNITIES = {"exalted", "moolatrikona", "own"}


class VaiseshikamsaEngine:
    """Computes multi-varga dignity accumulations and Vaiseshikamsa designations."""

    def calculate_planet(
        self,
        planet: str,
        chart: D1Chart,
        scheme: VaiseshikamsaScheme = "dasavarga",
    ) -> PlanetVaiseshikamsaResult:
        planet_name = planet.lower()
        vargas = _SCHEME_VARGAS[scheme]

        # Find natal planet position
        pos = next((p for p in chart.planets if p.planet.lower() == planet_name), None)
        if pos is None:
            raise ValueError(f"Planet {planet!r} not found in chart")

        from apps.api.services.divisional_engine import compute_varga_sign

        placements: list[VargaDignityPlacement] = []
        auspicious_count = 0
        swavarga_count = 0

        for varga in vargas:
            if varga == "D1":
                varga_rashi = pos.rashi.lower()
                varga_deg = pos.rashi_degree
            else:
                varga_rashi, varga_deg = compute_varga_sign(varga, pos.sidereal_longitude)
                varga_rashi = varga_rashi.lower()

            dignity_val = compute_dignity_value(planet_name, varga_rashi, varga_deg)
            dignity_str = dignity_val.value if hasattr(dignity_val, "value") else str(dignity_val).lower()


            is_ausp = dignity_str in _AUSPICIOUS_DIGNITIES
            if is_ausp:
                auspicious_count += 1
            if dignity_str in _SWAVARGA_DIGNITIES:
                swavarga_count += 1

            placements.append(
                VargaDignityPlacement(
                    varga=varga,
                    rashi=varga_rashi,
                    dignity=dignity_str,
                    is_auspicious=is_ausp,
                )
            )

        title, desc = _TITLES.get(
            auspicious_count,
            ("Samanya", "Standard planetary placement without Vaiseshikamsa title"),
        )

        return PlanetVaiseshikamsaResult(
            planet=planet_name,
            scheme=scheme,
            total_vargas_evaluated=len(vargas),
            auspicious_varga_count=auspicious_count,
            swavarga_count=swavarga_count,
            title=title,
            description=desc,
            placements=tuple(placements),
        )

    def calculate_all(
        self,
        chart: D1Chart,
        scheme: VaiseshikamsaScheme = "dasavarga",
    ) -> VaiseshikamsaChartResult:
        results = tuple(
            self.calculate_planet(p, chart, scheme=scheme)
            for p in _CLASSICAL_SEVEN
        )
        return VaiseshikamsaChartResult(planets=results)

