"""
Unit tests — Sangya × Graha event signatures and the two-tier wording.

The load-bearing assertion here is completeness: every one of the 10
Sangyas paired with every one of the 9 grahas must produce a signature
whose *forecast* rendering satisfies the forecast policy. If the guarded
table has a hole, this fails at build time rather than being papered
over by runtime redaction in front of a reader.
"""

from __future__ import annotations

import pytest

from apps.api.services.sbc_vedha_engine import GRAHA_VEDHA_RULES, SANGYA_LIFE_AREAS
from packages.shared.event_signature import (
    GUARDED_KEYWORDS,
    GUARDED_SANGYA_AREAS,
    build_signature,
    signatures_for_point,
    verify_guarded_keywords,
)
from packages.shared.temporal_stance import (
    TemporalDirection,
    assert_compliant,
    resolve_policy,
)

SANGYAS = sorted(SANGYA_LIFE_AREAS)
GRAHAS = sorted(GRAHA_VEDHA_RULES)


# ── Table completeness ────────────────────────────────────────────────────────


def test_every_graha_has_a_guarded_restatement():
    assert set(GUARDED_KEYWORDS) == set(GRAHAS)


def test_every_sangya_has_a_guarded_area():
    assert set(GUARDED_SANGYA_AREAS) == set(SANGYAS)


def test_guarded_tables_are_forecast_safe():
    """The whole point of authoring them by hand."""
    assert verify_guarded_keywords() == {}


# ── Signature construction ────────────────────────────────────────────────────


@pytest.mark.parametrize("sangya", SANGYAS)
@pytest.mark.parametrize("graha", GRAHAS)
def test_every_pair_builds(sangya, graha):
    signature = build_signature(sangya, graha)
    assert signature.sangya_key == sangya
    assert signature.graha == graha
    assert signature.classical_keywords
    assert signature.guarded_keywords
    assert signature.classical_area
    assert signature.guarded_area
    assert signature.nature in {"benefic", "malefic"}


@pytest.mark.parametrize("sangya", SANGYAS)
@pytest.mark.parametrize("graha", GRAHAS)
def test_no_forecast_rendering_breaks_the_policy(sangya, graha):
    """Completeness proof for the guarded side, pair by pair."""
    policy = resolve_policy(TemporalDirection.FUTURE)
    described = build_signature(sangya, graha).describe(TemporalDirection.FUTURE)
    assert_compliant({f"{sangya}:{graha}": described}, policy)


def test_past_rendering_keeps_the_classical_words():
    signature = build_signature("vainashika", "mars")
    described = signature.describe(TemporalDirection.PAST)
    assert "financial loss" in described
    assert "ruin" in described.lower()


def test_future_rendering_softens_both_halves():
    signature = build_signature("vainashika", "mars")
    described = signature.describe(TemporalDirection.FUTURE)
    # Guarding the graha keywords alone would leave "complete breakdown" in a
    # forecast, which is blunter than anything it would be paired with.
    assert "accidents" not in described
    assert "complete breakdown" not in described
    # Still specific — this is a category, not a euphemism.
    assert "sudden conflict" in described
    assert "capital" in described


def test_the_two_tiers_actually_differ():
    signature = build_signature("janma", "ketu")
    assert signature.describe(TemporalDirection.PAST) != signature.describe(
        TemporalDirection.FUTURE
    )


def test_present_direction_uses_the_classical_tier():
    """Only forecasts are guarded; a running window is not a prediction."""
    signature = build_signature("manasa", "saturn")
    assert signature.describe(TemporalDirection.PRESENT) == signature.describe(
        TemporalDirection.PAST
    )


def test_nature_matches_the_source_table():
    assert build_signature("karma", "jupiter").nature == "benefic"
    assert not build_signature("karma", "jupiter").is_adverse
    assert build_signature("karma", "saturn").is_adverse


def test_label_is_stable_and_compact():
    assert build_signature("vainashika", "mars").label == "vainashika:mars"


# ── Error handling ────────────────────────────────────────────────────────────


def test_unknown_sangya_raises():
    with pytest.raises(KeyError):
        build_signature("not_a_sangya", "mars")


def test_unknown_graha_raises():
    with pytest.raises(KeyError):
        build_signature("janma", "pluto")


def test_signatures_for_point_skips_unrecognised_grahas():
    """A display-name change must cost one signature, not the whole window."""
    found = signatures_for_point("janma", ["mars", "pluto", "saturn"])
    assert [s.graha for s in found] == ["mars", "saturn"]


def test_signatures_for_point_returns_empty_rather_than_raising():
    assert signatures_for_point("janma", []) == []
