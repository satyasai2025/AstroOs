"""
AstroOS — AI Engine (Module 24, Phase 1)

Template-based natural language generation from existing domain objects.
8 generators consuming all completed modules. No external LLM, no
network calls, no astrology calculations.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from apps.api.domain.ai import AIResponse, Citation, ExplanationRequest
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

_ENGINE_VERSION = "1.0"
_RASHI_NAMES = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


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


class QAResponder:
    """Answers natural language questions using chart data."""

    @staticmethod
    def generate(
        question: str,
        chart: Optional[D1Chart] = None,
    ) -> AIResponse:
        q = question.lower().strip()
        body: str

        if not chart:
            body = "Chart data is required to answer this question."

        elif "ascendant" in q or "lagna" in q:
            asc = chart.ascendant
            body = (
                f"The ascendant (lagna) is {_rashi_name(asc.rashi) if asc else 'unknown'}, "
                f"at {asc.rashi_degree:.1f} degrees." if asc else "Ascendant data not available."
            )

        elif "sun" in q:
            sun = next((p for p in chart.planets if p.planet == "sun"), None)
            body = (
                f"Sun is in {_rashi_name(sun.rashi)} in house {sun.house_number}, "
                f"dignity: {sun.dignity.value if sun.dignity else 'neutral'}."
                if sun else "Sun position not available."
            )

        elif "moon" in q:
            moon = next((p for p in chart.planets if p.planet == "moon"), None)
            body = (
                f"Moon is in {_rashi_name(moon.rashi)} in house {moon.house_number}, "
                f"nakshatra: {moon.nakshatra}."
                if moon else "Moon position not available."
            )

        elif "jupiter" in q or "guru" in q:
            jup = next((p for p in chart.planets if p.planet == "jupiter"), None)
            body = (
                f"Jupiter is in {_rashi_name(jup.rashi)} in house {jup.house_number}, "
                f"dignity: {jup.dignity.value if jup.dignity else 'neutral'}."
                if jup else "Jupiter position not available."
            )

        elif "retrograde" in q or "vakri" in q:
            retrogrades = [p for p in chart.planets if p.is_retrograde]
            if retrogrades:
                names = ", ".join(_planet_name(p.planet) for p in retrogrades)
                body = f"Retrograde planets: {names}."
            else:
                body = "No planets are currently retrograde in this chart."

        else:
            body = (
                "I can answer questions about the ascendant, Sun, Moon, Jupiter, "
                "and retrograde planets. Please ask a more specific question."
            )

        return AIResponse(
            response_type="qa_answer",
            title=f"Q: {question[:80]}{'...' if len(question) > 80 else ''}",
            summary=body[:200] if len(body) > 200 else body,
            body=body,
            sources=("chart_engine",),
            version=_ENGINE_VERSION,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AI Engine
# ═══════════════════════════════════════════════════════════════════════════════


class AIEngine:
    """Dispatches explanation requests to the correct generator."""

    _ENGINE_VERSION = _ENGINE_VERSION

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
            return ChartSummarizer.generate(chart, style, verification)

        elif topic == "yoga_explanation":
            yoga = data.get("yoga")
            if not yoga:
                return _missing_data("yoga")
            karakatvas = data.get("karakatvas", ())
            citations = data.get("citations", ())
            return YogaExplainer.generate(yoga, karakatvas, citations)

        elif topic == "dasha_interpretation":
            period = data.get("period")
            if not period:
                return _missing_data("dasha period")
            chart = data.get("chart")
            return DashaIinterpreter.generate(period, chart)

        elif topic == "transit_reading":
            transits = data.get("transits", ())
            return TransitReader.generate(tuple(transits))

        elif topic == "verification_report":
            findings = data.get("findings")
            if not findings:
                return _missing_data("verification findings")
            return VerificationReporter.generate(findings)

        elif topic == "research_insight":
            stats = data.get("stats")
            if not stats:
                return _missing_data("statistics")
            return ResearchInsightGenerator.generate(stats)

        elif topic == "recommendation":
            timeline = data.get("timeline")
            verification = data.get("verification")
            transits = data.get("transits", ())
            return RecommendationEngine.generate(timeline, verification, tuple(transits))

        elif topic == "qa":
            question = data.get("question", "")
            chart = data.get("chart")
            return QAResponder.generate(question, chart)

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
        return ChartSummarizer.generate(chart, style, verification)

    @staticmethod
    def explain_yoga(
        yoga: YogaResult,
        karakatvas: tuple = (),
        citations: tuple[Citation, ...] = (),
    ) -> AIResponse:
        return YogaExplainer.generate(yoga, karakatvas, citations)

    @staticmethod
    def interpret_dasha(
        period: DashaPeriod,
        chart: Optional[D1Chart] = None,
    ) -> AIResponse:
        return DashaIinterpreter.generate(period, chart)

    @staticmethod
    def read_transit(
        transits: tuple[TransitPlanetResult, ...],
    ) -> AIResponse:
        return TransitReader.generate(transits)

    @staticmethod
    def report_verification(
        findings: VerificationFindings,
    ) -> AIResponse:
        return VerificationReporter.generate(findings)

    @staticmethod
    def research_insight(
        stats: AggregateReport,
    ) -> AIResponse:
        return ResearchInsightGenerator.generate(stats)

    @staticmethod
    def recommend(
        timeline: Optional[Timeline] = None,
        verification: Optional[VerificationFindings] = None,
        transits: tuple[TransitPlanetResult, ...] = (),
    ) -> AIResponse:
        return RecommendationEngine.generate(timeline, verification, transits)

    @staticmethod
    def answer_question(
        question: str,
        chart: Optional[D1Chart] = None,
    ) -> AIResponse:
        return QAResponder.generate(question, chart)


def _missing_data(name: str) -> AIResponse:
    return AIResponse(
        response_type="error",
        title="Missing Data",
        summary=f"{name} data is required but was not provided.",
        body=f"The {name} data was not included in the request. "
             f"Please provide the required source data and try again.",
        version=_ENGINE_VERSION,
    )
