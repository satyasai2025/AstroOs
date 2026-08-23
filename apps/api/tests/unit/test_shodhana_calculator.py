"""
AstroOS — Shodhana Calculator Unit Tests (Module 10 Phase 2)

Every test case here traces directly back to the three stated rules
from C.S. Patel & Aiyar (1957), p. 44 (see shodhana_calculator.py's
module docstring for the verbatim quote).
"""

import pytest

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult
from apps.api.services.ashtakavarga.shodhana_calculator import ShodhanaCalculator

_RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def _make_bhinna(values_by_rashi: dict[str, int], target_planet: str = "sun") -> BhinnashtakavargaResult:
    bindus = [values_by_rashi.get(r, 0) for r in _RASHI_LIST]
    return BhinnashtakavargaResult(
        target_planet=target_planet, bindus_by_rashi=tuple(bindus), total_bindus=sum(bindus),
    )


def test_rule1_subtracts_minimum_from_all_three():
    """Aries=5, Leo=3, Sagittarius=8 -> min=3 -> (2, 0, 5)."""
    bhinna = _make_bhinna({"aries": 5, "leo": 3, "sagittarius": 8})
    calc = ShodhanaCalculator()
    reduced = calc.apply_trikona_shodhana(bhinna)
    assert reduced.bindus_in_rashi("aries") == 2
    assert reduced.bindus_in_rashi("leo") == 0
    assert reduced.bindus_in_rashi("sagittarius") == 5


def test_rule2_no_reduction_when_one_house_has_zero():
    """A zero anywhere in the triad means min=0 -> subtracting 0 changes nothing."""
    bhinna = _make_bhinna({"aries": 5, "leo": 0, "sagittarius": 8})
    calc = ShodhanaCalculator()
    reduced = calc.apply_trikona_shodhana(bhinna)
    assert reduced.bindus_in_rashi("aries") == 5
    assert reduced.bindus_in_rashi("leo") == 0
    assert reduced.bindus_in_rashi("sagittarius") == 8


def test_rule3_all_equal_removes_all():
    """All three equal -> min equals that value -> all become 0."""
    bhinna = _make_bhinna({"aries": 4, "leo": 4, "sagittarius": 4})
    calc = ShodhanaCalculator()
    reduced = calc.apply_trikona_shodhana(bhinna)
    assert reduced.bindus_in_rashi("aries") == 0
    assert reduced.bindus_in_rashi("leo") == 0
    assert reduced.bindus_in_rashi("sagittarius") == 0


def test_trikona_shodhana_applies_to_all_4_triads_independently():
    bhinna = _make_bhinna({
        "aries": 6, "leo": 2, "sagittarius": 4,       # min=2 -> (4,0,2)
        "taurus": 3, "virgo": 3, "capricorn": 3,       # all equal -> (0,0,0)
        "gemini": 1, "libra": 5, "aquarius": 7,        # min=1 -> (0,4,6)
        "cancer": 0, "scorpio": 8, "pisces": 2,        # has zero -> unchanged
    })
    calc = ShodhanaCalculator()
    reduced = calc.apply_trikona_shodhana(bhinna)
    assert (reduced.bindus_in_rashi("aries"), reduced.bindus_in_rashi("leo"), reduced.bindus_in_rashi("sagittarius")) == (4, 0, 2)
    assert (reduced.bindus_in_rashi("taurus"), reduced.bindus_in_rashi("virgo"), reduced.bindus_in_rashi("capricorn")) == (0, 0, 0)
    assert (reduced.bindus_in_rashi("gemini"), reduced.bindus_in_rashi("libra"), reduced.bindus_in_rashi("aquarius")) == (0, 4, 6)
    assert (reduced.bindus_in_rashi("cancer"), reduced.bindus_in_rashi("scorpio"), reduced.bindus_in_rashi("pisces")) == (0, 8, 2)


