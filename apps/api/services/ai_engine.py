"""
AstroOS — AI Engine (Module 24, Phase 1)

Template-based natural language generation from existing domain objects.
8 generators consuming all completed modules. No external LLM, no
network calls, no astrology calculations.

Calculator Integration Pattern (Task #13):
  AI services that need computed astrological values should call into
  the corresponding calculator engine directly:

  +-------------------+------------------------------------------+
  | Calculator        | Service class                            |
  +-------------------+------------------------------------------+
  | Shadbala (6 balas)| ShadbalaEngine                           |
  | Ashtakavarga      | AshtakavargaEngine                       |
  | Yoga detection    | YogaEngine                               |
  | Dasha computation | DashaEngine                              |
  | Transit positions | TransitEngine                            |
  | Horoscope/D1 chart| HoroscopeEngine                          |
  | Divisional charts | DivisionalEngine                         |
  +-------------------+------------------------------------------+

  WorkerPool ranges (for thread/process isolation):
    - ``WorkerPool.calculator`` (range 0-999) — planetary calculators
    - ``WorkerPool.ai``        (range 1000-1999) — AI/nlg generators

  Fallback chain (see apps/api/services/ai_fallback.py):
    Try AI generator ➜ low-confidence/empty ➜ fallback to rule-based
    calculator (ShadbalaEngine, YogaEngine, etc.) ➜ still fails ➜
    return structural error.

  All generators in this module are deterministic — they produce the
  same output for the same domain objects, every time.
"""

from __future__ import annotations

import dataclasses
import uuid
from typing import Any, Optional

from apps.api.config import get_settings
from apps.api.domain.ai import AIResponse, Citation, ExplanationRequest
from apps.api.services.local_llm_client import enrich_narration
from apps.api.domain.dasha import DashaPeriod
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.yoga import YogaResult
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.domain.ashtakavarga import SarvashtakavargaResult
from apps.api.domain.transit import TransitPlanetResult
from apps.api.domain.events import EventRecord
from apps.api.domain.timeline import Timeline
from apps.api.domain.verification import VerificationFindings
from apps.api.domain.statistics import AggregateReport

from packages.shared.enums import Rashi

_ENGINE_VERSION = "1.0"
_RASHI_NAMES = [r.value for r in Rashi]


def _planet_name(p: str) -> str:
    return p.capitalize()


def _rashi_name(r: str) -> str:
    return r.capitalize()


def _confidence_from_verification(vf: Optional[VerificationFindings]) -> str:
    if vf is None or vf.total_pairs == 0:
        return "medium"
    confirmed = sum(
        1 for p in vf.verification_pairs
        if p.alignment.value == "confirmed"
    )
    ratio = confirmed / vf.total_pairs
    if ratio >= 0.7:
        return "high"
    elif ratio >= 0.3:
        return "medium"
    return "low"


# ═══════════════════════════════════════════════════════════════════════════════
# Chart Summarizer
# ═══════════════════════════════════════════════════════════════════════════════


