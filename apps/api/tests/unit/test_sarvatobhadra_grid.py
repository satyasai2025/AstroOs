"""
AstroOS — Sarvatobhadra Chakra Grid Unit Tests

Verifies the hand-derived 28-nakshatra border layout against all 4
worked examples published by Saravali (https://saravali.github.io/
astrology/sbc_vedhas.html) — see packages/shared/sarvatobhadra_grid.py's
module docstring for the full sourcing/derivation note. All 4 nakshatras
x all 3 Vedha types (12 checks) must match exactly for the grid to be
trusted; this is the executable form of that verification.
"""

import pytest

from packages.shared.sarvatobhadra_grid import (
    SBC_BORDER,
    backward_vedha_target,
    forward_vedha_target,
    longitude_to_sbc_nakshatra,
    opposite_vedha_target,
)

# (nakshatra, forward, opposite, backward) — Saravali's 4 worked examples.
_SARAVALI_EXAMPLES = [
    ("ashwini", "rohini", "purva_phalguni", "jyeshtha"),
    ("swati", "jyeshtha", "shatabhisha", "rohini"),
    ("purva_ashadha", "uttara_bhadrapada", "ardra", "hasta"),
    ("krittika", "vishakha", "shravana", "bharani"),
]


@pytest.mark.parametrize("nakshatra,forward,opposite,backward", _SARAVALI_EXAMPLES)
def test_matches_saravali_worked_examples(nakshatra, forward, opposite, backward):
    assert forward_vedha_target(nakshatra) == forward
    assert opposite_vedha_target(nakshatra) == opposite
    assert backward_vedha_target(nakshatra) == backward


def test_grid_has_all_28_nakshatras():
    assert len(SBC_BORDER) == 28
    assert "abhijit" in SBC_BORDER


def test_every_nakshatra_has_valid_distinct_targets():
    for nak in SBC_BORDER:
        f = forward_vedha_target(nak)
        o = opposite_vedha_target(nak)
        b = backward_vedha_target(nak)
        for target in (f, o, b):
            assert target in SBC_BORDER
            assert target != nak


def test_opposite_is_involutive():
    """A straight-across relationship must point back at itself: if A's
    opposite is B, B's opposite must be A."""
    for nak in SBC_BORDER:
        other = opposite_vedha_target(nak)
        assert opposite_vedha_target(other) == nak


def test_forward_and_backward_are_inverse_directions():
    """Forward from A lands somewhere B; going Backward from B should
    return to A (same diagonal, opposite rotational sense)."""
    for nak in SBC_BORDER:
        fwd_target = forward_vedha_target(nak)
        assert backward_vedha_target(fwd_target) == nak


@pytest.mark.parametrize(
    "longitude,expected",
    [
        (0.0, "ashwini"),
        (270.0, "uttara_ashadha"),  # well inside Uttara Ashadha, away from the Abhijit boundary
        (278.0, "abhijit"),  # inside the carved-out Abhijit arc
        (285.0, "shravana"),  # well inside Shravana, away from the Abhijit boundary
        (359.99, "revati"),
    ],
)
def test_longitude_to_sbc_nakshatra(longitude, expected):
    assert longitude_to_sbc_nakshatra(longitude) == expected
