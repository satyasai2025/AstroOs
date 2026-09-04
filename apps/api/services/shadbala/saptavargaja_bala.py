"""
AstroOS — Saptavargaja Bala (SHADBALA-SAPTAVARGAJA)

Sthana Bala's cross-varga sub-component — the one this entire Sthana
Bala prerequisite pass (dignity extended to divisional charts, see
GrahaEngine.compute_dignity() and packages/shared/dignity.py) was
specifically for. Sums a planet's dignity across all 7 classical
Saptavargaja vargas (D1, D2, D3, D7, D9, D12, D30), converting each
varga's dignity into points and adding them together.

**Explicitly an approximated point scale, not verified classical
fidelity — same honesty-over-precision judgment call as Drik Bala and
Chesta Bala.** Classical sources grade dignity into finer tiers than
this codebase currently computes (some distinguish "great friend" from
"friend" and "great enemy" from "enemy" — a 8-9 tier scale). This
codebase's dignity computation (GrahaEngine.compute_dignity /
packages/shared/dignity.py) produces 7 discrete levels (exalted /
moolatrikona / own / friendly / neutral / enemy / debilitated), and the
point values below are a commonly-cited approximate halving scale, not
independently derived or verified against a single primary source.
Revisit if/when the finer great-friend/great-enemy distinction is added
to the dignity computation itself.

Architecturally different from every other Shadbala component so far:
this is the first one that needs to COMPUTE additional charts (the 6
non-D1 vargas), not just read from an already-built D1Chart. It takes
a DivisionalEngine and the raw birth parameters, not just a chart.
"""

from __future__ import annotations

from datetime import datetime

from apps.api.domain.shadbala import BalaComponentResult
from apps.api.domain.horoscope import D1Chart
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.graha_engine import GrahaEngine

_COMPONENT_ID = "SHADBALA-SAPTAVARGAJA"
_COMPONENT_NAME = "Saptavargaja Bala"
_RULE_VERSION = "1.0"

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# The 7 classical Saptavargaja vargas. D1 is handled from the
# already-computed chart; the other 6 are computed on demand.
_NON_D1_VARGAS = ["D2", "D3", "D7", "D9", "D12", "D30"]

# Cross-verified against PyJHora's jhora.horoscope.chart.strength.
# _sapthavargaja_bala_1()/_2(): moolatrikona=45, own=30, and a 5-tier
# friend/enemy scale (great-friend 22.5 / friend 15 / neutral 7.5 /
# enemy 3.75 / great-enemy 1.875) — there is NO separate "exalted" tier
# in Saptavargaja Bala specifically (unlike Uchcha Bala, which scores
# exact exaltation degree separately); an exalted planet is simply
# scored at its moolatrikona/own-sign level here. The previous
# "exalted": 60.0 entry was an unverified guess that didn't match this
# reference and has been removed — exalted now falls through to the
# moolatrikona tier below via `dignity if dignity != "exalted" else
# "moolatrikona"` in calculate().
#
# The great-friend/great-enemy split (22.5 / 1.875) is NOT applied here
# — this codebase's dignity computation (GrahaEngine.compute_dignity)
# only produces a flat friendly/enemy (no Panchadha Maitri compound-
# relationship tiering), so "friendly"/"enemy" below use the plain
# friend/enemy points. Extending to the full 5-tier scale needs that
# compound-relationship capability added to GrahaEngine first — a
# separate, larger scope item, not a coefficient tweak.
_DIGNITY_POINTS: dict[str, float] = {
    "moolatrikona": 45.0,
    "own": 30.0,
    "friendly": 15.0,
    "neutral": 7.5,
    "enemy": 3.75,
    "debilitated": 1.875,
}


def _dignity_points(dignity_value: str | None) -> float:
    """"exalted" has no dedicated Saptavargaja tier — scored at moolatrikona's level."""
    if dignity_value is None:
        return 0.0
    key = "moolatrikona" if dignity_value == "exalted" else dignity_value
    return _DIGNITY_POINTS.get(key, 0.0)


class SaptavargajaBalaCalculator:
    """
    Needs a DivisionalEngine (to compute the 6 non-D1 vargas) and a
    GrahaEngine (to score dignity per varga) — unlike every other
    Shadbala calculator, this one triggers new ephemeris computation
    rather than only reading an already-built D1Chart.
    """

    def __init__(
        self,
        divisional_engine: DivisionalEngine,
        graha_engine: GrahaEngine | None = None,
    ) -> None:
        self._divisional_engine = divisional_engine
        self._graha_engine = graha_engine or GrahaEngine()

    def calculate(
        self,
        planet: str,
        d1_chart: D1Chart,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> BalaComponentResult:
        if planet not in _CLASSICAL_SEVEN:
            raise ValueError(
                f"Saptavargaja Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        trace: list[str] = []
        total = 0.0

        d1_position = next((p for p in d1_chart.planets if p.planet == planet), None)
        if d1_position is None:
            trace.append("D1: planet not found in chart — skipped")
        else:
            d1_dignity = self._graha_engine.compute_dignity(
                planet, d1_position.rashi, d1_position.rashi_degree
            )
            points = _dignity_points(d1_dignity.value if d1_dignity else None)
            total += points
            trace.append(f"D1: dignity={d1_dignity.value if d1_dignity else 'none'} → {points} points")

        for varga in _NON_D1_VARGAS:
            varga_chart = self._divisional_engine.compute(
                birth_datetime_utc=birth_datetime_utc, latitude=latitude,
                longitude=longitude, varga=varga, ayanamsa=ayanamsa,
                house_system=house_system,
            )
            varga_position = next(
                (p for p in varga_chart.planet_positions if p.planet == planet), None
            )
            if varga_position is None:
                trace.append(f"{varga}: planet not found in chart — skipped")
                continue

            varga_dignity = self._graha_engine.compute_dignity(
                planet, varga_position.varga_rashi, varga_position.varga_rashi_degree
            )
            points = _dignity_points(varga_dignity.value if varga_dignity else None)
            total += points
            trace.append(
                f"{varga}: dignity={varga_dignity.value if varga_dignity else 'none'} → {points} points"
            )

        trace.append(f"Final: sum across 7 vargas = {total:.4f} Shashtiamsas")

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(total, 4), trace=tuple(trace),
        )

    def calculate_all(
        self,
        d1_chart: D1Chart,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> list[BalaComponentResult]:
        return [
            self.calculate(
                planet, d1_chart, birth_datetime_utc=birth_datetime_utc,
                latitude=latitude, longitude=longitude, ayanamsa=ayanamsa,
                house_system=house_system,
            )
            for planet in _CLASSICAL_SEVEN
        ]
