"""
AstroOS — Argala & Virodhargala Engine Unit Tests
"""

import pytest

from apps.api.services.argala_engine import ArgalaEngine
from apps.api.tests.unit.jaimini_fixtures import make_d1_chart, make_planet


def test_reference_resolution_by_sign_name():
    chart = make_d1_chart("aries", [make_planet("sun", "aries", 10.0)])
    result = ArgalaEngine().compute(chart, "aries")
    assert result.reference_rashi == "aries"
    assert result.reference_label == "aries"


def test_reference_resolution_by_planet_name_matches_sign_lookup():
    chart = make_d1_chart("aries", [make_planet("sun", "aries", 10.0)])
    by_sign = ArgalaEngine().compute(chart, "aries")
    by_planet = ArgalaEngine().compute(chart, "sun")
    assert by_planet.reference_rashi == by_sign.reference_rashi
    assert by_planet.reference_label == "sun"


def test_unrecognized_reference_raises():
    chart = make_d1_chart("aries", [make_planet("sun", "aries", 10.0)])
    with pytest.raises(ValueError):
        ArgalaEngine().compute(chart, "not-a-planet-or-sign")


def test_four_pairs_at_correct_houses():
    chart = make_d1_chart("aries", [make_planet("sun", "aries", 10.0)])
    result = ArgalaEngine().compute(chart, "aries")
    pairs = [(p.argala_house, p.virodhargala_house) for p in result.pairs]
    assert pairs == [(2, 12), (4, 10), (5, 9), (11, 3)]


def test_virodhargala_cancels_when_equal_or_greater_count():
    # Reference aries: 4th house = cancer, 10th (virodhargala) = capricorn.
    # 1 malefic (ketu) in cancer vs 2 malefics (saturn, rahu) in capricorn -> cancelled.
    chart = make_d1_chart(
        "aries",
        [
            make_planet("ketu", "cancer", 10.0),
            make_planet("saturn", "capricorn", 5.0),
            make_planet("rahu", "capricorn", 15.0),
        ],
    )
    result = ArgalaEngine().compute(chart, "aries")
    pair_4_10 = next(p for p in result.pairs if p.argala_house == 4)
    assert pair_4_10.is_active is True
    assert pair_4_10.is_cancelled is True


def test_virodhargala_does_not_cancel_when_weaker():
    # 2 planets in cancer (4th) vs 1 in capricorn (10th) -> argala stands.
    chart = make_d1_chart(
        "aries",
        [
            make_planet("jupiter", "cancer", 10.0),
            make_planet("venus", "cancer", 15.0),
            make_planet("saturn", "capricorn", 5.0),
        ],
    )
    result = ArgalaEngine().compute(chart, "aries")
    pair_4_10 = next(p for p in result.pairs if p.argala_house == 4)
    assert pair_4_10.is_cancelled is False


def test_empty_argala_house_is_not_active():
    chart = make_d1_chart("aries", [make_planet("sun", "aries", 10.0)])
    result = ArgalaEngine().compute(chart, "aries")
    pair_4_10 = next(p for p in result.pairs if p.argala_house == 4)
    assert pair_4_10.is_active is False
    assert pair_4_10.is_cancelled is False  # can't cancel an argala that never existed


def test_strength_score_is_net_benefic_minus_malefic():
    # 2nd house (taurus) from aries occupied by jupiter (benefic) and mars (malefic) -> net 0.
    chart = make_d1_chart(
        "aries", [make_planet("jupiter", "taurus", 5.0), make_planet("mars", "taurus", 15.0)]
    )
    result = ArgalaEngine().compute(chart, "aries")
    pair_2_12 = next(p for p in result.pairs if p.argala_house == 2)
    assert pair_2_12.strength_score == 0.0


def test_net_strength_excludes_cancelled_pairs():
    chart = make_d1_chart(
        "aries",
        [
            make_planet("ketu", "cancer", 10.0),  # 4th, malefic, will be cancelled
            make_planet("saturn", "capricorn", 5.0),
            make_planet("rahu", "capricorn", 15.0),
            make_planet("jupiter", "taurus", 5.0),  # 2nd, benefic, not cancelled
        ],
    )
    result = ArgalaEngine().compute(chart, "aries")
    pair_4_10 = next(p for p in result.pairs if p.argala_house == 4)
    assert pair_4_10.is_cancelled is True
    # net_strength should reflect only the non-cancelled 2nd-house contribution (+1), not the cancelled 4th's -1.
    assert result.net_strength == 1.0
