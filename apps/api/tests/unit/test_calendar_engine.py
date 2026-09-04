"""
AstroOS — CalendarEngine Unit Tests

Verifies Masa and Samvatsara against real drikpanchang.com output for
New Delhi, Saturday 2026-08-15: Amanta "Shravana", Purnimanta "Shravana",
Shaka Samvat 1948 "Parabhava", Vikram Samvat 2083 "Siddharthi".
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.calendar_engine import CalendarEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, datetime_to_jd

_EPHE_PATH = "data/ephemeris"


@pytest.fixture
def engine():
    return CalendarEngine(EphemerisWrapper(ephemeris_path=_EPHE_PATH))


def test_matches_drikpanchang_new_delhi_2026_08_15(engine):
    jd = datetime_to_jd(datetime(2026, 8, 15, 6, 30, tzinfo=timezone.utc))  # local noon IST
    result = engine.calculate(jd)

    assert result.masa.amanta == "Shravana"
    assert result.masa.purnimanta == "Shravana"
    assert result.samvatsara.shaka_year == 1948
    assert result.samvatsara.shaka_samvatsara == "Parabhava"
    assert result.samvatsara.vikram_year == 2083
    assert result.samvatsara.vikram_samvatsara == "Siddharthi"


def test_chaitra_start_is_ugadi_2026(engine):
    """Chaitra Shukla Pratipada 2026 (Ugadi) is 2026-03-19 — the year
    turnover this engine's Shaka/Vikram year numbers are anchored to."""
    jd = datetime_to_jd(datetime(2026, 8, 15, 6, 30, tzinfo=timezone.utc))
    amavasya_jd, sun_rashi = engine._find_amavasya_before(jd)
    chaitra_jd = engine._find_chaitra_start(amavasya_jd, sun_rashi)

    import swisseph as swe
    year, month, day, _ = swe.revjul(chaitra_jd, swe.GREG_CAL)
    assert (year, month) == (2026, 3)
    assert 17 <= day <= 21  # allow for the ~1-day IST/UT and search-step tolerance


def test_krishna_paksha_purnimanta_rolls_to_next_amanta_month(engine):
    """During Krishna Paksha, Purnimanta names the NEXT Amanta month —
    2026-08-28 falls in Krishna Paksha of the Shravana Amanta month, so
    Purnimanta should already read 'Bhadrapada'."""
    jd = datetime_to_jd(datetime(2026, 8, 28, 6, 30, tzinfo=timezone.utc))
    result = engine.calculate(jd)

    assert result.masa.amanta == "Shravana"
    assert result.masa.purnimanta == "Bhadrapada"
