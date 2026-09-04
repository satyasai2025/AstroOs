"""
AstroOS — MuhurtaEngine Unit Tests

Verifies Hora sequencing and the Rahukalam/Gulikalam/Yamagandam
1/8-of-daylight segment placement against known classical values
(New Delhi, a known Tuesday) — Rahukalam for Tuesday is the 7th of
8 daylight segments (afternoon, ~15:00-16:30 IST region).
"""

from datetime import datetime, timedelta, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper, datetime_to_jd, jd_to_datetime
from apps.api.services.muhurta_engine import MuhurtaEngine

NEW_DELHI_LAT = 28.6139
NEW_DELHI_LON = 77.2090
_EPHE_PATH = "data/ephemeris"


@pytest.fixture
def engine():
    return MuhurtaEngine(EphemerisWrapper(ephemeris_path=_EPHE_PATH))


def test_horas_span_full_day_and_night(engine):
    # 2026-08-18 is a Tuesday
    jd = datetime_to_jd(datetime(2026, 8, 18, 18, 30, tzinfo=timezone.utc))
    result = engine.calculate(jd, NEW_DELHI_LAT, NEW_DELHI_LON)

    assert len(result.horas) == 24
    assert result.horas[0].start_jd == pytest.approx(result.sunrise_jd)
    assert result.horas[11].end_jd == pytest.approx(result.sunset_jd)
    assert result.horas[12].start_jd == pytest.approx(result.sunset_jd)
    assert result.horas[23].end_jd == pytest.approx(result.next_sunrise_jd)

    day_horas = result.horas[:12]
    assert all(h.is_day for h in day_horas)
    night_horas = result.horas[12:]
    assert all(not h.is_day for h in night_horas)

    # First day-hora is ruled by the weekday's own lord (Tuesday = Mars)
    assert result.horas[0].lord == "mars"


def test_rahukalam_is_seventh_of_eight_segments_on_tuesday(engine):
    jd = datetime_to_jd(datetime(2026, 8, 18, 18, 30, tzinfo=timezone.utc))
    result = engine.calculate(jd, NEW_DELHI_LAT, NEW_DELHI_LON)

    day_length = result.sunset_jd - result.sunrise_jd
    segment = day_length / 8.0
    expected_start = result.sunrise_jd + 6 * segment  # 7th segment, 0-indexed 6

    assert result.rahukalam.start_jd == pytest.approx(expected_start)
    assert result.rahukalam.end_jd - result.rahukalam.start_jd == pytest.approx(segment)


def test_periods_are_distinct_segments(engine):
    jd = datetime_to_jd(datetime(2026, 8, 18, 18, 30, tzinfo=timezone.utc))
    result = engine.calculate(jd, NEW_DELHI_LAT, NEW_DELHI_LON)

    starts = {result.rahukalam.start_jd, result.gulikalam.start_jd, result.yamagandam.start_jd}
    assert len(starts) == 3


def test_polar_latitude_raises(engine):
    # High summer at the pole — polar day, no sunset
    jd = datetime_to_jd(datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc))
    with pytest.raises(ValueError):
        engine.calculate(jd, 89.9, 0.0)


def test_matches_drikpanchang_new_delhi_2026_08_15(engine):
    """
    Cross-checked against drikpanchang.com for New Delhi, Sat 2026-08-15:
    sunrise 05:50 AM, sunset 07:01 PM, Rahu Kalam 09:08 AM - 10:47 AM.

    Anchored at local NOON (IST = UTC+5:30), not midnight — midnight falls
    before sunrise and would bracket to the PREVIOUS day's sunrise instead
    (the bug this test guards against).
    """
    jd = datetime_to_jd(datetime(2026, 8, 15, 6, 30, tzinfo=timezone.utc))  # local noon IST
    result = engine.calculate(jd, NEW_DELHI_LAT, NEW_DELHI_LON)

    sunrise_ist = jd_to_datetime(result.sunrise_jd) + timedelta(hours=5, minutes=30)
    sunset_ist = jd_to_datetime(result.sunset_jd) + timedelta(hours=5, minutes=30)
    rahu_start_ist = jd_to_datetime(result.rahukalam.start_jd) + timedelta(hours=5, minutes=30)
    rahu_end_ist = jd_to_datetime(result.rahukalam.end_jd) + timedelta(hours=5, minutes=30)

    assert sunrise_ist.strftime("%H:%M") == "05:50"
    assert sunset_ist.strftime("%H:%M") == "19:00"  # drikpanchang rounds to 19:01
    assert rahu_start_ist.strftime("%H:%M") == "09:07"  # drikpanchang rounds to 09:08
    assert rahu_end_ist.strftime("%H:%M") == "10:46"  # drikpanchang rounds to 10:47


