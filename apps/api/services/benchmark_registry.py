"""
AstroOS — Benchmark Registry Service

Maintains canonical benchmark definitions and enforces cryptographic immutability
for locked benchmark corpora.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.benchmark_dataset import (
    BenchmarkDefinition,
    InclusionCriteria,
    LockedBenchmarkCorpus,
)
from apps.api.domain.research_calibration import (
    BirthDataConfidence,
    EventDateConfidence,
    EventVerification,
)


class ImmutableBenchmarkError(Exception):
    """Raised when attempting to mutate or overwrite a locked benchmark corpus."""
    pass


class BenchmarkRegistry:
    """Registry for benchmark problem definitions and immutable historical corpora."""

    def __init__(self) -> None:
        self._definitions: dict[str, BenchmarkDefinition] = {}
        self._locked_corpora: dict[tuple[str, str], LockedBenchmarkCorpus] = {}
        self._register_default_definitions()

    def clear_locked_corpora(self) -> None:
        """Clears locked corpora (used for test isolation)."""
        self._locked_corpora.clear()

    def _register_default_definitions(self) -> None:
        """Registers canonical benchmark specifications and quality policies."""
        if self._definitions:
            return

        career_def = BenchmarkDefinition(
            benchmark_id="BENCH-CAREER-001",
            name="Executive Career Elevations & Leadership Promotions",
            event_type="career",
            description="Canonical benchmark for testing timing of career promotions, corporate appointments, and status elevations.",
            inclusion_criteria=InclusionCriteria(
                min_birth_confidence=BirthDataConfidence.A,
                allowed_date_confidences=(EventDateConfidence.EXACT_DATE, EventDateConfidence.APPROX_WEEK),
                min_event_verification=EventVerification.PRIMARY_BIOGRAPHY,
            ),
            standard_tolerance_days=30,
        )

        marriage_def = BenchmarkDefinition(
            benchmark_id="BENCH-MARRIAGE-001",
            name="Matrimonial Crystallization Dates",
            event_type="marriage_timing",
            description="Canonical benchmark for testing matrimonial timing windows and vivaha yoga activation.",
            inclusion_criteria=InclusionCriteria(
                min_birth_confidence=BirthDataConfidence.A,
                allowed_date_confidences=(EventDateConfidence.EXACT_DATE,),
                min_event_verification=EventVerification.OFFICIAL_DOCUMENT,
            ),
            standard_tolerance_days=30,
        )

        wealth_def = BenchmarkDefinition(
            benchmark_id="BENCH-WEALTH-001",
            name="Major Financial Windfalls & Dhana Manifestations",
            event_type="wealth",
            description="Canonical benchmark for evaluating Dhana Yoga timing and wealth manifestation.",
            inclusion_criteria=InclusionCriteria(
                min_birth_confidence=BirthDataConfidence.B,
                allowed_date_confidences=(EventDateConfidence.EXACT_DATE, EventDateConfidence.APPROX_WEEK, EventDateConfidence.APPROX_MONTH),
                min_event_verification=EventVerification.SECONDARY_REPORT,
            ),
            standard_tolerance_days=45,
        )

        transit_def = BenchmarkDefinition(
            benchmark_id="BENCH-TRANSIT-001",
            name="Saturn Karmic Cycle Milestones",
            event_type="event_timing",
            description="Canonical benchmark for Sade Sati, Ashtama Shani, and Kantaka Shani trigger events.",
            inclusion_criteria=InclusionCriteria(
                min_birth_confidence=BirthDataConfidence.B,
                allowed_date_confidences=(EventDateConfidence.EXACT_DATE, EventDateConfidence.APPROX_WEEK),
                min_event_verification=EventVerification.SECONDARY_REPORT,
            ),
            standard_tolerance_days=30,
        )

        self._definitions[career_def.benchmark_id] = career_def
        self._definitions[marriage_def.benchmark_id] = marriage_def
        self._definitions[wealth_def.benchmark_id] = wealth_def
        self._definitions[transit_def.benchmark_id] = transit_def

    def register_definition(self, definition: BenchmarkDefinition) -> None:
        self._definitions[definition.benchmark_id] = definition

    def get_definition(self, benchmark_id: str) -> Optional[BenchmarkDefinition]:
        return self._definitions.get(benchmark_id)

    def list_definitions(self) -> tuple[BenchmarkDefinition, ...]:
        return tuple(self._definitions.values())

    def lock_corpus(self, corpus: LockedBenchmarkCorpus) -> None:
        """
        Locks a validated corpus with its computed content hash.
        Raises ImmutableBenchmarkError if (benchmark_id, version) already exists.
        """
        key = (corpus.benchmark_id, corpus.version)
        if key in self._locked_corpora:
            existing = self._locked_corpora[key]
            raise ImmutableBenchmarkError(
                f"Benchmark corpus '{corpus.benchmark_id}' v{corpus.version} is already locked (SHA-256: {existing.content_hash_sha256[:12]}...). "
                f"To update historical data, you must release a new version (e.g. v{corpus.version}.1)."
            )
        self._locked_corpora[key] = corpus

    def get_locked_corpus(self, benchmark_id: str, version: str = "1.0.0") -> Optional[LockedBenchmarkCorpus]:
        return self._locked_corpora.get((benchmark_id, version))

    def list_locked_corpora(self) -> tuple[LockedBenchmarkCorpus, ...]:
        return tuple(self._locked_corpora.values())