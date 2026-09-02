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
