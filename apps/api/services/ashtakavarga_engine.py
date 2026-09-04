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
from apps.api.services.ashtakavarga.kakshya_calculator import KakshyaCalculator, KakshyaTransitEvaluation
from apps.api.services.ashtakavarga.shodhana_calculator import ShodhanaCalculator
from apps.api.services.ashtakavarga.shodhya_pinda_calculator import ShodhyaPindaCalculator, ShodhyaPindaResult
from packages.shared.ashtakavarga_bindu_table import CONTRIBUTORS, EXPECTED_GRAND_TOTAL, TARGET_PLANETS

_RULE_VERSION = "1.0"

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


class AshtakavargaEngine:
    """Stateless — needs only an already-built D1Chart."""

    def __init__(
        self,
        calculator: BhinnashtakavargaCalculator | None = None,
        shodhana_calculator: ShodhanaCalculator | None = None,
        shodhya_pinda_calculator: ShodhyaPindaCalculator | None = None,
        kakshya_calculator: KakshyaCalculator | None = None,
    ) -> None:
        self._calculator = calculator or BhinnashtakavargaCalculator()
        self._shodhana = shodhana_calculator or ShodhanaCalculator()
        self._shodhya_pinda = shodhya_pinda_calculator or ShodhyaPindaCalculator()
        self._kakshya = kakshya_calculator or KakshyaCalculator()

    def _contributor_rashis(self, chart: D1Chart) -> dict[str, str]:
        rashis = {p.planet: p.rashi for p in chart.planets if p.planet in CONTRIBUTORS}
        rashis["lagna"] = chart.ascendant.rashi
        return rashis

    def _occupied_rashis(self, chart: D1Chart) -> set[str]:
        """
        Rashis occupied by ANY graha (including Rahu/Ketu) — used by
        Ekadhipatya Shodhana's occupied-house protection. Previously
        scoped to only the 7 classical grahas; cross-verified against
        PyJHora's jhora.horoscope.chart.ashtakavarga._ekadhipatya_sodhana(),
        which checks raw chart occupancy (including the nodes) — a rashi
        with only Rahu or Ketu in it is still "occupied" for this rule,
        even though the nodes aren't Bhinnashtakavarga contributors.
        """
        return {p.rashi for p in chart.planets}

    def compute_bhinnashtakavarga(self, chart: D1Chart) -> list[BhinnashtakavargaResult]:
        """All 7 planets' individual Ashtakavarga tables (unreduced)."""
        contributor_rashis = self._contributor_rashis(chart)
        return self._calculator.calculate_all(contributor_rashis)

    def compute_sarvashtakavarga(
        self,
        chart: D1Chart,
        bhinna_results: list[BhinnashtakavargaResult] | None = None,
    ) -> SarvashtakavargaResult:
        """
        Sum of all 7 planetary Bhinnashtakavargas (Lagna's own is
        excluded from the sum, per classical convention). Always
        unreduced — Shodhana applies only to Bhinnashtakavarga, per the
        source (see shodhana_calculator.py).

        `bhinna_results` lets a caller that already computed
        Bhinnashtakavarga for this chart (e.g. compute_all) pass it
        straight through instead of triggering a second full
        recalculation. Defaults to None, which computes it fresh —
        existing single-argument callers are unaffected.
        """
        if bhinna_results is None:
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
        self,
        chart: D1Chart,
        bhinna_results: list[BhinnashtakavargaResult] | None = None,
    ) -> list[BhinnashtakavargaResult]:
        """
        All 7 planets' Bhinnashtakavarga after both classical Shodhana
        (reduction) passes — Trikona Shodhana then Ekadhipatya Shodhana,
        applied sequentially per the source. See shodhana_calculator.py.

        `bhinna_results` reuses an already-computed (unreduced)
        Bhinnashtakavarga list instead of recomputing it — see
        compute_sarvashtakavarga's docstring for the same pattern.
        """
        occupied = self._occupied_rashis(chart)
        if bhinna_results is None:
            bhinna_results = self.compute_bhinnashtakavarga(chart)
        return [
            self._shodhana.apply_both(bhinna, occupied)
            for bhinna in bhinna_results
        ]

    def verify_checksum(
        self,
        chart: D1Chart,
        sarvashtakavarga: SarvashtakavargaResult | None = None,
    ) -> bool:
        """
        Classical validation: Sarvashtakavarga must always total exactly
        337 bindus across the 12 rashis, on any correctly computed
        chart. Exposed as a public method so callers (and tests) can
        confirm engine correctness directly against this invariant.

        `sarvashtakavarga` lets a caller that already computed it pass
        it straight through instead of recomputing — see
        compute_sarvashtakavarga's docstring for the same pattern.
        """
        sav = sarvashtakavarga if sarvashtakavarga is not None else self.compute_sarvashtakavarga(chart)
        return sav.total_bindus == EXPECTED_GRAND_TOTAL

    def compute_shodhya_pinda(
        self,
        chart: D1Chart,
        reduced_bhinna: list[BhinnashtakavargaResult] | None = None,
    ) -> dict[str, ShodhyaPindaResult]:
        """
        Computes Rashi Pinda, Graha Pinda, and Shodhya Pinda for all 7 planets.
        """
        if reduced_bhinna is None:
            reduced_bhinna = self.compute_reduced_bhinnashtakavarga(chart)

        reduced_bav_map = {b.target_planet: b.bindus_by_rashi for b in reduced_bhinna}
        planet_positions_rashi = {p.planet: p.rashi for p in chart.planets}

        return self._shodhya_pinda.calculate_all(reduced_bav_map, planet_positions_rashi)

    def compute_prastarashtakavarga(
        self,
        chart: D1Chart,
    ) -> dict[str, dict[str, list[int]]]:
        """
        Computes 8x12 Prastarashtakavarga matrix for all 7 planets.
        """
        contributor_rashis = self._contributor_rashis(chart)
        return self._kakshya.compute_all_prastara(contributor_rashis)

    def evaluate_transit_kakshya(
        self,
        transiting_planet: str,
        transit_longitude: float,
        chart: D1Chart,
    ) -> KakshyaTransitEvaluation:
        """
        Evaluates whether a transiting planet has an active bindu in its current kakshya.
        """
        contributor_rashis = self._contributor_rashis(chart)
        prastara = self._kakshya.compute_prastara_matrix(transiting_planet, contributor_rashis)
        return self._kakshya.evaluate_transit_kakshya(
            transiting_planet=transiting_planet,
            transit_longitude=transit_longitude,
            prastara_matrix=prastara,
        )
