"""
Unit tests for BPHS Ishta-Kashta Main Strength Engine.
"""

import pytest
from apps.api.services.ishta_kashta_engine import (
    BPHS_DIGNITY_SCALE,
    IshtaKashtaEngine,
)


def test_main_strength_scale():
    # Exalted should map to 60
    ex = IshtaKashtaEngine.get_main_strength("exalted")
    assert ex.main_strength_score == 60
    assert ex.main_strength_rank == 9

    # Own sign should map to 30
    own = IshtaKashtaEngine.get_main_strength("own")
    assert own.main_strength_score == 30
    assert own.main_strength_rank == 7

    # Debilitated should map to 0
    deb = IshtaKashtaEngine.get_main_strength("debilitated")
    assert deb.main_strength_score == 0
    assert deb.main_strength_rank == 1


def test_bhava_50_percent_baseline_rule():
    # Direct aspect => aspect factor 1.0
    rep_direct = IshtaKashtaEngine.calculate_bhava_strength(
        house_number=10,
        lord="Saturn",
        lord_dignity="own",
        lord_is_retrograde=False,
        has_direct_lord_aspect=True,
    )
    assert rep_direct.effective_lord_aspect_factor == 1.0
    assert rep_direct.total_bhava_score == 30.0

    # No direct aspect => aspect factor 0.50 (Jha's 50% baseline presence rule)
    rep_no_aspect = IshtaKashtaEngine.calculate_bhava_strength(
        house_number=10,
        lord="Saturn",
        lord_dignity="own",
        lord_is_retrograde=False,
        has_direct_lord_aspect=False,
    )
    assert rep_no_aspect.effective_lord_aspect_factor == 0.50
    assert rep_no_aspect.total_bhava_score == 15.0
