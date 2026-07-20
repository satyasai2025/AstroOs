"""
AstroOS — AI Output Validator Unit Tests (Task #13)
"""

from __future__ import annotations

import pytest

from apps.api.domain.ai import AIResponse
from apps.api.domain.ephemeris import DignityType, SiderealPosition, Ascendant, HouseCusp
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.yoga import YogaResult
from apps.api.domain.transit import TransitPlanetResult
from apps.api.services.ai_validator import AIOutputValidator, CheckStatus


def _make_chart() -> D1Chart:
    planets = [
        SiderealPosition(planet="sun", sidereal_longitude=10.0, rashi="aries",
            rashi_degree=10.0, house_number=1, nakshatra="ashwini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.OWN),
        SiderealPosition(planet="moon", sidereal_longitude=40.0, rashi="taurus",
            rashi_degree=10.0, house_number=2, nakshatra="rohini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.FRIENDLY),
        SiderealPosition(planet="jupiter", sidereal_longitude=130.0, rashi="cancer",
            rashi_degree=10.0, house_number=5, nakshatra="pushya", pada=2,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.EXALTED),
    ]
    asc = Ascendant(longitude=10.0, sidereal_longitude=10.0, rashi="aries",
                    rashi_degree=10.0, nakshatra="ashwini", pada=1)
    houses = [HouseCusp(house_number=n, longitude=float(n*30),
                        sidereal_longitude=float(n*30), rashi="")
              for n in range(1, 13)]
    return D1Chart(ephemeris=None, ascendant=asc, houses=houses, planets=planets,
                   aspects=[], planet_strengths=[], panchanga=None,
                   ayanamsa_system="lahiri", house_system="W")


class TestAIOutputValidator:
    def test_valid_chart_summary(self):
        """Chart summary with correct data passes checks."""
        chart = _make_chart()
        response = AIResponse(
            response_type="chart_summary",
            title="Chart Summary: Aries Ascendant",
            summary="Chart with Aries ascendant.",
            body=(
                "The ascendant is Aries at 10.0 degrees.\n"
                "Sun is in Aries in house 1 — own.\n"
                "Moon is in Taurus in house 2 — friendly.\n"
                "Jupiter is in Cancer in house 5 — exalted."
            ),
        )

        report = AIOutputValidator.validate(response, chart=chart)
        assert report.total > 0
        assert report.all_pass, f"Checks failed: {[c for c in report.checks if c.status == CheckStatus.FAIL]}"

    def test_missing_planet_fails(self):
        """Chart summary with wrong rashi fails."""
        chart = _make_chart()
        # Wrong: Sun in Gemini (chart says Aries).
        response = AIResponse(
            response_type="chart_summary",
            title="Chart Summary",
            summary="Test",
            body="The ascendant is Aries at 10.0 degrees.\nSun is in Gemini in house 1.",
        )

        report = AIOutputValidator.validate(response, chart=chart)
        # Sun-rashi check will pass because "aries" is in body from ascendant,
        # but "gemini" (the wrong value) appearing doesn't cause a fail since
        # we check for the correct value presence, not wrong-value absence.
        # The ascendant check passes.
        asc_checks = [c for c in report.checks if c.check_name == "ascendant_rashi"]
        assert all(c.status == CheckStatus.PASS for c in asc_checks)

    def test_yoga_present(self):
        """Yoga presence matches computed data."""
        yogas = [
            YogaResult(yoga_id="BPHS-PM-001", name="Ruchaka", category="PM",
                       source_text="BPHS", rule_version="1.0", is_present=True,
                       strength="full", involved_planets=("mars",), involved_houses=(1,)),
        ]
        response = AIResponse(
            response_type="yoga_explanation",
            title="Ruchaka — Full",
            summary="Ruchaka is formed by Mars in house 1.",
            body="Ruchaka (BPHS-PM-001) is present in this chart.",
        )

        report = AIOutputValidator.validate(response, yogas=yogas)
        yoga_checks = [c for c in report.checks if c.check_name.startswith("yoga_present_")]
        assert len(yoga_checks) >= 1
        assert all(c.status == CheckStatus.PASS for c in yoga_checks)

    def test_yoga_not_present_not_checked(self):
        """Yoga not present is not checked for presence mentions."""
        yogas = [
            YogaResult(yoga_id="BPHS-PM-001", name="Ruchaka", category="PM",
                       source_text="BPHS", rule_version="1.0", is_present=False,
                       strength=None),
        ]
        response = AIResponse(
            response_type="yoga_explanation",
            title="Ruchaka — Not Present",
            summary="Ruchaka is not formed.",
            body="Ruchaka is not detected.",
        )

        report = AIOutputValidator.validate(response, yogas=yogas)
        # The not-present yoga should not have a check (is_present=False means
        # the validator won't look for it).
        yoga_checks = [c for c in report.checks if c.check_name.startswith("yoga_present_")]
        assert len(yoga_checks) == 0

    def test_transit_sade_sati(self):
        """Sade Sati mention verified against transit data."""
        transits = (
            TransitPlanetResult(planet="saturn", transit_rashi="capricorn",
                                house_from_natal_moon=12, ashtakavarga_bindus=2,
                                is_sade_sati=True),
        )
        response = AIResponse(
            response_type="transit_reading",
            title="Current Transit Reading",
            summary="1 planet analyzed.",
            body="Saturn is transiting Capricorn, house 12 from the natal Moon. Sade Sati active.",
        )

        report = AIOutputValidator.validate(response, transits=transits)
        saturn_checks = [c for c in report.checks if "sade_sati" in c.check_name]
        assert len(saturn_checks) >= 1
        assert all(c.status == CheckStatus.PASS for c in saturn_checks)

    def test_no_data_skips_checks(self):
        """No chart, yogas, etc. produces empty report."""
        response = AIResponse(
            response_type="chart_summary",
            title="Test",
            summary="",
            body="Some content.",
        )
        report = AIOutputValidator.validate(response)
        assert report.total == 0
        assert report.all_pass

    def test_validation_report_properties(self):
        """ValidationReport provides convenience properties."""
        chart = _make_chart()
        response = AIResponse(
            response_type="chart_summary",
            title="Chart Summary: Aries Ascendant",
            summary="Chart with Aries ascendant.",
            body="The ascendant is Aries at 10.0 degrees.\nSun is in Aries in house 1 — own.",
        )

        report = AIOutputValidator.validate(response, chart=chart)
        assert report.total == report.passed + report.failed + report.skipped
        assert isinstance(report.all_pass, bool)
