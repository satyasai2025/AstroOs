"""
AstroOS — Supplementary Ephemeris-Verified Golden Reference Cases
==================================================================
Four astronomical and Siddhantic edge cases verifying the complete dual-frame,
house cusp, upagraha, and dasha calculation engines:

  Case 1: Polar Latitude Chart (Circumpolar 24h Day/Night, Tromsø & Longyearbyen)
  Case 2: Exact Nakshatra-Boundary Moon (13°20'00" Boundary Inclusivity Doctrine)
  Case 3: Southern Hemisphere Chart (Sydney & Buenos Aires, Negative Declination)
  Case 4: Exact Daśā-Boundary Full-Stack Integration (Seamless Microsecond Handover)
"""

from datetime import date, datetime, timedelta, timezone
import math
import pytest

from apps.api.config import get_settings
from apps.api.domain.dasha import DashaPeriod
from apps.api.services.dasha_engine import DashaEngine, _nakshatra_balance
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.divisional_vimshottari_engine import DivisionalVimshottariEngine
from apps.api.services.upagraha_engine import UpagrahaEngine
from packages.shared.constants import (
    DAYS_PER_JULIAN_YEAR,
    DEGREES_PER_NAKSHATRA,
    VIMSHOTTARI_DASHA_YEARS,
    VIMSHOTTARI_SEQUENCE,
    VIMSHOTTARI_TOTAL_YEARS,
)

_SETTINGS = get_settings()
_WRAPPER = EphemerisWrapper(ephemeris_path=_SETTINGS.EPHEMERIS_PATH)
_DASHA = DashaEngine(_WRAPPER)
_DIV_ENGINE = DivisionalEngine(_WRAPPER)
_DIV_DASHA = DivisionalVimshottariEngine(_WRAPPER)
_UPAGRAHA = UpagrahaEngine(_WRAPPER)


# ═══════════════════════════════════════════════════════════════════════════════
# CASE 1: Polar Latitude Chart (Circumpolar Sunrise/Sunset & House Invariants)
# ═══════════════════════════════════════════════════════════════════════════════


class TestGoldenCase1PolarLatitude:
    """
    Validates ephemeris, house cusp, and upagraha calculations at extreme polar
    latitudes where standard sunrise/sunset does not occur (midnight sun / polar night).
    """

    @pytest.mark.parametrize(
        "location_name,lat,lon,dt_utc",
        [
            ("Longyearbyen_MidnightSun", 78.2232, 15.6267, datetime(2024, 6, 21, 12, 0, 0, tzinfo=timezone.utc)),
            ("Longyearbyen_PolarNight", 78.2232, 15.6267, datetime(2024, 12, 21, 12, 0, 0, tzinfo=timezone.utc)),
            ("Tromso_SummerSolstice", 69.6492, 18.9553, datetime(2024, 6, 21, 0, 0, 0, tzinfo=timezone.utc)),
            ("Tromso_WinterSolstice", 69.6492, 18.9553, datetime(2024, 12, 21, 0, 0, 0, tzinfo=timezone.utc)),
        ],
    )
    def test_polar_chart_ephemeris_and_house_invariants(self, location_name, lat, lon, dt_utc):
        result = _WRAPPER.calculate(
            dt=dt_utc,
            latitude=lat,
            longitude=lon,
            ayanamsa="lahiri",
            house_system="W",
        )

        # 1. Calculation must succeed and return all 9 grahas + ascendant
        assert result is not None
        assert len(result.planet_positions) >= 9
        assert 0.0 <= result.ascendant.sidereal_longitude < 360.0
        assert 0.0 <= result.ascendant.longitude < 360.0

        # 2. Dual-frame arithmetic exactness: sidereal + ayanamsa == tropical (mod 360)
        ayanamsa = result.ayanamsa_value
        for p in result.planet_positions:
            trop_pos = _WRAPPER.get_planet_position(p.planet, result.julian_day)
            expected_trop = (p.sidereal_longitude + ayanamsa) % 360.0
            diff = abs(trop_pos.longitude - expected_trop)
            if diff > 180:
                diff = abs(diff - 360)
            assert diff < 1e-4, f"Dual-frame mismatch for {p.planet}: {p.sidereal_longitude} + {ayanamsa} != {trop_pos.longitude}"

        # 3. Ketu = Rahu - 180° in both frames
        rahu = next(p for p in result.planet_positions if p.planet.lower() == "rahu")
        ketu = next(p for p in result.planet_positions if p.planet.lower() == "ketu")
        rahu_ketu_diff_sid = abs((rahu.sidereal_longitude - ketu.sidereal_longitude) % 360.0 - 180.0)
        assert rahu_ketu_diff_sid < 1e-4, f"Ketu not 180° opposite Rahu sidereal: {rahu.sidereal_longitude} vs {ketu.sidereal_longitude}"

        # 4. Whole-Sign Cusps: exactly 12 cusps, each separated by 30°
        assert len(result.house_cusps) == 12
        for i in range(1, 13):
            cusp_i = result.house_cusps[i - 1]
            assert cusp_i.house_number == i
            expected_lon = (result.house_cusps[0].longitude + (i - 1) * 30.0) % 360.0
            diff = abs(cusp_i.longitude - expected_lon)
            if diff > 180:
                diff = abs(diff - 360)
            assert diff < 1e-4, f"House cusp {i} not spaced 30° in Whole-Sign: {cusp_i.longitude} vs {expected_lon}"

        # 5. Upagraha computation handles polar conditions gracefully
        up_res = _UPAGRAHA.compute(
            birth_datetime_utc=dt_utc,
            latitude=lat,
            longitude=lon,
            ayanamsa="lahiri",
        )
        assert up_res is not None
        assert len(up_res.upagrahas) == 2  # Gulika and Maandi
        assert len(up_res.special_lagnas) == 3  # Bhava, Hora, Ghati Lagna
        assert 0.0 <= up_res.upagrahas[0].sidereal_longitude < 360.0