def test_choghadiya_saturday_sequence(engine):
    """
    Saturday's day Choghadiya starts at Kaal and its night starts at Labh —
    standard published values matching drikpanchang.com's convention
    (verified for New Delhi 2026-08-15, a Saturday). The rest of each
    8-slot half follows the fixed cycle: Udveg, Chal, Labh, Amrit, Kaal,
    Shubh, Rog.
    """
    jd = datetime_to_jd(datetime(2026, 8, 15, 6, 30, tzinfo=timezone.utc))  # local noon IST
    result = engine.calculate(jd, NEW_DELHI_LAT, NEW_DELHI_LON)

    assert len(result.choghadiya) == 16
    day = result.choghadiya[:8]
    night = result.choghadiya[8:]

    assert [c.name for c in day] == [
        "Kaal", "Shubh", "Rog", "Udveg", "Chal", "Labh", "Amrit", "Kaal",
    ]
    # Night steps by -2 through the cycle (not +1 like the day sequence) —
    # cross-verified directly against PyJHora's raw gauri_choghadiya_night_table
    # constant (Saturday row [2,0,5,3,1,6,4,2], decoded via its own
    # 0:Udveg/1:Chara/2:Laabha/3:Amrit/4:Kaala/5:Shubha/6:Rog index legend).
    # The previous "+1" sequence asserted here did not match that table.
    assert [c.name for c in night] == [
        "Labh", "Udveg", "Shubh", "Amrit", "Chal", "Rog", "Kaal", "Labh",
    ]
    assert all(c.is_day for c in day)
    assert all(not c.is_day for c in night)
    assert day[0].nature == "inauspicious"  # Kaal
    assert day[1].nature == "auspicious"    # Shubh


def test_panchanga_five_limbs_calculated(engine):
    jd = datetime_to_jd(datetime(2026, 8, 15, 6, 30, tzinfo=timezone.utc))  # 12:00 IST
    result = engine.calculate(jd, NEW_DELHI_LAT, NEW_DELHI_LON)

    # 1. Tithi
    assert result.tithi is not None
    assert 1 <= result.tithi.number <= 30
    assert result.tithi.paksha in ["shukla", "krishna"]
    assert 0.0 <= result.tithi.completion_percent <= 100.0
    assert result.tithi.end_jd is not None and result.tithi.end_jd >= jd
    assert len(result.tithi.lord) > 0
    assert len(result.tithi.group) > 0

    # 2. Vara
    assert result.vara is not None
    assert result.vara.number == 6  # Saturday = 6
    assert result.vara.name == "Saturday"
    assert result.vara.lord == "Saturn"

    # 3. Nakshatra
    assert result.nakshatra is not None
    assert 1 <= result.nakshatra.number <= 27
    assert 1 <= result.nakshatra.pada <= 4
    assert len(result.nakshatra.lord) > 0
    assert 0.0 <= result.nakshatra.degree_in_nakshatra <= 13.3334
    assert result.nakshatra.end_jd is not None and result.nakshatra.end_jd >= jd

    # 4. Yoga
    assert result.yoga is not None
    assert 1 <= result.yoga.number <= 27
    assert len(result.yoga.name) > 0
    assert 0.0 <= result.yoga.completion_percent <= 100.0
    assert result.yoga.end_jd is not None and result.yoga.end_jd >= jd

    # 5. Karana
    assert result.karana is not None
    assert 1 <= result.karana.number <= 60
    assert len(result.karana.name) > 0
    assert result.karana.end_jd is not None and result.karana.end_jd >= jd


