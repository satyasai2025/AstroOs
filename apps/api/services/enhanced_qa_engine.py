"""
AstroOS — Enhanced QAResponder (Phase E)

Extends the Phase 1 QAResponder with knowledge of yogas, dashas,
transits, strengths, and shadbala. Answers natural language questions
using chart data across all computed domains.

All methods are static — no state.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from apps.api.domain.ai import AIResponse, Citation
from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.transit import TransitPlanetResult
from apps.api.domain.yoga import YogaResult


def _rashi_name(r: str) -> str:
    return r.capitalize()


def _planet_name(p: str) -> str:
    return p.capitalize()


def _dasha_level_name(level: int) -> str:
    names = ["Mahadasha", "Antardasha", "Pratyantar", "Sookshma", "Prana"]
    return names[level - 1] if 1 <= level <= len(names) else f"Level {level}"


class EnhancedQAResponder:
    """Answers natural language questions using full chart context."""

    @staticmethod
    def generate(
        question: str,
        chart: Optional[D1Chart] = None,
        yogas: Optional[list[YogaResult]] = None,
        dasha_tree: Optional[DashaTree] = None,
        transits: Optional[list[TransitPlanetResult]] = None,
        shadbala_totals: Optional[dict[str, float]] = None,
    ) -> AIResponse:
        """Answer a question with full chart context across all domains."""
        q = question.lower().strip()

        # ── Route to the right handler based on question content ──────────
        if chart is None:
            body = "Chart data is required to answer this question."

        elif "dasha" in q or ("mahadasha" in q) or ("period" in q and any(
            p in q for p in ["current", "active", "now", "running", "today"]
        )):
            body = EnhancedQAResponder._answer_dasha(q, dasha_tree, chart)

        elif "transit" in q or "gochar" in q or "sade sati" in q or "ashtama shani" in q:
            body = EnhancedQAResponder._answer_transit(q, transits, chart)

        elif "yoga" in q or any(y in q for y in ["raja", "dhana", "gajakesari", "panch mahapurusha"]):
            body = EnhancedQAResponder._answer_yoga(q, yogas, chart)

        elif "shadbala" in q or "strength" in q or "strong" in q or "bala" in q or "rupa" in q:
            body = EnhancedQAResponder._answer_strength(q, shadbala_totals, chart)

        elif "retrograde" in q or "vakri" in q:
            body = EnhancedQAResponder._answer_retrograde(q, chart)

        elif "combust" in q or "astang" in q:
            body = EnhancedQAResponder._answer_combustion(q, chart)

        elif "aspect" in q or "drishti" in q or "see" in q:
            body = EnhancedQAResponder._answer_aspects(q, chart)

        elif "house" in q or "bhava" in q:
            body = EnhancedQAResponder._answer_house(q, chart)

        elif "dignit" in q or "exalted" in q or "debilitated" in q or "neecha" in q:
            body = EnhancedQAResponder._answer_dignity(q, chart)

        elif "ascendant" in q or "lagna" in q:
            body = EnhancedQAResponder._answer_ascendant(q, chart)

        elif "planet" in q or any(p in q for p in ["sun", "moon", "mars", "mercury", "jupiter",
                                                     "venus", "saturn", "rahu", "ketu",
                                                     "surya", "chandra", "mangal", "budha",
                                                     "guru", "shukra", "shani"]):
            body = EnhancedQAResponder._answer_planet(q, chart)

        elif "pada" in q or "nakshatra" in q:
            body = EnhancedQAResponder._answer_nakshatra(q, chart)

        elif "varga" in q or "divisional" in q or "navamsha" in q or "d9" in q:
            body = (
                "Varga (divisional chart) information is available through the "
                "Analysis page's Vargas tab. I can tell you about a specific "
                "planet's D1 placement — ask about any planet for its rashi, "
                "house, and dignity."
            )

        elif "conflict" in q or "disagreement" in q or "debate" in q or "controversy" in q:
            body = (
                "Doctrinal conflicts are documented in the Knowledge section. "
                "Use the Research Assistant to ask about specific disagreements "
                "between traditions — it searches the knowledge base and returns "
                "structured answers with classical references."
            )

        elif "about" in q:
            # "Tell me about <X>" where X didn't match any known topic above
            # (e.g. an unrecognized planet name) — _answer_planet already has
            # a well-formed "which planet did you mean" fallback for this.
            body = EnhancedQAResponder._answer_planet(q, chart)

        else:
            body = (
                "I can answer questions about: ascendant/lagna, specific planets "
                "(Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu), "
                "yogas (Raja, Dhana, Gajakesari, Panch Mahapurusha, Neecha Bhanga), "
                "dasha periods (current Mahadasha, Antardasha), transits (Sade Sati, "
                "Ashtama Shani), planetary strength (Shadbala), dignity states "
                "(exaltation, debilitation, own sign), retrograde planets, combustion, "
                "aspects, houses (bhavas), and nakshatras. "
                "Please ask a more specific question from these topics."
            )

        # Determine confidence based on available context.
        confidence = "high"
        if chart is None:
            confidence = "low"

        return AIResponse(
            response_type="qa_answer",
            title=f"Q: {question[:80]}{'...' if len(question) > 80 else ''}",
            summary=body[:200] if len(body) > 200 else body,
            body=body,
            sources=("chart_engine",),
            confidence=confidence,
            version="2.0",
        )

    @staticmethod
    def _answer_dasha(
        q: str, dasha_tree: Optional[DashaTree], chart: D1Chart,
    ) -> str:
        """Answer questions about dasha periods."""
        if dasha_tree is None:
            return "Dasha data was not computed for this chart."

        # Find all active periods (current date).
        today = date.today()
        active_periods: list[DashaPeriod] = []
        stack = list(dasha_tree.mahadashas)
        while stack:
            period = stack.pop(0)
            if period.start_date <= today <= period.end_date:
                active_periods.append(period)
                stack = list(period.sub_periods)
            else:
                stack.extend(period.sub_periods)

        if not active_periods:
            return "No active dasha period found for today's date."

        md = active_periods[0]
        body_lines = [
            f"The current {dasha_tree.system} period is:",
            f"  • {_dasha_level_name(md.level)}: {_planet_name(md.lord)} — "
            f"{md.start_date} to {md.end_date}",
        ]

        if len(active_periods) > 1:
            for ap in active_periods[1:]:
                body_lines.append(
                    f"  • {_dasha_level_name(ap.level)}: {_planet_name(ap.lord)} — "
                    f"{ap.start_date} to {ap.end_date}"
                )

        # Add lord's placement from chart.
        lord = next((p for p in chart.planets if p.planet == md.lord), None)
        if lord:
            dignity = lord.dignity.value if lord.dignity else "neutral"
            retro = " (retrograde)" if lord.is_retrograde else ""
            body_lines.append(
                f"\n{_planet_name(md.lord)} is placed in {_rashi_name(lord.rashi)} "
                f"in house {lord.house_number} — {dignity}{retro}."
            )

        return "\n".join(body_lines)

    @staticmethod
    def _answer_transit(
        q: str, transits: Optional[list[TransitPlanetResult]], chart: D1Chart,
    ) -> str:
        """Answer questions about transits."""
        if not transits:
            return "Transit data was not computed for this request."

        lines: list[str] = []
        for t in transits:
            parts = [
                f"{_planet_name(t.planet)} is transiting {_rashi_name(t.transit_rashi)}, "
                f"house {t.house_from_natal_moon} from the natal Moon."
            ]
            if t.is_sade_sati:
                parts.append(" ⚠️ Sade Sati is active.")
            if t.is_ashtama_shani:
                parts.append(" ⚠️ Ashtama Shani is active.")
            if t.has_vedha:
                parts.append(f" ⚠️ Vedha from {t.vedha_planet}.")
            lines.append("".join(parts))

        return "\n".join(lines)

    @staticmethod
    def _answer_yoga(
        q: str, yogas: Optional[list[YogaResult]], chart: D1Chart,
    ) -> str:
        """Answer questions about yogas."""
        if not yogas:
            return "Yoga data was not computed for this chart."

        present = [y for y in yogas if y.is_present]
        if not present:
            body = "No classical yogas are formed in this chart.\n\n"
            body += "Specific yogas can be evaluated on the Yogas tab."
            return body

        body_lines: list[str] = []
        for y in present[:5]:
            body_lines.append(
                f"• {y.name} ({y.category}) — "
                f"{y.strength or 'present'}"
            )
            if y.involved_planets:
                body_lines[-1] += f" — planets: {', '.join(_planet_name(p) for p in y.involved_planets)}"
            if y.involved_houses:
                body_lines[-1] += f" — houses: {', '.join(str(h) for h in y.involved_houses)}"

        body = f"Found {len(present)} present yoga{'s' if len(present) != 1 else ''}:\n"
        body += "\n".join(body_lines)

        if len(present) > 5:
            body += f"\n\n...and {len(present) - 5} more (see the Yogas tab for full list)."

        return body

    @staticmethod
    def _answer_strength(
        q: str, shadbala_totals: Optional[dict[str, float]], chart: D1Chart,
    ) -> str:
        """Answer questions about planetary strength."""
        if not shadbala_totals:
            return "Shadbala strength data was not computed for this chart."

        lines: list[str] = ["Planetary strength (Shadbala totals in Rupas):"]
        for planet in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
            rupas = shadbala_totals.get(planet, 0.0)
            indicator = "✅ Strong" if rupas >= 5.0 else "⚠️ Moderate" if rupas >= 3.0 else "❌ Weak"
            lines.append(f"  • {_planet_name(planet)}: {rupas:.2f} Rupas — {indicator}")

        lines.append("\nClassical required bala (minimum strength): 5.0 Rupas per planet.")
        return "\n".join(lines)

    @staticmethod
    def _answer_retrograde(q: str, chart: D1Chart) -> str:
        """Answer questions about retrograde planets."""
        retrogrades = [p for p in chart.planets if p.is_retrograde]
        if retrogrades:
            names = ", ".join(_planet_name(p.planet) for p in retrogrades)
            lines = [f"Retrograde planets: {names}."]
            for p in retrogrades:
                lines.append(
                    f"  • {_planet_name(p.planet)} in {_rashi_name(p.rashi)} "
                    f"house {p.house_number}"
                )
            lines.append("\nRetrograde planets are not inherently negative — they indicate "
                        "inward-focused or re-evaluative expression of that planet's energies.")
            return "\n".join(lines)
        return "No planets are retrograde in this chart. All planets are moving direct."

    @staticmethod
    def _answer_combustion(q: str, chart: D1Chart) -> str:
        """Answer questions about combust planets."""
        combust = [p for p in chart.planets if p.is_combust]
        if combust:
            names = ", ".join(_planet_name(p.planet) for p in combust)
            lines = [f"Combust planets: {names}."]
            for p in combust:
                lines.append(
                    f"  • {_planet_name(p.planet)} — orb: {p.combustion_orb:.1f}° from Sun"
                )
            lines.append("\nCombustion weakens a planet's independent expression as it is "
                        "overshadowed by the Sun's light.")
            return "\n".join(lines)
        return "No planets are combust in this chart."

    @staticmethod
    def _answer_aspects(q: str, chart: D1Chart) -> str:
        """Answer questions about planetary aspects."""
        if not chart.aspects:
            return "No aspect data available for this chart."

        # Find aspects involving the most mentioned planet.
        lines: list[str] = []
        for a in chart.aspects[:8]:
            applying = " (applying)" if a.is_applying else ""
            lines.append(
                f"• {_planet_name(a.from_planet)} → {_planet_name(a.to_planet)}: "
                f"{a.aspect_type} (orb: {a.orb_degrees:.1f}°){applying}"
            )

        if len(chart.aspects) > 8:
            lines.append(f"...and {len(chart.aspects) - 8} more aspects.")

        body = f"Found {len(chart.aspects)} aspects:\n"
        body += "\n".join(lines)
        return body

    @staticmethod
    def _answer_house(q: str, chart: D1Chart) -> str:
        """Answer questions about house placements."""
        # Try to extract a specific house number from the question.
        import re
        house_match = re.search(r'\b(1[0-2]|[1-9])\b', q)
        if house_match:
            h = int(house_match.group(0))
            planets = [p for p in chart.planets if p.house_number == h]
            if planets:
                names = ", ".join(_planet_name(p.planet) for p in planets)
                return f"House {h} contains: {names}."
            return f"House {h} is empty of classical planets."

        # General house overview.
        lines: list[str] = []
        for h in range(1, 13):
            planets = [p for p in chart.planets if p.house_number == h]
            if planets:
                names = ", ".join(_planet_name(p.planet) for p in planets)
                lines.append(f"• House {h}: {names}")
        if lines:
            body = "Planetary distribution by house:\n"
            body += "\n".join(lines)
            return body
        return "House placement data is available in the Chart tab."

    @staticmethod
    def _answer_dignity(q: str, chart: D1Chart) -> str:
        """Answer questions about planetary dignity states."""
        lines: list[str] = []
        for p in chart.planets:
            dignity = p.dignity.value if p.dignity else "neutral"
            if dignity not in ("neutral", "friendly", "benefic"):
                indicator = {
                    "exalted": "⭐ Exalted (highest dignity)",
                    "own": "✅ Own sign",
                    "moolatrikona": "✅ Moolatrikona",
                    "debilitated": "❌ Debilitated (weakest dignity)",
                    "enemy": "⚠️ Enemy sign",
                }.get(dignity, dignity)
                lines.append(f"  • {_planet_name(p.planet)} in {_rashi_name(p.rashi)}: {indicator}")

        if not lines:
            return "No strongly dignified or debilitated planets in this chart."

        body = "Planetary dignity highlights:\n"
        body += "\n".join(lines)
        body += "\n\nFull dignity details are available in the Chart tab."
        return body

    @staticmethod
    def _answer_ascendant(q: str, chart: D1Chart) -> str:
        """Answer questions about the ascendant."""
        asc = chart.ascendant
        if asc is None:
            return "Ascendant data is not available for this chart."
        return (
            f"The ascendant (lagna) is {_rashi_name(asc.rashi)} "
            f"at {asc.rashi_degree:.1f}° (nakshatra: {asc.nakshatra}, pada: {asc.pada})."
        )

    @staticmethod
    def _answer_planet(q: str, chart: D1Chart) -> str:
        """Answer questions about a specific planet."""
        # Find which planet is being asked about.
        planet_names = {
            "sun": "sun", "surya": "sun",
            "moon": "moon", "chandra": "moon",
            "mars": "mars", "mangal": "mars", "mangala": "mars",
            "mercury": "mercury", "budha": "mercury",
            "jupiter": "jupiter", "guru": "jupiter", "brihaspati": "jupiter",
            "venus": "venus", "shukra": "venus",
            "saturn": "saturn", "shani": "saturn",
            "rahu": "rahu",
            "ketu": "ketu",
        }
        found_planet = None
        for name, canonical in planet_names.items():
            if name in q:
                found_planet = canonical
                break

        if not found_planet:
            body = "Which planet would you like to know about? You can ask about Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, or Ketu."
            return body

        planet_data = next((p for p in chart.planets if p.planet == found_planet), None)
        if planet_data is None:
            return f"{_planet_name(found_planet)} position data is not available."

        dignity = planet_data.dignity.value if planet_data.dignity else "neutral"
        retro = " (retrograde)" if planet_data.is_retrograde else ""
        combust = " (combust)" if planet_data.is_combust else ""

        return (
            f"{_planet_name(found_planet)} is in {_rashi_name(planet_data.rashi)} "
            f"at {planet_data.rashi_degree:.1f}°, house {planet_data.house_number}. "
            f"Dignity: {dignity}. "
            f"Nakshatra: {planet_data.nakshatra}, pada {planet_data.pada}.{retro}{combust}"
        )

    @staticmethod
    def _answer_nakshatra(q: str, chart: D1Chart) -> str:
        """Answer questions about nakshatras."""
        # Find nakshatra-related query.
        import re
        nakshatra_match = re.search(
            r'\b(ashwini|bharani|krittika|rohini|mrigashira|ardra|punarvasu|pushya|ashlesha|'
            r'magha|purva phalguni|uttara phalguni|hasta|chitra|swati|vishakha|anuradua|'
            r'jyeshtha|mula|purva ashadha|uttara ashadha|shravana|dhanishta|shatabhisha|'
            r'purva bhadrapada|uttara bhadrapada|revati)\b', q, re.IGNORECASE
        )
        if nakshatra_match:
            target = nakshatra_match.group(1).lower()
            planets_in = [
                p for p in chart.planets
                if p.nakshatra and target in p.nakshatra.lower()
            ]
            if planets_in:
                names = ", ".join(_planet_name(p.planet) for p in planets_in)
                return (f"Planets in {target.capitalize()} nakshatra: {names}.")
            return f"No classical planets are in {target.capitalize()} nakshatra."

        # General nakshatra overview.
        lines: list[str] = []
        for p in chart.planets:
            if p.nakshatra:
                lines.append(
                    f"  • {_planet_name(p.planet)}: {p.nakshatra.capitalize()} (pada {p.pada})"
                )
        body = "Planetary nakshatra positions:\n"
        body += "\n".join(lines)
        return body