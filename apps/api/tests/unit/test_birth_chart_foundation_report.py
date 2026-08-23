"""
Unit tests for AstroOS Birth Chart Foundation Report Builder and SVG Renderer.
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.birth_chart_report_builder import BirthChartReportBuilder
from apps.api.services.chart_svg_renderer import render_north_indian_svg
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.report_template_engine import ReportTemplateEngine


def test_north_indian_svg_rendering():
    """Verify SVG renderer produces well-formed SVG with houses and planets."""
    svg = render_north_indian_svg(
        ascendant_rashi_num=3,  # Gemini
        planets_in_houses={
            1: ["As"],
            7: ["Sun", "Moon", "Mercury"],
            3: ["Mars"],
            5: ["Jupiter", "Venus", "Rahu"],
            9: ["Saturn"],
            11: ["Ketu"]
        },
        chart_title="D1 Rasi",
    )
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Su Mo Me" in svg or "Su" in svg
    assert "Ma" in svg


def test_birth_chart_report_builder_and_template():
    """Verify end-to-end foundation report compilation and HTML rendering."""
    wrapper = EphemerisWrapper("data/ephemeris")
    horoscope_engine = HoroscopeEngine(wrapper)

    
    # 1995-01-01 12:00:00 UTC at New Delhi
    birth_dt = datetime(1995, 1, 1, 12, 0, tzinfo=timezone.utc)
    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=birth_dt,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="P",
    )

    builder = BirthChartReportBuilder(wrapper)
    report_data = builder.build_report_data(
        chart=chart,
        subject_name="Arjun Sharma (Demo Chart)",
        birth_datetime_utc=birth_dt,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa_name="Lahiri",
        house_system_code="P",
    )

    # Assert basic data structure
    assert report_data["subject_name"] == "Arjun Sharma (Demo Chart)"
    assert "panchanga" in report_data
    assert "planets" in report_data
    assert len(report_data["planets"]) >= 10
    assert "d1_svg" in report_data
    assert "d9_svg" in report_data
    assert "dasha_timeline" in report_data
    assert len(report_data["dasha_timeline"]) == 9
    assert "sav_data" in report_data
    assert "avasthas" in report_data

    # Render through Jinja2 HTML template
    html = ReportTemplateEngine.render_html(report_data, template_name="birth_chart.html")
    assert "<!DOCTYPE html>" in html
    assert "ASTRO" in html
    assert "Arjun Sharma" in html
    assert "Vimshottari Dasha" in html
    assert "<svg" in html
    assert "Sarvashtakavarga (SAV)" in html


