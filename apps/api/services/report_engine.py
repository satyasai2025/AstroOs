"""
AstroOS — Report Engine (Module 20, Phase 1)

Assembles structured reports from existing module outputs. An assembly
layer — composes domain objects into report sections without performing
any calculations, statistics, or astrology.

Takes already-computed data. Never calls any engine.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from apps.api.domain.event_analysis import EventAnalysisRecord
from apps.api.domain.events import NatalSnapshot
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.knowledge import KnowledgeSearchResult
from apps.api.domain.research import AstrologicalSnapshot
from apps.api.domain.statistics import AggregateReport
from apps.api.domain.timeline import Timeline
from apps.api.domain.verification import VerificationFindings
from apps.api.domain.report import (
    ChartReport,
    ComparisonReport,
    ReportContent,
    ReportMetadata,
    ReportSection,
    ResearchReport,
)

_ENGINE_VERSION = "1.0"


def _build_metadata(
    report_type: str,
    chart_id: uuid.UUID | None = None,
    research_project_id: uuid.UUID | None = None,
    generated_by: str | None = None,
    extra_versions: dict[str, str] | None = None,
) -> ReportMetadata:
    versions = {"report_engine": _ENGINE_VERSION}
    if extra_versions:
        versions.update(extra_versions)
    return ReportMetadata(
        report_id=uuid.uuid4(),
        report_type=report_type,
        report_version=_ENGINE_VERSION,
        generated_at=datetime.now(timezone.utc),
        engine_versions=versions,
        chart_id=chart_id,
        research_project_id=research_project_id,
        generated_by=generated_by,
    )


def _extract_chart_summary(chart: D1Chart) -> ReportContent:
    moon = None
    if chart.planets:
        for p in chart.planets:
            if p.planet == "moon":
                moon = p.nakshatra
                break
    return ReportContent(
        section_type="chart_summary",
        data={
            "ayanamsa": chart.ayanamsa_system,
            "house_system": chart.house_system,
            "lagna_rashi": chart.ascendant.rashi if chart.ascendant else None,
            "lagna_degree": chart.ascendant.rashi_degree if chart.ascendant else None,
            "moon_nakshatra": moon,
        },
    )


def _extract_planets(chart: D1Chart) -> ReportContent:
    planets_data = []
    for p in chart.planets:
        planets_data.append({
            "name": p.planet,
            "rashi": p.rashi,
            "house": p.house_number,
            "dignity": p.dignity.value if p.dignity else None,
            "retrograde": p.is_retrograde,
        })
    return ReportContent(
        section_type="planets",
        data={"planets": planets_data, "count": len(planets_data)},
    )


def _extract_dimension_content(dim: dict[str, Any]) -> ReportContent:
    """
    One Event Analysis scope dimension (natal_promise, dasha_support,
    transit_influence, planetary_strength, yogas_activated, muhurta) as
    evidence-based ReportContent. `dim` is a pre-computed plain dict from
    EventAnalysisEngine's dimension evaluators — this function only shapes
    it into the report, per this module's "assembly only" contract.
    """
    sub_score = dim.get("sub_score")
    return ReportContent(section_type=dim["key"], data={
        "status": dim["status"],
        "sub_score_pct": round(sub_score * 100, 1) if sub_score is not None else None,
        "weight": dim["weight"],
        "points_earned": dim["points_earned"],
        "points_max": dim["points_max"],
        "evidence": dim["evidence"],
    })


def _extract_timeline_summary(timeline: Timeline) -> ReportContent:
    return ReportContent(
        section_type="timeline_summary",
        data={
            "total_events": timeline.summary.total_events,
            "date_range": [
                timeline.summary.date_range[0].isoformat(),
                timeline.summary.date_range[1].isoformat(),
            ],
            "events_per_category": timeline.summary.events_per_category,
        },
    )


def _extract_verification_summary(vf: VerificationFindings) -> ReportContent:
    strengths: dict[str, int] = {}
    for pair in vf.verification_pairs:
        key = pair.strength.value if hasattr(pair.strength, "value") else str(pair.strength)
        strengths[key] = strengths.get(key, 0) + 1
    return ReportContent(
        section_type="verification_summary",
        data={
            "total_pairs": vf.total_pairs,
            "total_rules": vf.total_rules_evaluated,
            "strengths": strengths,
        },
    )


def _extract_knowledge_citations(citations: tuple[KnowledgeSearchResult, ...]) -> ReportContent:
    return ReportContent(
        section_type="knowledge_citations",
        data={
            "citations": [
                {
                    "entity_type": c.entity_type,
                    "entity_id": str(c.entity_id),
                    "title": c.title,
                    "snippet": c.snippet,
                    "book_title": c.book_title,
                    "tradition": c.tradition,
                }
                for c in citations
            ],
            "count": len(citations),
        },
    )


def _extract_statistics_summary(stats: AggregateReport) -> ReportContent:
    dists = []
    for d in stats.distributions:
        dists.append({
            "label": d.label,
            "variable": d.variable,
            "total": d.total,
        })
    return ReportContent(
        section_type="statistics_summary",
        data={
            "sample_size": stats.metadata.sample_size,
            "distributions": dists,
        },
    )


class ReportEngine:
    """
    Assembles structured reports from existing domain objects.

    All methods are static — no state, no dependencies. Data is passed
    in, sections are extracted, reports are returned.
    """

    _ENGINE_VERSION = _ENGINE_VERSION

    @staticmethod
    def build_chart_report(
        chart_ref: D1Chart,
        *,
        timeline: Timeline | None = None,
        verification: VerificationFindings | None = None,
        stats: AggregateReport | None = None,
        citations: tuple[KnowledgeSearchResult, ...] | None = None,
        title: str = "Chart Analysis",
        subject_name: str = "Unnamed",
        generated_by: str | None = None,
        chart_id: uuid.UUID | None = None,
    ) -> ChartReport:
        """Full single-chart report with all available sections."""
        sections: list[ReportSection] = []
        order = 0

        sections.append(ReportSection(
            "Chart Summary", "chart_summary",
            _extract_chart_summary(chart_ref), order=order,
        ))
        order += 1

        sections.append(ReportSection(
            "Planetary Positions", "planets",
            _extract_planets(chart_ref), order=order,
        ))
        order += 1

        if timeline:
            sections.append(ReportSection(
                "Event Timeline", "timeline_summary",
                _extract_timeline_summary(timeline), order=order,
            ))
            order += 1

        if verification:
            sections.append(ReportSection(
                "Verification Results", "verification_summary",
                _extract_verification_summary(verification), order=order,
            ))
            order += 1

        if stats:
            sections.append(ReportSection(
                "Statistics", "statistics_summary",
                _extract_statistics_summary(stats), order=order,
            ))
            order += 1

        if citations:
            sections.append(ReportSection(
                "Knowledge Citations", "knowledge_citations",
                _extract_knowledge_citations(citations), order=order,
            ))
            order += 1

        metadata = _build_metadata(
            report_type="chart",
            chart_id=chart_id,
            generated_by=generated_by,
        )

        return ChartReport(
            metadata=metadata,
            title=title,
            subject_name=subject_name,
            sections=tuple(sections),
        )

    @staticmethod
    def build_research_report(
        project_id: uuid.UUID,
        snapshots: tuple[AstrologicalSnapshot, ...],
        *,
        stats: AggregateReport | None = None,
        title: str = "Research Analysis",
        generated_by: str | None = None,
    ) -> ResearchReport:
        """Snapshot collection report with statistics."""
        sections: list[ReportSection] = []

        # Snapshot overview section.
        overview = ReportContent(
            section_type="snapshot_overview",
            data={
                "snapshot_count": len(snapshots),
                "labels": [s.label for s in snapshots if s.label],
            },
        )
        sections.append(ReportSection(
            "Snapshot Overview", "snapshot_overview", overview, order=0,
        ))

        if stats:
            sections.append(ReportSection(
                "Statistics", "statistics_summary",
                _extract_statistics_summary(stats), order=1,
            ))

        metadata = _build_metadata(
            report_type="research",
            research_project_id=project_id,
            generated_by=generated_by,
        )

        return ResearchReport(
            metadata=metadata,
            title=title,
            snapshot_count=len(snapshots),
            sections=tuple(sections),
        )

    @staticmethod
    def build_comparison_report(
        charts: tuple[D1Chart, ...],
        labels: tuple[str, ...],
        *,
        title: str = "Chart Comparison",
        generated_by: str | None = None,
    ) -> ComparisonReport:
        """Side-by-side comparison of 2+ charts."""
        if len(charts) != len(labels):
            raise ValueError(
                f"Number of charts ({len(charts)}) must match labels ({len(labels)})"
            )
        if len(charts) < 2:
            raise ValueError("At least 2 charts required for comparison")

        sections: list[ReportSection] = []
        chart_ids: list[uuid.UUID] = []

        # Planet comparison section.
        planets_data: list[dict[str, Any]] = []
        for i, chart in enumerate(charts):
            for p in chart.planets:
                planets_data.append({
                    "chart_index": i,
                    "chart_label": labels[i],
                    "planet": p.planet,
                    "rashi": p.rashi,
                    "house": p.house_number,
                    "dignity": p.dignity.value if p.dignity else None,
                })

        sections.append(ReportSection(
            "Planet Comparison", "planet_comparison",
            ReportContent(section_type="planet_comparison", data={
                "planets": planets_data,
                "chart_count": len(charts),
            }),
            order=0,
        ))

        metadata = _build_metadata(
            report_type="comparison",
            generated_by=generated_by,
        )

        return ComparisonReport(
            metadata=metadata,
            title=title,
            chart_ids=tuple(chart_ids),
            chart_labels=labels,
            sections=tuple(sections),
        )

    @staticmethod
    def build_event_report(
        event_chart: D1Chart,
        *,
        natal_snapshot: NatalSnapshot,
        dimension_results: list[dict[str, Any]],
        event_record: EventAnalysisRecord,
        score: Optional[float] = None,
        generated_by: str | None = None,
    ) -> ChartReport:
        """
        Event Analysis report (muhurta consultation): the cast event D1 plus
        one evidence-based section per selected scope dimension
        (natal_promise, dasha_support, transit_influence, planetary_strength,
        yogas_activated, muhurta) and a score breakdown. Purely assembly —
        `dimension_results` is a list of pre-computed plain dicts from
        EventAnalysisEngine's dimension evaluators (one per scope flag the
        analysis was run with); this method only shapes them into sections,
        it does not compute or interpret anything.

        `natal_snapshot` is accepted for symmetry/provenance (the event is
        read against the natal frame) but is not emitted as its own section,
        keeping the report focused on the event moment itself.
        """
        sections: list[ReportSection] = []
        order = 0

        sections.append(ReportSection(
            "Event Chart", "chart_summary",
            _extract_chart_summary(event_chart), order=order,
        ))
        order += 1

        sections.append(ReportSection(
            "Event Planetary Positions", "planets",
            _extract_planets(event_chart), order=order,
        ))
        order += 1

        for dim in dimension_results:
            sections.append(ReportSection(
                dim["label"], dim["key"],
                _extract_dimension_content(dim), order=order,
            ))
            order += 1

        if dimension_results and score is not None:
            sections.append(ReportSection(
                "Score Breakdown", "score_breakdown",
                ReportContent(section_type="score_breakdown", data={
                    "overall_score": score,
                    "dimensions": [
                        {
                            "key": d["key"],
                            "label": d["label"],
                            "weight": d["weight"],
                            "points_earned": d["points_earned"],
                            "points_max": d["points_max"],
                            "status": d["status"],
                        }
                        for d in dimension_results
                    ],
                }),
                order=order,
            ))

        metadata = _build_metadata(
            report_type="event",
            chart_id=event_record.birth_chart_id,
            generated_by=generated_by,
        )

        return ChartReport(
            metadata=metadata,
            title=f"Event Analysis — {event_record.event_name}",
            subject_name=event_record.event_name,
            sections=tuple(sections),
        )
