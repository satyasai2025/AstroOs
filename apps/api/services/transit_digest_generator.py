"""
AstroOS — Personalized Transit Digest Generation Service
=========================================================
Synthesizes the user's Default Birth Chart (is_default == True), current
active Swiss Ephemeris transits, and canonical 27-Nakshatra deities/remedies
into a tailored, high-value email digest.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.data.nakshatra_remedies_catalogue import get_nakshatra_profile
from apps.api.models.astrology import BirthChartModel
from apps.api.models.user import UserModel
from apps.api.templates.transit_digest_email import render_transit_digest_html

# Classical 12-Rashi index mapping (1-based: Aries=1 ... Pisces=12)
RASHI_TO_INDEX: Dict[str, int] = {
    "aries": 1, "mesha": 1,
    "taurus": 2, "vrishabha": 2,
    "gemini": 3, "mithuna": 3,
    "cancer": 4, "karka": 4,
    "leo": 5, "simha": 5,
    "virgo": 6, "kanya": 6,
    "libra": 7, "tula": 7,
    "scorpio": 8, "vrischika": 8,
    "sagittarius": 9, "dhanu": 9,
    "capricorn": 10, "makara": 10,
    "aquarius": 11, "kumbha": 11,
    "pisces": 12, "meena": 12,
}

INDEX_TO_RASHI: Dict[int, str] = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
    5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
    9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
}

# House-specific dynamic predictive themes for Jupiter transiting Ashlesha/Cancer
HOUSE_TRANSIT_THEMES: Dict[int, str] = {
    1: (
        "Jupiter's transit through your 1st House (Lagna) brings profound personal expansion, self-awareness, "
        "and intellectual vitality. Hidden talents and clarity of purpose surface. It is a period to sharpen your "
        "strategy, adopt holistic health practices, and guide others with renewed intuitive confidence."
    ),
    2: (
        "Jupiter's transit through your 2nd House brings growth through financial strategy, refined speech, and deep "
        "family understanding. Hidden resources or ancestral insights may unlock. Focus on long-term wealth preservation "
        "and avoid impulsive or secretive investments."
    ),
    3: (
        "Jupiter's transit through your 3rd House stimulates courageous initiatives, deep writing, research communications, "
        "and sibling relationships. Your curiosity is heightened. Channel this into writing, teaching, or mastering a "
        "specialized technical or astrological skill."
    ),
    4: (
        "Jupiter's transit through your 4th House brings growth through deeper understanding rather than through obvious "
        "opportunities. Things that were hidden can come to light, unanswered questions may begin to make sense, and you may "
        "find yourself looking much more deeply at people, situations and even your own patterns. This can be an excellent "
        "period for research, learning, medicine and healing, astrology and other hidden sciences, strategy, financial planning "
        "and solving complicated emotional problems."
    ),
    5: (
        "Jupiter's transit through your 5th House creates a golden window for creative intellect, spiritual mantras, higher "
        "education, and children. Your analytical intuition becomes formidable. Focus on mastering sacred scriptures and "
        "discerning genuine creative inspiration from egoic distraction."
    ),
    6: (
        "Jupiter's transit through your 6th House brings resolution to lingering obstacles, health revitalization, and mastery "
        "over complex competitive challenges. You gain the ability to diagnose root causes of problems. Focus on daily routine, "
        "healing therapies, and resolving debts with prudent strategy."
    ),
    7: (
        "Jupiter's transit through your 7th House enhances partnership depth, strategic collaborations, and interpersonal insight. "
        "You begin seeing beneath the surface of contracts and relationships. Clear honest communication will transform alliances, "
        "while suspicious overthinking must be consciously released."
    ),
    8: (
        "Jupiter's transit through your 8th House opens a gateway for profound occult research, unearned wealth/inheritances, "
        "and transformative psychological healing. Taboo subjects or long-standing mysteries become clear. A supreme period for "
        "deep meditation, Kundalini work, and investigating hidden truths."
    ),
    9: (
        "Jupiter's transit through your 9th House brings immense spiritual fortune (Bhagya), higher philosophical illumination, "
        "and guidance from mentors/Gurus. Long-distance journeys or scholarly publications prosper. Trust your higher principles "
        "and embrace selfless dharma."
    ),
    10: (
        "Jupiter's transit through your 10th House elevates professional authority, strategic leadership, and career reputation. "
        "Complex career problems can now be resolved through insightful planning. Lead with moral integrity and share mentorship "
        "with junior colleagues."
    ),
    11: (
        "Jupiter's transit through your 11th House accelerates gains, expands influential networks, and fulfills cherished aspirations. "
        "Collaborative projects with research groups or scholars yield tangible rewards. Keep your focus on collective welfare rather "
        "than transient personal gains."
    ),
    12: (
        "Jupiter's transit through your 12th House facilitates spiritual liberation (Moksha), foreign connections, meditative retreat, "
        "and dissolving past karmic debts. Dreams and subconscious patterns yield deep revelations. Prioritize solitary reflection, "
        "charity, and restful sleep."
    ),
}


class TransitDigestGeneratorService:
    """Service to generate personalized transit email digests for registered & default-chart users."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_default_chart(self, user_id: uuid.UUID) -> Optional[BirthChartModel]:
        """Fetch the user's primary/default birth chart."""
        # 1. Look for explicit is_default == True
        stmt = (
            select(BirthChartModel)
            .where(BirthChartModel.user_id == user_id, BirthChartModel.is_default.is_(True))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        chart = result.scalar_one_or_none()
        if chart is not None:
            return chart

        # 2. Fallback to latest created chart
        fallback_stmt = (
            select(BirthChartModel)
            .where(BirthChartModel.user_id == user_id)
            .order_by(BirthChartModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(fallback_stmt)
        return result.scalar_one_or_none()

    async def generate_personalized_digest(
        self,
        *,
        user_id: Optional[uuid.UUID] = None,
        email: str,
        user_name: Optional[str] = None,
        target_planet: str = "Jupiter",
        transit_nakshatra: str = "Ashlesha",
        transit_rashi: str = "Cancer",
        transit_date_range: str = "August 18 to October 18, 2026",
        base_url: str = "https://astroos.internal",
        unsubscribe_url: str = "https://astroos.internal/settings/notifications",
    ) -> Dict[str, Any]:
        """
        Generate a fully personalized transit digest payload and rendered HTML.
        Automatically inherits the user's default birth chart.
        """
        resolved_name = user_name or "Valued Practitioner"
        lagna_rashi: Optional[str] = None
        house_number: Optional[int] = None

        if user_id:
            # 1. Fetch User Record
            user = await self._session.get(UserModel, user_id)
            if user and user.display_name:
                resolved_name = user.display_name

            # 2. Fetch User's Default Chart
            default_chart = await self.get_user_default_chart(user_id)
            if default_chart:
                if default_chart.subject_name and default_chart.subject_name != "Unnamed":
                    resolved_name = default_chart.subject_name

                if default_chart.lagna_rashi:
                    lagna_rashi = default_chart.lagna_rashi.capitalize()
                    lagna_idx = RASHI_TO_INDEX.get(default_chart.lagna_rashi.lower(), 1)
                    transit_idx = RASHI_TO_INDEX.get(transit_rashi.lower(), 4)
                    # House from Lagna: (transit_idx - lagna_idx) % 12 + 1
                    house_number = ((transit_idx - lagna_idx) % 12) + 1

        # Retrieve classical nakshatra profile
        nakshatra_profile = get_nakshatra_profile(transit_nakshatra)

        # Build prediction text
        if house_number and house_number in HOUSE_TRANSIT_THEMES:
            prediction_text = HOUSE_TRANSIT_THEMES[house_number]
        else:
            prediction_text = (
                f"{target_planet}'s transit through {transit_nakshatra} ({transit_rashi}) awakens deeper intuitive insights, "
                "strategic investigation, and spiritual discernment. Hidden connections surface and complex questions find clarity. "
                "Connect your default birth chart to receive house-exact predictions for your Lagna."
            )

        # Classical remedies mapping
        ruling_planet = nakshatra_profile.ruling_planet if nakshatra_profile else "Mercury"
        deity = nakshatra_profile.deity if nakshatra_profile else "Nagas"
        scripture_title = f"Read the {nakshatra_profile.associated_sage_or_scripture}" if nakshatra_profile else "Study Classical Shastras"
        scripture_text = (
            nakshatra_profile.scripture_recommendation
            if nakshatra_profile
            else "Study classical scriptures to harmonize mental clarity during this planetary transit."
        )
        mantra_sanskrit = nakshatra_profile.primary_mantra if nakshatra_profile else "ॐ अनन्ताय नमः"
        mantra_iast = nakshatra_profile.primary_mantra_iast if nakshatra_profile else "Om Anantaya Namah"
        mantra_instructions = f"Chant {mantra_iast} - {mantra_sanskrit} every day (11, 27, or 108 times) to stabilize energy and clear mental agitation."

        symbol_insight = (
            f"The symbol of {transit_nakshatra} is the {nakshatra_profile.symbol if nakshatra_profile else 'Sacred Symbol'}, "
            "an ancient archetype closely associated with deep intuition, kundalini vitality, and protective wisdom."
        )

        wisdom_warning = (
            f"{target_planet} expands whatever it touches, so {transit_nakshatra}'s powerful intuition and intelligence can "
            "become stronger—but so can its tendency to overthink, hold on, become suspicious or get entangled in situations "
            "unnecessarily. One of the biggest lessons of this transit is therefore to use your intelligence wisely, trust your "
            "intuition without becoming suspicious, and know what to hold on to and what it is finally time to release."
        )

        rashi_dignity = "exaltation sign" if transit_rashi.lower() in ("cancer", "karka") and target_planet.lower() == "jupiter" else "sidereal transit"

        # Render complete responsive HTML email
        html_content = render_transit_digest_html(
            user_name=resolved_name,
            planet=target_planet,
            nakshatra=transit_nakshatra,
            rashi=transit_rashi,
            rashi_dignity=rashi_dignity,
            date_range=transit_date_range,
            ruling_planet=ruling_planet,
            deity=deity,
            house_number=house_number,
            lagna_rashi=lagna_rashi,
            transit_prediction=prediction_text,
            scripture_title=scripture_title,
            scripture_text=scripture_text,
            primary_mantra_sanskrit=mantra_sanskrit,
            primary_mantra_iast=mantra_iast,
            mantra_instructions=mantra_instructions,
            symbol_insight=symbol_insight,
            wisdom_warning=wisdom_warning,
            base_url=base_url,
            unsubscribe_url=unsubscribe_url,
        )

        return {
            "recipient_email": email,
            "user_name": resolved_name,
            "is_personalized": house_number is not None,
            "lagna_rashi": lagna_rashi,
            "house_number": house_number,
            "planet": target_planet,
            "nakshatra": transit_nakshatra,
            "rashi": transit_rashi,
            "date_range": transit_date_range,
            "prediction": prediction_text,
            "remedies": {
                "scripture": scripture_text,
                "mantra_sanskrit": mantra_sanskrit,
                "mantra_iast": mantra_iast,
            },
            "html_email": html_content,
        }