def test_trikona_shodhana_never_produces_negative_values():
    bhinna = _make_bhinna({
        "aries": 8, "leo": 0, "sagittarius": 5,
        "taurus": 7, "virgo": 7, "capricorn": 1,
    })
    calc = ShodhanaCalculator()
    reduced = calc.apply_trikona_shodhana(bhinna)
    assert all(v >= 0 for v in reduced.bindus_by_rashi)


# ── Ekadhipatya Shodhana — a REPLACE operation between a planet's own
# co-lorded pair, not a "subtract the pair minimum" rule, and it only
# ever touches the bindu table of the planet that owns that pair (Sun
# and Moon own no co-lorded rashi, so they're never touched). Verified
# byte-for-byte against PyJHora's jhora.horoscope.chart.ashtakavarga.
# _ekadhipatya_sodhana() for a real chart (1995-01-01 12:00 UTC, New
# Delhi) — see pinda_engine.py's module docstring for that cross-check. ─

def test_ekadhipatya_unoccupied_pair_both_become_the_lower_value():
    """Mars owns Aries/Scorpio. Neither occupied, values differ -> both become the lower value (not subtracted)."""
    bhinna = _make_bhinna({"aries": 6, "scorpio": 2}, target_planet="mars")
    calc = ShodhanaCalculator()
    reduced = calc.apply_ekadhipatya_shodhana(bhinna, occupied_rashis=set())
    assert reduced.bindus_in_rashi("aries") == 2
    assert reduced.bindus_in_rashi("scorpio") == 2


def test_ekadhipatya_unoccupied_pair_equal_values_both_become_zero():
    bhinna = _make_bhinna({"aries": 4, "scorpio": 4}, target_planet="mars")
    calc = ShodhanaCalculator()
    reduced = calc.apply_ekadhipatya_shodhana(bhinna, occupied_rashis=set())
    assert reduced.bindus_in_rashi("aries") == 0
    assert reduced.bindus_in_rashi("scorpio") == 0


def test_ekadhipatya_protects_occupied_house_from_reduction():
    """The one stated exception: a house occupied by a planet is never reduced — the empty one is set to the occupied one's value (copied) if it isn't already lower."""
    bhinna = _make_bhinna({"aries": 6, "scorpio": 2}, target_planet="mars")
    calc = ShodhanaCalculator()
    reduced = calc.apply_ekadhipatya_shodhana(bhinna, occupied_rashis={"aries"})
    assert reduced.bindus_in_rashi("aries") == 6  # protected, unchanged
    assert reduced.bindus_in_rashi("scorpio") == 0  # lower than occupied's value -> zeroed


def test_ekadhipatya_occupied_house_lower_value_copied_to_empty():
    """Occupied rashi's value is LOWER than the empty one's -> the empty one is set equal to it (not zeroed)."""
    bhinna = _make_bhinna({"aries": 2, "scorpio": 6}, target_planet="mars")
    calc = ShodhanaCalculator()
    reduced = calc.apply_ekadhipatya_shodhana(bhinna, occupied_rashis={"aries"})
    assert reduced.bindus_in_rashi("aries") == 2  # protected, unchanged
    assert reduced.bindus_in_rashi("scorpio") == 2  # copied from occupied aries


def test_ekadhipatya_both_occupied_neither_reduced():
    bhinna = _make_bhinna({"aries": 6, "scorpio": 2}, target_planet="mars")
    calc = ShodhanaCalculator()
    reduced = calc.apply_ekadhipatya_shodhana(bhinna, occupied_rashis={"aries", "scorpio"})
    assert reduced.bindus_in_rashi("aries") == 6
    assert reduced.bindus_in_rashi("scorpio") == 2


def test_ekadhipatya_zero_in_either_rashi_means_no_change():
    bhinna = _make_bhinna({"aries": 6, "scorpio": 0}, target_planet="mars")
    calc = ShodhanaCalculator()
    reduced = calc.apply_ekadhipatya_shodhana(bhinna, occupied_rashis=set())
    assert reduced.bindus_in_rashi("aries") == 6
    assert reduced.bindus_in_rashi("scorpio") == 0