class ChartSummarizer:
    """Natural language overview of a D1Chart."""

    @staticmethod
    def generate(
        chart: D1Chart,
        style: str = "concise",
        verification: Optional[VerificationFindings] = None,
    ) -> AIResponse:
        asc = chart.ascendant
        asc_rashi = _rashi_name(asc.rashi) if asc else "Unknown"
        asc_degree = asc.rashi_degree if asc else 0

        # Build planet table summary in body.
        lines = [f"The ascendant is {asc_rashi} at {asc_degree:.1f} degrees."]
        for p in chart.planets:
            dignity = p.dignity.value if p.dignity else "neutral"
            retro = " (retrograde)" if p.is_retrograde else ""
            lines.append(
                f"{_planet_name(p.planet)} is in {_rashi_name(p.rashi)} "
                f"in house {p.house_number} — {dignity}{retro}."
            )

        body = "\n".join(lines)
        summary = f"Chart with {asc_rashi} ascendant and {len(chart.planets)} planets."

        return AIResponse(
            response_type="chart_summary",
            title=f"Chart Summary: {asc_rashi} Ascendant",
            summary=summary,
            body=body,
            sources=("chart_engine", "graha_engine"),
            confidence=_confidence_from_verification(verification),
            version=_ENGINE_VERSION,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Yoga Explainer
# ═══════════════════════════════════════════════════════════════════════════════


class YogaExplainer:
    """Explains detected yogas with classical references."""

    @staticmethod
    def generate(
        yoga: YogaResult,
        karakatvas: tuple = (),
        citations: tuple[Citation, ...] = (),
    ) -> AIResponse:
        if not yoga.is_present:
            return AIResponse(
                response_type="yoga_explanation",
                title=f"{yoga.name} — Not Present",
                summary=f"{yoga.name} is not formed in this chart.",
                body=f"{yoga.name} ({yoga.yoga_id}) is not detected. "
                     f"Required conditions were not met: {', '.join(yoga.missing) if yoga.missing else 'none fulfilled'}.",
                sources=("yoga_engine",),
                version=_ENGINE_VERSION,
            )

        planets_str = ", ".join(_planet_name(p) for p in yoga.involved_planets)
        houses_str = ", ".join(str(h) for h in yoga.involved_houses)
        strength_desc = yoga.strength or "present"

        body = (
            f"{yoga.name} ({yoga.yoga_id}) is present in this chart. "
            f"Strength: {strength_desc}. "
            f"Involved planets: {planets_str}. "
            f"Involved houses: {houses_str}."
        )

        return AIResponse(
            response_type="yoga_explanation",
            title=f"{yoga.name} — {strength_desc.capitalize()}",
            summary=f"{yoga.name} is formed by {planets_str} in house{'s' if len(yoga.involved_houses) != 1 else ''} {houses_str}.",
            body=body,
            citations=citations,
            sources=("yoga_engine", "knowledge_engine"),
            recommendations=yoga.satisfied if yoga.satisfied else (),
            version=_ENGINE_VERSION,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Dasha Interpreter
# ═══════════════════════════════════════════════════════════════════════════════


class DashaIinterpreter:
    """Describes active Dasha periods."""

    @staticmethod
    def generate(
        period: DashaPeriod,
        chart: Optional[D1Chart] = None,
    ) -> AIResponse:
        lord = _planet_name(period.lord)
        body = (
            f"{lord} {['Mahadasha', 'Antardasha', 'Pratyantar', 'Sookshma', 'Prana'][period.level - 1]}: "
            f"{period.start_date} to {period.end_date} "
            f"({period.duration_days} days, level {period.level})."
        )

        # If we have a chart, add lord's placement.
        if chart:
            for p in chart.planets:
                if p.planet == period.lord:
                    dignity = p.dignity.value if p.dignity else "neutral"
                    body += (
                        f" {lord} is placed in {_rashi_name(p.rashi)} "
                        f"in house {p.house_number} ({dignity})."
                    )
                    break

        return AIResponse(
            response_type="dasha_interpretation",
            title=f"{lord} Dasha (Level {period.level})",
            summary=f"{lord} period active from {period.start_date} to {period.end_date}.",
            body=body,
            sources=("dasha_engine", "chart_engine"),
            version=_ENGINE_VERSION,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Transit Reader
# ═══════════════════════════════════════════════════════════════════════════════


class TransitReader:
    """Generates transit readings."""

    @staticmethod
    def generate(
        transits: tuple[TransitPlanetResult, ...],
    ) -> AIResponse:
        if not transits:
            return AIResponse(
                response_type="transit_reading",
                title="Transit Reading",
                summary="No transit data available.",
                body="Transit positions were not computed for this request.",
                sources=("transit_engine",),
                version=_ENGINE_VERSION,
            )

        lines: list[str] = []
        for t in transits:
            parts = [
                f"{_planet_name(t.planet)} is transiting {_rashi_name(t.transit_rashi)}, "
                f"house {t.house_from_natal_moon} from the natal Moon."
            ]
            if t.is_sade_sati:
                parts.append(" Sade Sati active.")
            if t.is_ashtama_shani:
                parts.append(" Ashtama Shani active.")
            if t.has_vedha:
                parts.append(f" Vedha from {t.vedha_planet}.")
            lines.append("".join(parts))

        body = "\n".join(lines)

        return AIResponse(
            response_type="transit_reading",
            title="Current Transit Reading",
            summary=f"{len(transits)} planets analyzed for transit positions.",
            body=body,
            sources=("transit_engine", "ashtakavarga_engine"),
            version=_ENGINE_VERSION,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Verification Reporter
# ═══════════════════════════════════════════════════════════════════════════════


class VerificationReporter:
    """Summarizes verification findings."""

    @staticmethod
    def generate(
        findings: VerificationFindings,
    ) -> AIResponse:
        strengths: dict[str, int] = {}
        for pair in findings.verification_pairs:
            key = pair.strength.value if hasattr(pair.strength, "value") else str(pair.strength)
            strengths[key] = strengths.get(key, 0) + 1

        body_lines: list[str] = [
            f"Total evaluations: {findings.total_pairs} across {findings.total_rules_evaluated} rules.",
            f"Confidence distribution:",
        ]
        for s, count in sorted(strengths.items()):
            body_lines.append(f"  - {s}: {count}")

        summary = (
            f"{findings.total_pairs} rule evaluations completed. "
            f"{strengths.get('high', 0)} confirmed at high confidence."
        )

        return AIResponse(
            response_type="verification_report",
            title="Verification Report",
            summary=summary,
            body="\n".join(body_lines),
            sources=("verification_engine", "rule_engine", "event_engine"),
            confidence=_confidence_from_verification(findings),
            version=_ENGINE_VERSION,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Research Insight Generator
# ═══════════════════════════════════════════════════════════════════════════════


class ResearchInsightGenerator:
    """Produces comparative insights from statistics."""

    @staticmethod
    def generate(
        stats: AggregateReport,
    ) -> AIResponse:
        body_lines: list[str] = [
            f"Analysis of {stats.metadata.sample_size} snapshots.",
            "",
            "Distributions:",
        ]
        for d in stats.distributions:
            peak_idx = max(range(len(d.counts)), key=lambda i: d.counts[i])
            peak_bin = d.bins[peak_idx] if peak_idx < len(d.bins) else "?"
            body_lines.append(
                f"  - {d.label}: peak at {peak_bin} ({d.counts[peak_idx]} occurrences, total {d.total})."
            )

        return AIResponse(
            response_type="research_insight",
            title="Research Insights",
            summary=f"{stats.metadata.sample_size} snapshots analyzed with {len(stats.distributions)} distributions.",
            body="\n".join(body_lines),
            sources=("statistics_engine", "research_engine"),
            version=_ENGINE_VERSION,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Recommendation Engine
# ═══════════════════════════════════════════════════════════════════════════════


# Canonical Nakshatra to Vimshottari Lord Mapping (27 Nakshatras)
NAK_TO_VIMSHOTTARI: dict[str, str] = {
    # Cycle 1
    "ashwini": "Ketu", "bharani": "Venus", "krittika": "Sun", "rohini": "Moon",
    "mrigashira": "Mars", "mrigasira": "Mars", "ardra": "Rahu", "punarvasu": "Jupiter",
    "pushya": "Saturn", "ashlesha": "Mercury", "aslesha": "Mercury",
    # Cycle 2
    "magha": "Ketu", "purva_phalguni": "Venus", "purva phalguni": "Venus",
    "uttara_phalguni": "Sun", "uttara phalguni": "Sun", "hasta": "Moon",
    "chitra": "Mars", "swati": "Rahu", "vishakha": "Jupiter", "visakha": "Jupiter",
    "anuradha": "Saturn", "jyeshtha": "Mercury", "jyeshta": "Mercury",
    # Cycle 3
    "mula": "Ketu", "moola": "Ketu", "purva_ashadha": "Venus", "purva ashadha": "Venus",
    "uttara_ashadha": "Sun", "uttara ashadha": "Sun", "shravana": "Moon", "sravana": "Moon",
    "dhanishta": "Mars", "dhanishtha": "Mars", "shatabhisha": "Rahu", "satabhisha": "Rahu",
    "shatataraka": "Rahu", "purva_bhadrapada": "Jupiter", "purva bhadrapada": "Jupiter",
    "uttara_bhadrapada": "Saturn", "uttara bhadrapada": "Saturn", "revati": "Mercury",
}


class RecommendationEngine:
    """Generates contextual recommendations."""

    @staticmethod
    def generate(
        timeline: Optional[Timeline] = None,
        verification: Optional[VerificationFindings] = None,
        transits: tuple[TransitPlanetResult, ...] = (),
    ) -> AIResponse:
        recs: list[str] = []

        if verification:
            confirmed = sum(
                1 for p in verification.verification_pairs
                if p.alignment.value == "confirmed"
            )
            if confirmed > 0:
                recs.append(
                    f"Focus on areas where rules have been confirmed ({confirmed} confirmed pairs). "
                    f"Consider tracking additional events in untested categories."
                )

        for t in transits:
            if t.is_sade_sati:
                recs.append(
                    f"Sade Sati is active (Saturn in house {t.house_from_natal_moon}). "
                    f"This period favors reflection, discipline, and long-term planning."
                )
            if t.has_vedha:
                recs.append(
                    f"Transit obstruction (Vedha) detected for {_planet_name(t.planet)} "
                    f"from {_planet_name(t.vedha_planet) if t.vedha_planet else 'another planet'}. "
                    f"Consider reviewing classical remedies."
                )

        if not recs:
            recs.append("Continue tracking events to enable personalized recommendations.")

        return AIResponse(
            response_type="recommendation",
            title="Astrological Recommendations",
            summary=f"{len(recs)} recommendation{'s' if len(recs) != 1 else ''} generated.",
            body="\n".join(f"• {r}" for r in recs),
            recommendations=tuple(recs),
            sources=("verification_engine", "timeline_engine", "transit_engine"),
            version=_ENGINE_VERSION,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# QA Responder
# ═══════════════════════════════════════════════════════════════════════════════


def normalize_rule_id(rule_id: str) -> str:
    """
    Case-insensitive string normalizer for rule IDs.
    Transforms rule_id to lower case with hyphens replaced by underscores and whitespace trimmed,
    then resolves standard aliases (GAJA-001 -> gaja_kesari_yoga, DHANA-001 -> lakshmi_yoga,
    RAJA-001 -> dharma_karmadhipati_yoga, BUDHA-001 -> budhaditya_yoga).
    """
    from apps.api.services.rule_registry import normalize_rule_id as _reg_norm
    return _reg_norm(rule_id)


class QAResponder:
    """Answers natural language questions using chart data and astrological principles."""

    @staticmethod
    def generate(
        question: str,
        chart: Optional[D1Chart] = None,
    ) -> AIResponse:
        q = question.lower().strip()
        body: str
        title_topic: str = "Astrological Query"

        if not chart:
            body = "Chart data is required to answer this question. Please calculate or load a birth chart first."
            return AIResponse(
                response_type="qa_answer",
                title=f"Q: {question[:80]}{'...' if len(question) > 80 else ''}",
                summary="Chart data required.",
                body=body,
                sources=("chart_engine", "vedic_rules"),
                version=_ENGINE_VERSION,
            )

        asc = chart.ascendant
        asc_rashi = _rashi_name(asc.rashi) if asc else "Unknown"
        planets_by_name = {p.planet.lower(): p for p in chart.planets}
        planets_by_house: dict[int, list[Any]] = {}
        for p in chart.planets:
            planets_by_house.setdefault(p.house_number, []).append(p)

        def _clean_nak_title(raw_nak: str) -> str:
            if not raw_nak:
                return "Ashwini"
            return str(raw_nak).replace("_", " ").title()

        def _planet_pill(p: Optional[Any]) -> str:
            if not p:
                return "Not present"
            tags = []
            if p.dignity:
                dignity_map = {
                    "exalted": "Peak Strength (Exalted)",
                    "moolatrikona": "Exceptionally Strong (Moolatrikona)",
                    "own": "Strong & Stable (Own Sign)",
                    "friendly": "Naturally Supportive",
                    "neutral": "Balanced (Neutral)",
                    "enemy": "Challenging (Requires Extra Effort)",
                    "debilitated": "Needs Conscious Care (Debilitated)",
                }
                tags.append(dignity_map.get(p.dignity.value.lower(), p.dignity.value.capitalize()))
            if getattr(p, "is_combust", False):
                tags.append("Combust (near Sun)")
            if getattr(p, "is_retrograde", False):
                tags.append("Retrograde (intense internal drive)")
            tag_str = f" — {', '.join(tags)}" if tags else ""
            nak_title = _clean_nak_title(p.nakshatra)
            return f"• **{_planet_name(p.planet)}** in House {p.house_number} ({_rashi_name(p.rashi)} sign, {nak_title} star){tag_str}"

        def _describe_house(h_num: int, label: str = "") -> str:
            occ = planets_by_house.get(h_num, [])
            header = f"{label} (House {h_num})" if label else f"House {h_num}"
            if occ:
                occ_str = "\n  " + "\n  ".join(_planet_pill(p) for p in occ)
                return f"• **{header}** contains:{occ_str}"
            return f"• **{header}**: Currently unoccupied (Influenced by House Lord)."

        moon = planets_by_name.get("moon")
        raw_moon_nak = str(getattr(moon, "nakshatra", "") or "ashwini").lower().strip()
        moon_nak_slug = raw_moon_nak.replace("-", "_").replace(" ", "_")
        moon_nak_title = _clean_nak_title(raw_moon_nak)
        moon_rashi = _rashi_name(moon.rashi) if moon else "Unknown"

        janma_dasha_lord_name = NAK_TO_VIMSHOTTARI.get(moon_nak_slug, NAK_TO_VIMSHOTTARI.get(raw_moon_nak, "Ketu"))
        janma_dasha_lord_p = planets_by_name.get(janma_dasha_lord_name.lower())
        dasha_lord_pill = _planet_pill(janma_dasha_lord_p) if janma_dasha_lord_p else f"**{janma_dasha_lord_name}**"

        def _format_key_planets(planets_with_roles: list[tuple[Optional[Any], str, str]]) -> str:
            lines = []
            for p, role_name, default_significator in planets_with_roles:
                if p:
                    lines.append(f"  {_planet_pill(p)} ({role_name})")
                else:
                    lines.append(f"  • **{default_significator}**: General significator for {role_name.lower()}")
            return "\n".join(lines)

        if "money" in q or "wealth" in q or "gain" in q or "finance" in q or "dhana" in q:
            title_topic = "Monetary & Wealth Gains Analysis"
            h11 = _describe_house(11, "Primary Income & Growth")
            h2 = _describe_house(2, "Savings & Treasury")
            h9 = _describe_house(9, "Fortune & Opportunities")
            jup = planets_by_name.get("jupiter")
            ven = planets_by_name.get("venus")
            merc = planets_by_name.get("mercury")
            wealth_planets = _format_key_planets([
                (jup, "Expansion & Fortune", "Jupiter"),
                (ven, "Assets & Luxury", "Venus"),
                (merc, "Commercial Strategy & Trade", "Mercury"),
            ])
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"You have strong potential for accumulating wealth and generating cash flow, driven by active planetary configurations in your financial houses. Focus on steady compounding, avoid speculative trading during cycle transitions, and build an emergency reserve.\n\n"
                f"📊 **Key Wealth Placements**\n"
                f"{h11}\n"
                f"{h2}\n"
                f"{h9}\n"
                f"• **Key Career & Investment Factors**:\n"
                f"{wealth_planets}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• **Timing Alert**: Your birth planetary cycle is anchored by Moon in **{moon_nak_title}** star (ruled by **{janma_dasha_lord_name}**). Expect major financial breakthroughs during sub-periods activating your 2nd or 11th houses. Avoid risky investments during major cycle transitions (*Dasha Sandhi*).\n"
                f"• **Weekly Action**: Recite *Shri Suktam* or *Lakshmi Gayatri* on Friday mornings to strengthen financial abundance.\n"
                f"• **Remedies**: Support educational initiatives on Thursdays (Jupiter) and contribute to creative/women's welfare causes on Fridays (Venus).\n"
                f"• **Smart Money Rule**: Focus on compounding, avoid impulsive debt, and maintain an emergency asset cushion."
            )

        elif "career" in q or "job" in q or "profession" in q or "work" in q or "status" in q or "10th" in q:
            title_topic = "Career & Professional Impact Analysis"
            h10 = _describe_house(10, "Career, Leadership & Public Status")
            h6 = _describe_house(6, "Problem-Solving & Daily Execution")
            h1 = _describe_house(1, "Personal Brand & Authority")
            sun = planets_by_name.get("sun")
            sat = planets_by_name.get("saturn")
            mars = planets_by_name.get("mars")
            career_planets = _format_key_planets([
                (sun, "Executive Presence & Authority", "Sun"),
                (sat, "Long-Term Perseverance & Discipline", "Saturn"),
                (mars, "Execution Drive & Initiative", "Mars"),
            ])
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Your professional trajectory points toward executive leadership, strategic problem-solving, and steady career advancement. Your vocational growth is anchored in your 10th House of public reputation, powered by daily execution in your 6th House.\n\n"
                f"📊 **Key Career Placements**\n"
                f"{h10}\n"
                f"{h6}\n"
                f"{h1}\n"
                f"• **Key Career Drivers**:\n"
                f"{career_planets}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• **Timing Alert**: Your career timeline is steered by your birth star **{moon_nak_title}** (ruled by **{janma_dasha_lord_name}**). Significant promotions, role expansions, and leadership milestones emerge during periods activating your 10th house or major power angular houses (Kendras).\n"
                f"• **Leadership Practice**: Recite the *Aditya Hridaya Stotram* or spend 5 minutes in morning sunlight on Sundays to enhance clarity, vitality, and executive authority.\n"
                f"• **Workplace Ethics**: Treat subordinates and support staff with respect on Saturdays to build lasting workplace loyalty and appease Saturn.\n"
                f"• **Execution Strategy**: Set clear quarterly milestones, seek guidance from senior mentors, and avoid abrupt career leaps during unsupportive transition cycles (*Dasha Sandhi*)."
            )

        elif "transit" in q or "gochara" in q or "current" in q:
            title_topic = "Current Planetary Transits Overview"
            jup = planets_by_name.get("jupiter")
            sat = planets_by_name.get("saturn")
            rahu = planets_by_name.get("rahu")
            ketu = planets_by_name.get("ketu")
            transit_planets = _format_key_planets([
                (sat, "Structure & Long-Term Foundations", "Saturn"),
                (jup, "Expansion, Wisdom & Opportunities", "Jupiter"),
                (rahu, "Ambition & Innovation", "Rahu"),
                (ketu, "Spiritual Clarity & Insight", "Ketu"),
            ])
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Current planetary movements in the sky act as real-time triggers for the latent potential of your birth chart. Transits bring new opportunities and milestones into physical reality when aligned with your active life cycles.\n\n"
                f"📊 **Key Transit Influences**\n"
                f"• **Natal Foundation**: Ascendant in {asc_rashi} ({asc.rashi_degree:.1f}°), Moon in {moon_rashi} ({moon_nak_title} star).\n"
                f"• **Major Structural Anchors**:\n"
                f"{transit_planets}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• **Timing Alert**: Transits only deliver what your birth chart and active planetary period (Dasha ruled by **{janma_dasha_lord_name}**) permit. Major shifts by slow-moving planets (Saturn and Jupiter) crossing your Moon sign ({moon_rashi}) mark pivotal life chapters.\n"
                f"• **Harmonizing Practice**: Recite the *Navagraha Stotram* on Tuesdays and Saturdays to smooth out planetary friction and sustain mental calm.\n"
                f"• **Mindful Decision-Making**: Avoid making rushed long-term commitments during sensitive transit passages over challenging houses (such as the 8th or 12th houses).\n"
                f"• **Auspicious Windows**: Leverage Jupiter's supportive transit windows for personal development, learning, and philanthropic actions."
            )

        elif "health" in q or "vitality" in q or "wellness" in q or "disease" in q or "6th" in q:
            title_topic = "Health & Vitality Overview"
            h1 = _describe_house(1, "Physical Frame & Natural Immunity")
            h6 = _describe_house(6, "Digestive Fire & Daily Wellness")
            h8 = _describe_house(8, "Cellular Longevity & Rejuvenation")
            sun = planets_by_name.get("sun")
            mars = planets_by_name.get("mars")
            vitality_planets = _format_key_planets([
                (sun, "Vital Life Force & Stamina", "Sun"),
                (moon, "Mental Equilibrium & Hydration", "Moon"),
                (mars, "Muscular Strength & Physical Drive", "Mars"),
            ])
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Your constitutional vitality is anchored by your 1st House of natural immunity, balanced by daily wellness habits and cellular longevity. Maintaining steady daily rhythms and preventive health checks ensures peak resilience.\n\n"
                f"📊 **Key Vitality Placements**\n"
                f"{h1}\n"
                f"{h6}\n"
                f"{h8}\n"
                f"• **Key Vitality Factors**:\n"
                f"{vitality_planets}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• **Timing Alert**: Your wellness baseline is governed by Moon in **{moon_nak_title}** (ruled by **{janma_dasha_lord_name}**). Temporary energy dips often occur during transitional junction phases (*Dasha Sandhi*); prioritize restorative routines during these windows.\n"
                f"• **Morning Routine**: Practice morning *Surya Namaskar* (Sun Salutations) facing East and recite Gayatri or Maha Mrityunjaya mantra for immune strength.\n"
                f"• **Dietary Balance**: Maintain an Ayurvedic balanced seasonal diet suited to your **{asc_rashi}** constitution (balancing warmth, hydration, and clean nutrition).\n"
                f"• **Preventive Care**: Schedule routine health check-ups and safeguard consistent sleep cycles during intense work periods."
            )

        elif "marriage" in q or "relationship" in q or "partner" in q or "spouse" in q or "7th" in q:
            title_topic = "Relationship & 7th House Analysis"
            h7 = _describe_house(7, "Marriage & Long-Term Partnerships")
            ven = planets_by_name.get("venus")
            jup = planets_by_name.get("jupiter")
            rel_planets = _format_key_planets([
                (ven, "Romantic Affection & Harmony", "Venus"),
                (jup, "Mutual Respect, Values & Protection", "Jupiter"),
            ])
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Your relationship dynamics are guided by your 7th House of mutual partnership, with Venus fostering love and companionship and Jupiter providing wisdom, shared values, and protection.\n\n"
                f"📊 **Key Relationship Placements**\n"
                f"{h7}\n"
                f"• **Key Relationship Factors**:\n"
                f"{rel_planets}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• **Timing Alert**: Relationship milestones and mutual harmony unfold during supportive planetary periods involving the 7th or 1st house lords, or during benefic transits of Jupiter/Venus.\n"
                f"• **Harmony Practice**: Recite the *Gauri Shankar Mantra* or *Radha Krishna Stotram* on Friday evenings for mutual peace.\n"
                f"• **Communication Rule**: Practice active listening, transparent dialogue, and honor your partner's personal boundaries."
            )

        elif "ascendant" in q or "lagna" in q:
            title_topic = "Ascendant (Lagna) Profile"
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Your Ascendant (Lagna / Rising Sign) is **{asc_rashi}** at {asc.rashi_degree:.1f}°. It forms the master lens through which you experience the world, shaping your natural personality, physical temperament, and life approach.\n\n"
                f"📊 **Key Placements**\n"
                f"• Ascendant establishes your core vitality, worldview, and executive disposition.\n"
                f"• Planets in the 1st House: {', '.join(_planet_pill(p) for p in planets_by_house.get(1, [])) or 'No occupant planets (reflects pure sign characteristics)'}.\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• Align daily habits with the natural strengths of {asc_rashi} and nurture your physical health through regular morning routines."
            )

        elif "sun" in q:
            sun = planets_by_name.get("sun")
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"The Sun represents your core soul vitality, leadership presence, and public authority.\n\n"
                f"📊 **Key Placements**\n"
                f"{_planet_pill(sun) if sun else 'Sun position not available in this chart.'}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• Honor the Sun on Sunday mornings through *Surya Namaskar* to reinforce clarity and career confidence."
            )

        elif "moon" in q:
            moon = planets_by_name.get("moon")
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"The Moon represents your emotional mind, intuitive perception, and mental peace.\n\n"
                f"📊 **Key Placements**\n"
                f"{_planet_pill(moon) if moon else 'Moon position not available in this chart.'}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• Practice calming evening routines and stay well-hydrated to support steady emotional wellness."
            )

        elif "mars" in q or "mangal" in q or "kuja" in q:
            mars = planets_by_name.get("mars")
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Mars governs your physical energy, execution drive, courage, and initiative.\n\n"
                f"📊 **Key Placements**\n"
                f"{_planet_pill(mars) if mars else 'Mars position not available in this chart.'}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• Channel physical energy into disciplined workouts and constructive goals on Tuesdays."
            )

        elif "mercury" in q or "budha" in q:
            merc = planets_by_name.get("mercury")
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Mercury governs your analytical intellect, communication clarity, business acumen, and learning agility.\n\n"
                f"📊 **Key Placements**\n"
                f"{_planet_pill(merc) if merc else 'Mercury position not available in this chart.'}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• Engage in intellectual exploration, writing, and commercial planning on Wednesdays."
            )

        elif "jupiter" in q or "guru" in q:
            jup = planets_by_name.get("jupiter")
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Jupiter is the great benefic planet governing wisdom, financial expansion, mentorship, and good fortune.\n\n"
                f"📊 **Key Placements**\n"
                f"{_planet_pill(jup) if jup else 'Jupiter position not available in this chart.'}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• Support teachers, engage in study, and donate to educational charities on Thursdays."
            )

        elif "venus" in q or "shukra" in q:
            ven = planets_by_name.get("venus")
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Venus governs love, aesthetic appreciation, material comfort, and relational harmony.\n\n"
                f"📊 **Key Placements**\n"
                f"{_planet_pill(ven) if ven else 'Venus position not available in this chart.'}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• Foster harmonious relationships and celebrate artistic endeavors on Fridays."
            )

        elif "saturn" in q or "shani" in q:
            sat = planets_by_name.get("saturn")
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Saturn represents discipline, life structure, endurance, and long-term mastery through consistent effort.\n\n"
                f"📊 **Key Placements**\n"
                f"{_planet_pill(sat) if sat else 'Saturn position not available in this chart.'}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• Practice patience, maintain ethical integrity, and assist those in need on Saturdays."
            )

        elif "rahu" in q or "ketu" in q:
            rahu = planets_by_name.get("rahu")
            ketu = planets_by_name.get("ketu")
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Rahu and Ketu (the lunar nodes) represent your axis of worldly innovation and spiritual evolution.\n\n"
                f"📊 **Key Placements**\n"
                f"{_planet_pill(rahu)}\n"
                f"{_planet_pill(ketu)}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• Balance ambitious outward goals (Rahu) with quiet inner mindfulness (Ketu)."
            )

        elif "retrograde" in q or "vakri" in q:
            retrogrades = [p for p in chart.planets if getattr(p, "is_retrograde", False)]
            if retrogrades:
                ret_list = "\n".join(_planet_pill(p) for p in retrogrades)
                body = (
                    f"⚡ **Bottom Line (Executive Summary)**\n"
                    f"Retrograde planets indicate areas where energy is directed inward for deeper reflection, unique problem-solving, and second chances.\n\n"
                    f"📊 **Key Placements**\n"
                    f"{ret_list}\n\n"
                    f"⏰ **Action Plan & Timing**\n"
                    f"• Leverage your unique, non-linear insights in these areas rather than rushing conventional outcomes."
                )
            else:
                body = (
                    f"⚡ **Bottom Line (Executive Summary)**\n"
                    f"All planets in this chart are moving in direct (forward) motion, indicating smooth, forward-moving external energy in your life endeavors."
                )

        else:
            planet_list = "\n".join(_planet_pill(p) for p in chart.planets[:6])
            body = (
                f"⚡ **Bottom Line (Executive Summary)**\n"
                f"Astrological analysis for **{asc_rashi} Ascendant** native based on key planetary placements and active life timing cycles.\n\n"
                f"📊 **Key Placements**\n"
                f"• Ascendant: {asc_rashi} ({asc.rashi_degree:.1f}°)\n"
                f"{planet_list}\n\n"
                f"⏰ **Action Plan & Timing**\n"
                f"• Planetary influences manifest through the operative Dasha cycle (seed lord **{janma_dasha_lord_name}**) and angular power houses (Kendras 1, 4, 7, 10)."
            )

        return AIResponse(
            response_type="qa_answer",
            title=f"Q: {question[:80]}{'...' if len(question) > 80 else ''}",
            summary=body.split("\n\n")[0] if "\n\n" in body else body[:200],
            body=body,
            sources=("chart_engine", "vedic_rules"),
            version=_ENGINE_VERSION,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AI Engine
# ═══════════════════════════════════════════════════════════════════════════════


class AIEngine:
    """Dispatches explanation requests to the correct generator.

    Phase IV (IV.3): every response passes through _maybe_enrich() before
    returning. With the default AI_BACKEND=template, that's a no-op — the
    plain deterministic template output goes straight through, unchanged.
    Only with the opt-in AI_BACKEND=local_llm does it attempt to rewrite
    `body` via a locally-hosted model, and even then falls straight back
    to the template body if that local server is unreachable.
    """

    _ENGINE_VERSION = _ENGINE_VERSION

    @staticmethod
    def _maybe_enrich(response: AIResponse) -> AIResponse:
        """Opt-in narration enrichment. See local_llm_client.py's module
        docstring for the fallback contract this relies on."""
        settings = get_settings()
        if settings.AI_BACKEND != "local_llm":
            return response

        enriched_body = enrich_narration(
            base_url=settings.LOCAL_LLM_BASE_URL,
            model=settings.LOCAL_LLM_MODEL,
            timeout_seconds=settings.LOCAL_LLM_TIMEOUT_SECONDS,
            grounding_text=response.body,
        )
        if enriched_body is None:
            return response
        return dataclasses.replace(response, body=enriched_body)

    @staticmethod
    def explain(request: ExplanationRequest) -> AIResponse:
        topic = request.topic
        data = request.source_data
        style = request.style

        if topic == "chart_summary":
            chart = data.get("chart")
            if not chart:
                return _missing_data("chart")
            verification = data.get("verification")
            return AIEngine._maybe_enrich(ChartSummarizer.generate(chart, style, verification))

        elif topic == "yoga_explanation":
            yoga = data.get("yoga")
            if not yoga:
                return _missing_data("yoga")
            karakatvas = data.get("karakatvas", ())
            citations = data.get("citations", ())
            return AIEngine._maybe_enrich(YogaExplainer.generate(yoga, karakatvas, citations))

        elif topic == "dasha_interpretation":
            period = data.get("period")
            if not period:
                return _missing_data("dasha period")
            chart = data.get("chart")
            return AIEngine._maybe_enrich(DashaIinterpreter.generate(period, chart))

        elif topic == "transit_reading":
            transits = data.get("transits", ())
            return AIEngine._maybe_enrich(TransitReader.generate(tuple(transits)))

        elif topic == "verification_report":
            findings = data.get("findings")
            if not findings:
                return _missing_data("verification findings")
            return AIEngine._maybe_enrich(VerificationReporter.generate(findings))

        elif topic == "research_insight":
            stats = data.get("stats")
            if not stats:
                return _missing_data("statistics")
            return AIEngine._maybe_enrich(ResearchInsightGenerator.generate(stats))

        elif topic == "recommendation":
            timeline = data.get("timeline")
            verification = data.get("verification")
            transits = data.get("transits", ())
            return AIEngine._maybe_enrich(
                RecommendationEngine.generate(timeline, verification, tuple(transits))
            )

        elif topic == "qa":
            question = data.get("question", "")
            chart = data.get("chart")
            return AIEngine._maybe_enrich(QAResponder.generate(question, chart))

        else:
            return AIResponse(
                response_type="error",
                title="Unknown Topic",
                summary=f"No generator for topic: {topic}",
                body=f"The topic '{topic}' is not recognized. Supported topics: "
                     f"chart_summary, yoga_explanation, dasha_interpretation, "
                     f"transit_reading, verification_report, research_insight, "
                     f"recommendation, qa.",
                version=_ENGINE_VERSION,
            )

    @staticmethod
    def chart_summary(
        chart: D1Chart,
        style: str = "concise",
        verification: Optional[VerificationFindings] = None,
    ) -> AIResponse:
        return AIEngine._maybe_enrich(ChartSummarizer.generate(chart, style, verification))

    @staticmethod
    def explain_yoga(
        yoga: YogaResult,
        karakatvas: tuple = (),
        citations: tuple[Citation, ...] = (),
    ) -> AIResponse:
        return AIEngine._maybe_enrich(YogaExplainer.generate(yoga, karakatvas, citations))

    @staticmethod
    def interpret_dasha(
        period: DashaPeriod,
        chart: Optional[D1Chart] = None,
    ) -> AIResponse:
        return AIEngine._maybe_enrich(DashaIinterpreter.generate(period, chart))

    @staticmethod
    def read_transit(
        transits: tuple[TransitPlanetResult, ...],
    ) -> AIResponse:
        return AIEngine._maybe_enrich(TransitReader.generate(transits))

    @staticmethod
    def report_verification(
        findings: VerificationFindings,
    ) -> AIResponse:
        return AIEngine._maybe_enrich(VerificationReporter.generate(findings))

    @staticmethod
    def research_insight(
        stats: AggregateReport,
    ) -> AIResponse:
        return AIEngine._maybe_enrich(ResearchInsightGenerator.generate(stats))

    @staticmethod
    def recommend(
        timeline: Optional[Timeline] = None,
        verification: Optional[VerificationFindings] = None,
        transits: tuple[TransitPlanetResult, ...] = (),
    ) -> AIResponse:
        return AIEngine._maybe_enrich(RecommendationEngine.generate(timeline, verification, transits))

    @staticmethod
    def answer_question(
        question: str,
        chart: Optional[D1Chart] = None,
    ) -> AIResponse:
        return AIEngine._maybe_enrich(QAResponder.generate(question, chart))


def _missing_data(name: str) -> AIResponse:
    return AIResponse(
        response_type="error",
        title="Missing Data",
        summary=f"{name} data is required but was not provided.",
        body=f"The {name} data was not included in the request. "
             f"Please provide the required source data and try again.",
        version=_ENGINE_VERSION,
    )
