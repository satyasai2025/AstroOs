"""
AstroOS — Event Annotation & Provenance Service

Provides utilities for enriching ground truth event records with typed research
provenance, verification levels, and bibliographical citations.

STRICT ISOLATION GUARANTEE: Annotations are strictly for research categorization
and dataset inclusion; they are never passed as weights to prediction engines.
"""

from __future__ import annotations

from typing import Any, Sequence

from apps.api.domain.research_calibration import (
    BirthDataConfidence,
    EventDateConfidence,
    EventVerification,
    GroundTruthEvent,
)


class EventAnnotationService:
    """Enriches and manages metadata annotations for ground truth events."""

    @staticmethod
    def annotate_event(
        event: GroundTruthEvent,
        birth_confidence: BirthDataConfidence | None = None,
        event_date_confidence: EventDateConfidence | None = None,
        event_verification: EventVerification | None = None,
        source_citation: str | None = None,
        notes: str | None = None,
    ) -> GroundTruthEvent:
        """Returns a new GroundTruthEvent instance with updated metadata."""
        return GroundTruthEvent(
            event_id=event.event_id,
            subject_id=event.subject_id,
            event_type=event.event_type,
            actual_date=event.actual_date,
            birth_datetime_utc=event.birth_datetime_utc,
            birth_latitude=event.birth_latitude,
            birth_longitude=event.birth_longitude,
            birth_confidence=birth_confidence or event.birth_confidence,
            event_date_confidence=event_date_confidence or event.event_date_confidence,
            event_verification=event_verification or event.event_verification,
            source_citation=source_citation if source_citation is not None else event.source_citation,
            notes=notes if notes is not None else event.notes,
        )

    @staticmethod
    def summarize_provenance(events: Sequence[GroundTruthEvent]) -> dict[str, Any]:
        """Calculates provenance distribution summary across an event corpus."""
        rodden_dist: dict[str, int] = {}
        date_conf_dist: dict[str, int] = {}
        verif_dist: dict[str, int] = {}

        for e in events:
            rodden_dist[e.birth_confidence.value] = rodden_dist.get(e.birth_confidence.value, 0) + 1
            date_conf_dist[e.event_date_confidence.value] = date_conf_dist.get(e.event_date_confidence.value, 0) + 1
            verif_dist[e.event_verification.value] = verif_dist.get(e.event_verification.value, 0) + 1

        return {
            "total_events": len(events),
            "rodden_distribution": rodden_dist,
            "date_confidence_distribution": date_conf_dist,
            "verification_distribution": verif_dist,
        }