def test_calendar_and_celestial_info(engine):
    jd = datetime_to_jd(datetime(2026, 8, 15, 6, 30, tzinfo=timezone.utc))
    result = engine.calculate(jd, NEW_DELHI_LAT, NEW_DELHI_LON)

    assert result.calendar is not None
    assert result.calendar.shaka_year == 1948
    assert result.calendar.shaka_samvatsara == "Parabhava"
    assert result.calendar.vikram_year == 2083
    assert result.calendar.vikram_samvatsara == "Siddharthi"
    assert result.calendar.amanta_masa == "Shravana"
    assert result.calendar.purnimanta_masa == "Shravana"

    assert result.celestial is not None
    assert len(result.celestial.sun_sign) > 0
    assert len(result.celestial.moon_sign) > 0
    assert len(result.celestial.ascendant_sign) > 0


def test_auspicious_and_inauspicious_windows(engine):
    jd = datetime_to_jd(datetime(2026, 8, 15, 6, 30, tzinfo=timezone.utc))
    result = engine.calculate(jd, NEW_DELHI_LAT, NEW_DELHI_LON)

    # Abhijit
    assert result.abhijit_muhurta is not None
    assert result.abhijit_muhurta.start_jd < result.abhijit_muhurta.end_jd
    assert result.sunrise_jd < result.abhijit_muhurta.start_jd < result.sunset_jd
    assert result.abhijit_muhurta.is_auspicious is True

    # Brahma Muhurta
    assert result.brahma_muhurta is not None
    assert result.brahma_muhurta.start_jd < result.brahma_muhurta.end_jd
    assert result.brahma_muhurta.end_jd <= result.sunrise_jd

    # Dur Muhurta
    assert len(result.dur_muhurta) >= 1

    # Choghadiya (8 day + 8 night)
    assert len(result.choghadiya) == 16
    assert all(len(c.lord) > 0 for c in result.choghadiya)

    # Horas (12 day + 12 night)
    assert len(result.horas) == 24


def test_tarabala_chandrabala_panchaka(engine):
    jd = datetime_to_jd(datetime(2026, 8, 15, 6, 30, tzinfo=timezone.utc))
    # Test with custom Janma Nakshatra = 1 (Ashwini) and Janma Rashi = 1 (Mesha)
    result = engine.calculate(
        jd, NEW_DELHI_LAT, NEW_DELHI_LON, natal_nakshatra=1, natal_moon_sign=1
    )

    # Tarabala
    assert result.tarabala is not None
    assert 1 <= result.tarabala.tara_number <= 9
    assert result.tarabala.score in [100.0, 75.0, 20.0]

    # Chandrabala
    assert result.chandrabala is not None
    assert 1 <= result.chandrabala.house_from_natal_moon <= 12
    assert result.chandrabala.score in [0.0, 90.0, 45.0]

    # Panchaka
    assert result.panchaka is not None
    assert 0 <= result.panchaka.remainder <= 8


def test_activity_suitability_playbook(engine):
    jd = datetime_to_jd(datetime(2026, 8, 15, 6, 30, tzinfo=timezone.utc))
    result = engine.calculate(jd, NEW_DELHI_LAT, NEW_DELHI_LON)

    assert len(result.activities) == 8
    activity_ids = [a.activity_id for a in result.activities]
    assert "vivaha" in activity_ids
    assert "griha" in activity_ids
    assert "business" in activity_ids
    assert "property" in activity_ids
    assert "travel" in activity_ids
    assert "medical" in activity_ids
    assert "vidya" in activity_ids
    assert "puja" in activity_ids

    for act in result.activities:
        assert 0.0 <= act.score <= 100.0
        assert act.verdict.startswith(("UTTAMA", "SHUBHA", "MADHYAMA", "ADHAMA"))
        assert len(act.points) >= 1

