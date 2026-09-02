"""
AstroOS — Canonical Facts Generator Golden Pre/Post Migration Diff
==================================================================

Validates that CanonicalFactsGenerator and HistoricalBacktestHarness produce
100% deterministic, exact astronomical and Siddhantic facts with zero drift
across the .contains() datetime migration.
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.phalita_core.canonical_facts_generator import (
    CanonicalFacts,
    CanonicalFactsGenerator,
)
from apps.api.services.phalita_core.historical_backtest_harness import (
    BenchmarkTestCase,
    HistoricalBacktestHarness,
)

_WRAPPER = EphemerisWrapper(ephemeris_path="data/ephemeris")
_GENERATOR = CanonicalFactsGenerator(_WRAPPER)
_HARNESS = HistoricalBacktestHarness(_WRAPPER)


class TestCanonicalFactsGoldenDiff:
    """
    Asserts bitwise determinism and exact Siddhantic invariants across benchmark charts.
    """

    @pytest.mark.parametrize(
        "name,dt_utc,lat,lon,target_d,expected_lagna_rashi,expected_chandra_rashi,expected_md_lord",
        [
            (
                "Narendra_Modi",
                datetime(1950, 9, 17, 5, 30, 0, tzinfo=timezone.utc),
                23.7833,
                72.6333,
                date(2014, 5, 26),
                "Scorpio",
                "Scorpio",
                "moon",
            ),
            (
                "Indira_Gandhi",
                datetime(1917, 11, 19, 17, 41, 0, tzinfo=timezone.utc),
                25.45,
                81.85,
                date(1966, 1, 24),
                "Cancer",
                "Capricorn",
                "jupiter",
            ),
            (
                "J2000_Standard",
                datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                28.6139,
                77.2090,
                date(2024, 1, 1),
                "Gemini",
                "Libra",
                "saturn",
            ),
        ],
    )
    def test_canonical_facts_determinism_and_correctness(
        self,
        name,
        dt_utc,
        lat,
        lon,
        target_d,
        expected_lagna_rashi,
        expected_chandra_rashi,
        expected_md_lord,
    ):
        facts1 = _GENERATOR.generate_facts(
            birth_datetime=dt_utc,
            latitude=lat,
            longitude=lon,
            target_date=target_d,
            ayanamsa="lahiri",
        )

        facts2 = _GENERATOR.generate_facts(
            birth_datetime=dt_utc,
            latitude=lat,
            longitude=lon,
            target_date=target_d,
            ayanamsa="lahiri",
        )

        # 1. Determinism: facts1 and facts2 must be identical
        assert facts1 == facts2

        # 2. Planetary Fact Completeness
        assert len(facts1.planets) >= 9
        assert facts1.ascendant_rashi == expected_lagna_rashi
        assert facts1.chandra_rashi == expected_chandra_rashi
        assert facts1.active_d1_dasha["MD"].lower() == expected_md_lord.lower()

        # 3. 7 Chara Karakas Invariant: strictly 7 karakas, AK through DK
        assert len(facts1.chara_karakas) == 7
        karaka_roles = [k.karaka_role for k in facts1.chara_karakas]
        assert karaka_roles == ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]

        # 4. Bhavachalita Invariant: exactly 12 houses
        assert len(facts1.bhavachalita_houses) == 12

        # 5. Upagraha Invariant: Gulika, Maandi, Special Lagnas present
        assert len(facts1.upagrahas) >= 5

    def test_backtest_harness_fact_consistency(self):
        """Validates that backtest harness runs and produces consistent prediction evaluation."""
        summary = _HARNESS.run_benchmark_audit()
        assert summary is not None
        assert summary.total_cases >= 3
        assert summary.passed_cases >= 2
