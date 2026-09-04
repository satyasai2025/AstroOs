"""
Unit tests for Divisional Synthesis & Vimshopaka Bala Engine.
"""

import pytest
from apps.api.services.divisional_synthesis_engine import (
    DivisionalSynthesisEngine,
    DivisionalVerdict,
    VimshopakaScheme,
    VIMSHOPAKA_WEIGHTS,
)


def test_vimshopaka_scheme_sums_to_twenty():
    """Verify all 4 canonical BPHS Vimshopaka schemes sum exactly to 20.0 points."""
    for scheme, weights in VIMSHOPAKA_WEIGHTS.items():
        total = sum(weights.values())
        assert abs(total - 20.0) < 1e-5, f"{scheme} sum is {total}, expected 20.0"

    # Specific category weights check
    assert VIMSHOPAKA_WEIGHTS[VimshopakaScheme.SAPTAVARGA][7] == 2.5
    assert VIMSHOPAKA_WEIGHTS[VimshopakaScheme.SAPTAVARGA][9] == 4.5
    assert VIMSHOPAKA_WEIGHTS[VimshopakaScheme.DASHAVARGA][10] == 1.5
    assert VIMSHOPAKA_WEIGHTS[VimshopakaScheme.DASHAVARGA][60] == 5.0
    assert VIMSHOPAKA_WEIGHTS[VimshopakaScheme.SHODASHAVARGA][1] == 3.5
    assert VIMSHOPAKA_WEIGHTS[VimshopakaScheme.SHODASHAVARGA][60] == 4.0


def test_divisional_synthesis_reinforcing():
    engine = DivisionalSynthesisEngine()
    # Sun in Aries (exalted in D1)
    rep = engine.synthesize_d1_vs_divisional(
        planet="Sun",
        sidereal_lon=10.0,  # 10° Aries -> Exalted in D1
        target_varga=10,    # D10
        scheme=VimshopakaScheme.DASHAVARGA,
    )
    assert rep.d1_strength.dignity_label == "exalted"
    assert rep.d1_strength.main_strength_rank == 9
    assert rep.d1_strength.vimshopaka_weight == 3.0  # In Dashavarga, D1=3.0


def test_divisional_synthesis_d1_prevails_guardrail():
    engine = DivisionalSynthesisEngine()
    # Mars in Capricorn (28° - Exalted in D1)
    rep = engine.synthesize_d1_vs_divisional(
        planet="Mars",
        sidereal_lon=298.0,  # 28° Capricorn -> Exalted in D1
        target_varga=10,
        scheme=VimshopakaScheme.SHODASHAVARGA,
    )
    assert rep.d1_strength.dignity_label == "exalted"
    assert rep.d1_strength.vimshopaka_weight == 3.5  # In Shodash, D1=3.5
    # D1 weight (3.5) dominates D10 weight (0.5)
    assert rep.d1_strength.vimshopaka_weight > rep.divisional_strength.vimshopaka_weight
