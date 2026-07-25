"""
AstroOS — Ashtakavarga Bindu Table Unit Tests (Module 10)

The checksum validation described in the table's own module docstring,
run as an automated regression test — if this table is ever edited,
this test catches any count-level error immediately.
"""

import pytest

from packages.shared.ashtakavarga_bindu_table import (
    BINDU_TABLE,
    CONTRIBUTORS,
    EXPECTED_GRAND_TOTAL,
    EXPECTED_PLANET_TOTALS,
    TARGET_PLANETS,
)


@pytest.mark.parametrize("planet", TARGET_PLANETS)
def test_planet_total_matches_expected_checksum(planet):
    total = sum(len(houses) for houses in BINDU_TABLE[planet].values())
    assert total == EXPECTED_PLANET_TOTALS[planet]


def test_grand_total_is_337():
    grand_total = sum(
        len(houses)
        for contributors in BINDU_TABLE.values()
        for houses in contributors.values()
    )
    assert grand_total == EXPECTED_GRAND_TOTAL


@pytest.mark.parametrize("planet", TARGET_PLANETS)
def test_every_planet_has_all_8_contributors(planet):
    assert set(BINDU_TABLE[planet].keys()) == set(CONTRIBUTORS)


def test_table_covers_all_7_target_planets():
    assert set(BINDU_TABLE.keys()) == set(TARGET_PLANETS)


@pytest.mark.parametrize("planet", TARGET_PLANETS)
def test_all_house_offsets_within_1_to_12(planet):
    for contributor, houses in BINDU_TABLE[planet].items():
        for h in houses:
            assert 1 <= h <= 12, f"{planet}/{contributor} has invalid house {h}"


@pytest.mark.parametrize("planet", TARGET_PLANETS)
def test_no_duplicate_houses_within_a_contributor_list(planet):
    for contributor, houses in BINDU_TABLE[planet].items():
        assert len(houses) == len(set(houses)), f"{planet}/{contributor} has duplicates"