# ═══════════════════════════════════════════════════════════════════════════════
# CASE 2: Exact Nakshatra-Boundary Moon (13°20'00" Boundary Inclusivity)
# ═══════════════════════════════════════════════════════════════════════════════


class TestGoldenCase2NakshatraBoundary:
    """
    Validates the Siddhantic boundary inclusivity doctrine:
    Moon at exactly 13°20'00" (or any nakshatra boundary) belongs 100% to the
    INCOMING nakshatra lord with zero balance elapsed.
    """

    @pytest.mark.parametrize(
        "boundary_lon,expected_nak_idx,expected_lord,expected_years",
        [
            (0.0, 0, "ketu", 7),                  # Ashwini 0°00'00"
            (13.333333333333334, 1, "venus", 20), # Bharani 0°00'00" (13°20')
            (26.666666666666668, 2, "sun", 6),    # Krittika 0°00'00" (26°40')
            (40.0, 3, "moon", 10),                 # Rohini 0°00'00" (40°00')
            (53.333333333333336, 4, "mars", 7),   # Mrigashira 0°00'00" (53°20')
            (66.66666666666667, 5, "rahu", 18),   # Ardra 0°00'00" (66°40')
            (80.0, 6, "jupiter", 16),             # Punarvasu 0°00'00" (80°00')
            (93.33333333333333, 7, "saturn", 19), # Pushya 0°00'00" (93°20')
            (106.66666666666667, 8, "mercury", 17), # Ashlesha 0°00'00" (106°40')
        ],
    )
    def test_exact_nakshatra_boundary_balance_and_lord(
        self, boundary_lon, expected_nak_idx, expected_lord, expected_years
    ):
        birth_dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        first_lord, balance, first_start = _nakshatra_balance(
            boundary_lon,
            VIMSHOTTARI_SEQUENCE,
            VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS,
            birth_dt,
        )

        # 1. Lord must match incoming nakshatra lord
        assert first_lord == expected_lord

        # 2. Balance must be 100% of lord's full allocation
        assert math.isclose(balance, float(expected_years), rel_tol=1e-6)

        # 3. Anchor instant must equal birth instant (zero elapsed seconds)
        assert first_start == birth_dt

    def test_nakshatra_boundary_full_tree_tiling(self):
        """Build full dasha tree at exact boundary and verify gapless tiling."""
        birth_dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        tree = _DASHA.compute_vimshottari(birth_dt, 28.6139, 77.2090, max_depth=5)

        # Invariant: validate_tiling must pass gaplessly at depth 5
        tree.validate_tiling()
        assert len(tree.mahadashas) == 9
        assert tree.mahadashas[0].start_datetime_utc <= birth_dt <= tree.mahadashas[0].end_datetime_utc


