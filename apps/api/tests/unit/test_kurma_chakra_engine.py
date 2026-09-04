"""
AstroOS — Unit Tests for Kurma Chakra Engine
"""

from datetime import datetime, timezone
import pytest

from apps.api.domain.mundane import KurmaDirection
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.kurma_chakra_engine import KurmaChakraEngine


@pytest.fixture
def kurma_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return KurmaChakraEngine(wrapper)


def test_kurma_chakra_9_sectors_evaluation(kurma_engine):
    """Evaluates all 9 sectors of the celestial tortoise."""
    dt = datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)
    state = kurma_engine.evaluate_state(dt, "lahiri")

    assert len(state.sectors) == 9
    directions = [s.direction for s in state.sectors]
    assert KurmaDirection.CENTER in directions
    assert KurmaDirection.EAST in directions
    assert KurmaDirection.WEST in directions
    assert KurmaDirection.NORTH in directions
    assert KurmaDirection.SOUTH in directions

    assert len(state.summary) > 0
