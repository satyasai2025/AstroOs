"""
AstroOS — Ashtakavarga Engine (Module 10)

Orchestrates Bhinnashtakavarga for all 7 classical grahas, sums them
into Sarvashtakavarga, and applies the classical Shodhana (reduction)
passes on request.

Not wired into any router or persistence layer — same scope discipline
as every engine before it (HouseEngine, YogaEngine, ShadbalaEngine).
"""

from __future__ import annotations

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult, SarvashtakavargaResult
from apps.api.domain.horoscope import D1Chart
from apps.api.services.ashtakavarga.bhinnashtakavarga_calculator import BhinnashtakavargaCalculator
from apps.api.services.ashtakavarga.shodhana_calculator import ShodhanaCalculator
from packages.shared.ashtakavarga_bindu_table import CONTRIBUTORS, EXPECTED_GRAND_TOTAL, TARGET_PLANETS

_RULE_VERSION = "1.0"

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


class AshtakavargaEngine:
    """Stateless — needs only an already-built D1Chart."""

    def __init__(
        self,
        calculator: BhinnashtakavargaCalculator | None = None,
        shodhana_calculator: ShodhanaCalculator | None = None,
    ) -> None:
        self._calculator = calculator or BhinnashtakavargaCalculator()
        self._shodhana = shodhana_calculator or ShodhanaCalculator()

    def _contributor_rashis(self, chart: D1Chart) -> dict[str, str]:
        rashis = {p.planet: p.rashi for p in chart.planets if p.planet in CONTRIBUTORS}
        rashis["lagna"] = chart.ascendant.rashi
        return rashis

    def _occupied_rashis(self, chart: D1Chart) -> set[str]:
        """
        Rashis occupied by any of the 7 classical grahas — used by
        Ekadhipatya Shodhana's occupied-house protection. Scoped to the
        7 classical grahas, consistent with the rest of this codebase's
        Ashtakavarga scope; Rahu/Ketu occupancy is not tracked.
        """
        return {p.rashi for p in chart.planets if p.planet in _CLASSICAL_SEVEN}

    def compute_bhinnashtakavarga(self, chart: D1Chart) -> list[BhinnashtakavargaResult]:
        """All 7 planets' individual Ashtakavarga tables (unreduced)."""
        contributor_rashis = self._contributor_rashis(chart)
        return self._calculator.calculate_all(contributor_rashis)

    def compute_sarvashtakavarga(self, chart: D1Chart) -> SarvashtakavargaResult:
        """
        Sum of all 7 planetary Bhinnashtakavargas (Lagna's own is
        excluded from the sum, per classical convention). Always
        unreduced — Shodhana applies only to Bhinnashtakavarga, per the
        source (see shodhana_calculator.py).
        """
        bhinna_results = self.compute_bhinnashtakavarga(chart)
        bindus_by_rashi = [0] * 12
        for result in bhinna_results:
            for i, count in enumerate(result.bindus_by_rashi):
                bindus_by_rashi[i] += count

        return SarvashtakavargaResult(
            bindus_by_rashi=tuple(bindus_by_rashi),
            total_bindus=sum(bindus_by_rashi),
            rule_version=_RULE_VERSION,
        )

    def compute_reduced_bhinnashtakavarga(
        self, chart: D1Chart
    ) -> list[BhinnashtakavargaResult]:
        """
        All 7 planets' Bhinnashtakavarga after both classical Shodhana
        (reduction) passes — Trikona Shodhana then Ekadhipatya Shodhana,
        applied sequentially per the source. See shodhana_calculator.py.
        """
        occupied = self._occupied_rashis(chart)
        return [
            self._shodhana.apply_both(bhinna, occupied)
            for bhinna in self.compute_bhinnashtakavarga(chart)
        ]

    def verify_checksum(self, chart: D1Chart) -> bool:
        """
        Classical validation: Sarvashtakavarga must always total exactly
        337 bindus across the 12 rashis, on any correctly computed
        chart. Exposed as a public method so callers (and tests) can
        confirm engine correctness directly against this invariant.
        """
        sav = self.compute_sarvashtakavarga(chart)
        return sav.total_bindus == EXPECTED_GRAND_TOTAL
