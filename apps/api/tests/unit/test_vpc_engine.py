"""Tests for VPC (Varsha Pravesha Chakra / Solar Return) Engine."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.api.services.vpc_engine import VPCEngine, _normalize_deg, _angular_diff, SCDEntryMilestone, VPCReport


class TestVPCEngineHelpers:
    """Test VPC engine helper functions."""

    def test_normalize_deg_positive(self):
        """Test normalization of positive degrees."""
        assert _normalize_deg(90.0) == 90.0
        assert _normalize_deg(360.0) == 0.0
        assert _normalize_deg(450.0) == 90.0

    def test_normalize_deg_negative(self):
        """Test normalization of negative degrees."""
        assert _normalize_deg(-90.0) == 270.0
        assert _normalize_deg(-360.0) == 0.0

    def test_angular_diff_basic(self):
        """Test angular difference calculation."""
        assert _angular_diff(0.0, 0.0) == 0.0
        assert _angular_diff(10.0, 0.0) == 10.0
        assert _angular_diff(0.0, 10.0) == -10.0

    def test_angular_diff_wrap_around(self):
        """Test angular difference wraps correctly."""
        assert _angular_diff(350.0, 10.0) == -20.0
        assert _angular_diff(10.0, 350.0) == 20.0

    def test_angular_diff_bounds(self):
        """Test angular difference is always in [-180, 180]."""
        for a in range(0, 360, 15):
            for b in range(0, 360, 15):
                diff = _angular_diff(float(a), float(b))
                assert -180.0 <= diff <= 180.0


class TestVPCEngineInitialization:
    """Test VPC engine initialization."""

    def test_engine_initialization(self):
        """Test VPCEngine can be initialized."""
        engine = VPCEngine()
        assert engine is not None
        assert engine.wrapper is not None
        assert engine.bhava_engine is not None
        assert engine.sc_engine is not None

    def test_engine_with_wrapper(self):
        """Test VPCEngine with custom ephemeris wrapper."""
        from apps.api.services.ephemeris_wrapper import EphemerisWrapper
        wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
        engine = VPCEngine(ephemeris_wrapper=wrapper)
        assert engine.wrapper is wrapper


class TestVPCEngineComputations:
    """Test full 3-tier Sudarshana Pravesha (VPC, Monthly, Pratyantara) computations."""

    @pytest.fixture
    def vpc_engine(self):
        return VPCEngine()

    def test_compute_scd_house_progression(self, vpc_engine):
        """Test SCD house progression: Year 1 = House 1, Year 2 = House 2, Year 13 = House 1."""
        birth_dt = datetime(1985, 5, 15, 3, 0, 0, tzinfo=timezone.utc)

        # Age 0 (Year 1)
        h1 = vpc_engine.compute_scd_house_at_date(birth_dt, datetime(1985, 6, 1, tzinfo=timezone.utc))
        assert h1 == 1

        # Age 1 (Year 2)
        h2 = vpc_engine.compute_scd_house_at_date(birth_dt, datetime(1986, 6, 1, tzinfo=timezone.utc))
        assert h2 == 2

        # Age 11 (Year 12)
        h12 = vpc_engine.compute_scd_house_at_date(birth_dt, datetime(1996, 6, 1, tzinfo=timezone.utc))
        assert h12 == 12

        # Age 12 (Year 13, Cycle 2 start)
        h13 = vpc_engine.compute_scd_house_at_date(birth_dt, datetime(1997, 6, 1, tzinfo=timezone.utc))
        assert h13 == 1

    def test_compute_vpc_full_report(self, vpc_engine):
        """Test full Varsha Pravesha Chakra generation for benchmark native."""
        birth_dt = datetime(1985, 5, 15, 3, 0, 0, tzinfo=timezone.utc)
        target_year = 2026
        lat = 28.6139
        lon = 77.2090

        report = vpc_engine.compute_vpc(
            birth_datetime_utc=birth_dt,
            target_year=target_year,
            latitude=lat,
            longitude=lon,
            current_dasha_lords=["Jupiter", "Saturn", "Mercury", "Venus", "Mars"],
            ayanamsa="lahiri",
        )

        assert isinstance(report, VPCReport)
        assert report.target_year == 2026
        assert report.completed_years == 41
        # 41 completed years -> (41 % 12) + 1 = 5 + 1 = 6 (House 6 active)
        assert report.scd_annual_house == 6

        # Check Solar Return timestamp is in May 2026
        assert report.vpc_datetime_utc.year == 2026
        assert report.vpc_datetime_utc.month == 5
        assert 14 <= report.vpc_datetime_utc.day <= 16

        # Check 12 Monthly SCD entries
        assert len(report.monthly_scd_entries) == 12
        for i, m in enumerate(report.monthly_scd_entries):
            assert m.level == 2
            expected_house = ((report.scd_annual_house - 1 + i) % 12) + 1
            assert m.scd_house == expected_house

        # Verify chronological ordering of monthly entries
        for i in range(1, 12):
            prev_dt = report.monthly_scd_entries[i - 1].entry_datetime_utc
            curr_dt = report.monthly_scd_entries[i].entry_datetime_utc
            assert curr_dt > prev_dt

        # Check Pratyantara (Vidashaa) entries
        assert len(report.pratyantara_entries) == 12
        for p in report.pratyantara_entries:
            assert p.level == 3

        # Check VPC chart and Sudarshana Chakra
        assert report.vpc_chart is not None
        assert report.vpc_sudarshana is not None
        assert len(report.dasha_lord_vpc_strengths) == 5