def test_leo_and_cancer_never_touched_by_ekadhipatya():
    """Sun (Leo) and Moon (Cancer) rule only one sign each — no co-lorded pair, never reduced."""
    bhinna = _make_bhinna({"leo": 5, "cancer": 3}, target_planet="sun")
    calc = ShodhanaCalculator()
    reduced = calc.apply_ekadhipatya_shodhana(bhinna, occupied_rashis=set())
    assert reduced.bindus_in_rashi("leo") == 5
    assert reduced.bindus_in_rashi("cancer") == 3


def test_ekadhipatya_only_touches_the_owning_planets_own_pair():
    """Each of the 5 planets with a co-lorded pair only has ITS OWN pair reduced — never all 5 pairs at once."""
    values = {
        "aries": 6, "scorpio": 2,
        "taurus": 5, "libra": 1,
        "gemini": 4, "virgo": 4,
        "sagittarius": 7, "pisces": 3,
        "capricorn": 8, "aquarius": 6,
    }
    calc = ShodhanaCalculator()
    cases = [
        ("mars", "aries", "scorpio", (2, 2)),
        ("venus", "taurus", "libra", (1, 1)),
        ("mercury", "gemini", "virgo", (0, 0)),
        ("jupiter", "sagittarius", "pisces", (3, 3)),
        ("saturn", "capricorn", "aquarius", (6, 6)),
    ]
    for planet, r1, r2, expected in cases:
        bhinna = _make_bhinna(values, target_planet=planet)
        reduced = calc.apply_ekadhipatya_shodhana(bhinna, occupied_rashis=set())
        assert (reduced.bindus_in_rashi(r1), reduced.bindus_in_rashi(r2)) == expected, planet
        # Rashis outside this planet's own pair are untouched by ekadhipatya.
        assert reduced.bindus_in_rashi("taurus" if planet != "venus" else "aries") == values["taurus" if planet != "venus" else "aries"]


# ── apply_both — sequential pipeline ──────────────────────────────────────────

def test_apply_both_runs_trikona_then_ekadhipatya_sequentially():
    """
    Mars owns Aries/Scorpio. Aries starts at 6. Trikona group
    (Aries/Leo/Sagittarius) min=2 (Leo=2) -> Aries becomes 4. Then
    Ekadhipatya pair (Aries/Scorpio): Scorpio=1 (untouched by trikona,
    different group), both nonzero and unoccupied, unequal -> both
    become the lower value min(4,1)=1.
    """
    bhinna = _make_bhinna({"aries": 6, "leo": 2, "sagittarius": 8, "scorpio": 1}, target_planet="mars")
    calc = ShodhanaCalculator()
    result = calc.apply_both(bhinna, occupied_rashis=set())
    assert result.bindus_in_rashi("aries") == 1
    assert result.bindus_in_rashi("leo") == 0
    assert result.bindus_in_rashi("scorpio") == 1


def test_apply_both_preserves_total_bindus_consistency():
    bhinna = _make_bhinna({
        "aries": 6, "leo": 2, "sagittarius": 8, "scorpio": 1,
        "taurus": 5, "virgo": 3, "capricorn": 4, "libra": 2,
    })
    calc = ShodhanaCalculator()
    result = calc.apply_both(bhinna, occupied_rashis=set())
    assert result.total_bindus == sum(result.bindus_by_rashi)


def test_target_planet_preserved_through_reduction():
    bhinna = _make_bhinna({"aries": 5})
    bhinna = BhinnashtakavargaResult(
        target_planet="jupiter", bindus_by_rashi=bhinna.bindus_by_rashi, total_bindus=bhinna.total_bindus,
    )
    calc = ShodhanaCalculator()
    reduced = calc.apply_both(bhinna, occupied_rashis=set())
    assert reduced.target_planet == "jupiter"