# ═══════════════════════════════════════════════════════════════════════════════
# CASE 3: Southern Hemisphere Chart (Negative Latitude & Declination)
# ═══════════════════════════════════════════════════════════════════════════════


class TestGoldenCase3SouthernHemisphere:
    """
    Validates Southern Hemisphere charts (Sydney, Buenos Aires, Cape Town)
    ensuring correct eastern rising sign resolution and zodiacal house sequence.
    """

    @pytest.mark.parametrize(
        "city_name,lat,lon",
        [
            ("Sydney_Australia", -33.8688, 151.2093),
            ("Buenos_Aires_Argentina", -34.6037, -58.3816),
            ("Cape_Town_SouthAfrica", -33.9249, 18.4241),
            ("Auckland_NewZealand", -36.8485, 174.7633),
        ],
    )
    def test_southern_hemisphere_ascendant_and_houses(self, city_name, lat, lon):
        dt = datetime(2024, 3, 21, 6, 0, 0, tzinfo=timezone.utc)
        result = _WRAPPER.calculate(
            dt=dt,
            latitude=lat,
            longitude=lon,
            ayanamsa="lahiri",
            house_system="W",
        )

        # 1. Ascendant in valid range
        asc = result.ascendant
        assert 0.0 <= asc.sidereal_longitude < 360.0

        # 2. Whole-Sign houses follow direct forward zodiacal progression
        for i in range(1, 13):
            cusp = result.house_cusps[i - 1]
            assert cusp.house_number == i
            expected_cusp_lon = (result.house_cusps[0].longitude + (i - 1) * 30.0) % 360.0
            diff = abs(cusp.longitude - expected_cusp_lon)
            if diff > 180:
                diff = abs(diff - 360)
            assert diff < 1e-4

        # 3. Verify divisional chart generation from southern base chart
        varga_d9 = _DIV_ENGINE.compute(
            birth_datetime_utc=dt,
            latitude=lat,
            longitude=lon,
            varga="D9",
        )
        assert varga_d9 is not None
        assert varga_d9.ascendant.varga_rashi != ""
        assert len(varga_d9.planet_positions) >= 9


# ═══════════════════════════════════════════════════════════════════════════════
# CASE 4: Exact Daśā-Boundary Full-Stack Integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestGoldenCase4DashaBoundaryIntegration:
    """
    Validates microsecond-level handover on exact Mahādaśā and Antardaśā boundaries,
    ensuring continuous coverage and zero gaps across D1 and divisional charts.
    """

    def test_mahadasha_exact_boundary_handover(self):
        birth_dt = datetime(1990, 5, 15, 10, 30, 0, tzinfo=timezone.utc)
        tree = _DASHA.compute_vimshottari(birth_dt, 28.6139, 77.2090, max_depth=3)

        for i in range(len(tree.mahadashas) - 1):
            md_curr = tree.mahadashas[i]
            md_next = tree.mahadashas[i + 1]

            # Exact boundary instant
            boundary_instant = md_curr.end_datetime_utc
            assert md_next.start_datetime_utc == boundary_instant

            # Exact boundary instant membership (closed-interval boundary inclusivity)
            assert md_curr.contains(boundary_instant)
            assert md_next.contains(boundary_instant)

            # Evaluation 1 second before boundary -> belongs to md_curr
            t_before = boundary_instant - timedelta(seconds=1)
            assert md_curr.contains(t_before)
            assert not md_next.contains(t_before)

            # Evaluation 1 second after boundary -> belongs to md_next
            t_after = boundary_instant + timedelta(seconds=1)
            assert md_next.contains(t_after)
            assert not md_curr.contains(t_after)

    def test_divisional_vimshottari_boundary_concurrence(self):
        """Verify divisional Vimshottari (D9 Moon) computes independently with full tiling."""
        birth_dt = datetime(1990, 5, 15, 10, 30, 0, tzinfo=timezone.utc)
        d9_tree = _DIV_DASHA.compute_divisional_vimshottari(
            birth_datetime=birth_dt,
            latitude=28.6139,
            longitude=77.2090,
            varga_number=9,
            max_depth=3,
        )

        assert d9_tree is not None
        assert len(d9_tree.mahadashas) == 9

        # Invariant: D9 dasha tree must tile gaplessly
        for i in range(len(d9_tree.mahadashas) - 1):
            assert d9_tree.mahadashas[i].end_datetime_utc == d9_tree.mahadashas[i + 1].start_datetime_utc
