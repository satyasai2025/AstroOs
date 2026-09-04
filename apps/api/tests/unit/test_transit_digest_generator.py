"""
Unit Tests for AstroOS Personalized Transit Digest Generator
============================================================
Tests canonical Nakshatra remedy retrieval, house-exact transit calculations
from the user's Default Birth Chart, and responsive HTML email rendering.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest

from apps.api.data.nakshatra_remedies_catalogue import get_nakshatra_profile, NAKSHATRA_CATALOGUE
from apps.api.models.astrology import BirthChartModel
from apps.api.models.user import UserModel
from apps.api.services.transit_digest_generator import TransitDigestGeneratorService


def test_nakshatra_catalogue_completeness_and_ashlesha():
    """Verify that all 27 nakshatras are present and Ashlesha has authentic classical remedies."""
    assert len(NAKSHATRA_CATALOGUE) == 27

    ashlesha = get_nakshatra_profile("Ashlesha")
    assert ashlesha is not None
    assert ashlesha.name == "Ashlesha"
    assert ashlesha.ruling_planet == "Mercury"
    assert "Nagas" in ashlesha.deity
    assert "Patanjali" in ashlesha.associated_sage_or_scripture
    assert "ॐ अनन्ताय नमः" in ashlesha.primary_mantra
    assert "Om Anantaya Namah" in ashlesha.primary_mantra_iast


@pytest.mark.asyncio
async def test_personalized_digest_for_default_chart_meena():
    """Verify that a user with a default Aries Lagna chart receives 4th house Ashlesha transit guidance."""
    user_id = uuid.uuid4()
    mock_session = AsyncMock()

    # Mock user Meena
    mock_user = MagicMock(spec=UserModel)
    mock_user.id = user_id
    mock_user.display_name = "Meena"
    mock_session.get.return_value = mock_user

    # Mock default birth chart (Aries Lagna)
    mock_chart = MagicMock(spec=BirthChartModel)
    mock_chart.id = uuid.uuid4()
    mock_chart.user_id = user_id
    mock_chart.subject_name = "Meena"
    mock_chart.lagna_rashi = "mesha"  # Aries
    mock_chart.is_default = True

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_chart
    mock_session.execute.return_value = mock_result

    service = TransitDigestGeneratorService(mock_session)
    digest = await service.generate_personalized_digest(
        user_id=user_id,
        email="meena@example.com",
        user_name="Meena",
        target_planet="Jupiter",
        transit_nakshatra="Ashlesha",
        transit_rashi="Cancer",
        transit_date_range="August 18 to October 18, 2026",
    )

    assert digest["is_personalized"] is True
    assert digest["user_name"] == "Meena"
    assert digest["lagna_rashi"] == "Mesha"
    assert digest["house_number"] == 4  # Aries (1) to Cancer (4) = 4th House
    assert "4th House" in digest["prediction"] or "deeper understanding" in digest["prediction"]
    assert "astrology and other hidden sciences" in digest["prediction"]
    assert "ॐ अनन्ताय नमः" in digest["remedies"]["mantra_sanskrit"]
    assert "Patanjali Yoga Sutras" in digest["remedies"]["scripture"]

    # Check HTML email content
    html = digest["html_email"]
    assert "Dear Meena," in html
    assert "Jupiter in your 4th House" in html
    assert "Ashlesha Nakshatra" in html
    assert "Patanjali Yoga Sutras" in html
    assert "ॐ अनन्ताय नमः" in html
    assert "The AstroOS Research Team" in html
    assert "unsubscribe" in html


@pytest.mark.asyncio
async def test_fallback_digest_for_anonymous_subscriber():
    """Verify that an anonymous subscriber without a birth chart receives general transit guidance."""
    mock_session = AsyncMock()

    service = TransitDigestGeneratorService(mock_session)
    digest = await service.generate_personalized_digest(
        user_id=None,
        email="visitor@example.com",
        user_name=None,
        target_planet="Jupiter",
        transit_nakshatra="Ashlesha",
        transit_rashi="Cancer",
    )

    assert digest["is_personalized"] is False
    assert digest["house_number"] is None
    assert "Connect your default birth chart" in digest["prediction"]
    assert "Dear Valued Practitioner," in digest["html_email"]
    assert "Ashlesha Nakshatra" in digest["html_email"]
