"""
AstroOS — Quality Scorer

Implements the Research Data Office's quality scoring methodology (RDO §3).
Six weighted dimensions: completeness, accuracy, consistency, coverage,
timeliness, provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class QualityDimension:
    """A single quality dimension score."""
    name: str
    weight: float
    score: float  # 0.0-1.0
    details: str = ""


@dataclass
class QualityAssessment:
    """Complete quality assessment for a dataset."""
    dimensions: List[QualityDimension] = field(default_factory=list)
    overall_score: float = 0.0
    quality_tier: str = "F"
    record_count: int = 0
    field_count: int = 0
    completeness_pct: float = 0.0
    missing_fields: List[str] = field(default_factory=list)
    duplicate_count: int = 0
    duplicate_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality_score": round(self.overall_score, 2),
            "quality_tier": self.quality_tier,
            "dimension_scores": {d.name: round(d.score, 2) for d in self.dimensions},
            "record_count": self.record_count,
            "field_count": self.field_count,
            "completeness_pct": round(self.completeness_pct, 1),
            "missing_fields": self.missing_fields,
            "duplicate_count": self.duplicate_count,
            "duplicate_pct": round(self.duplicate_pct, 1),
        }


class QualityScorer:
    """Computes quality scores per RDO §3 methodology.

    Scoring rubric (simplified):
    - Completeness (0.25): record presence + field population
    - Accuracy (0.25): validation pass rate
    - Consistency (0.15): consistency rule pass rate
    - Coverage (0.15): coverage of expected scope
    - Timeliness (0.10): freshness (always 1.0 for initial import)
    - Provenance (0.10): source attribution quality
    """

    WEIGHTS = {
        "completeness": 0.25,
        "accuracy": 0.25,
        "consistency": 0.15,
        "coverage": 0.15,
        "timeliness": 0.10,
        "provenance": 0.10,
    }

    TIER_THRESHOLDS = [
        (0.90, "A", "Research Grade"),
        (0.75, "B", "Production Grade"),
        (0.50, "C", "Exploratory Grade"),
        (0.25, "D", "Draft Grade"),
        (0.00, "F", "Rejected"),
    ]

    def score(
        self,
        records: List[Dict[str, Any]],
        required_fields: List[str],
        all_fields: List[str],
        validation_pass_rate: float,
        consistency_pass_rate: float = 1.0,
        coverage_pct: float = 100.0,
        timeliness_score: float = 1.0,
        provenance_score: float = 1.0,
        total_expected_records: Optional[int] = None,
    ) -> QualityAssessment:
        """Compute quality score from components."""
        assessment = QualityAssessment()
        assessment.record_count = len(records)
        assessment.field_count = len(all_fields)

        # Completeness: field population + record presence
        field_population = self._compute_field_population(records, all_fields)
        record_presence = len(records) / total_expected_records if total_expected_records else 1.0
        record_presence = min(record_presence, 1.0)
        completeness = field_population * 0.5 + record_presence * 0.5
        assessment.dimensions.append(QualityDimension(
            name="completeness",
            weight=self.WEIGHTS["completeness"],
            score=completeness,
        ))

        # Accuracy: validation pass rate
        assessment.dimensions.append(QualityDimension(
            name="accuracy",
            weight=self.WEIGHTS["accuracy"],
            score=validation_pass_rate,
        ))

        # Consistency
        assessment.dimensions.append(QualityDimension(
            name="consistency",
            weight=self.WEIGHTS["consistency"],
            score=consistency_pass_rate,
        ))

        # Coverage
        coverage = coverage_pct / 100.0
        assessment.dimensions.append(QualityDimension(
            name="coverage",
            weight=self.WEIGHTS["coverage"],
            score=coverage,
        ))

        # Timeliness
        assessment.dimensions.append(QualityDimension(
            name="timeliness",
            weight=self.WEIGHTS["timeliness"],
            score=timeliness_score,
        ))

        # Provenance
        assessment.dimensions.append(QualityDimension(
            name="provenance",
            weight=self.WEIGHTS["provenance"],
            score=provenance_score,
        ))

        # Overall score
        assessment.overall_score = sum(d.weight * d.score for d in assessment.dimensions)

        # Quality tier
        for threshold, tier, label in self.TIER_THRESHOLDS:
            if assessment.overall_score >= threshold:
                assessment.quality_tier = tier
                break

        # Missing fields
        assessment.missing_fields = self._compute_missing_fields(records, all_fields)
        assessment.completeness_pct = round(field_population * 100, 1)

        return assessment

    def _compute_field_population(self, records: List[Dict[str, Any]], all_fields: List[str]) -> float:
        """Compute average non-null field population across all records."""
        if not records or not all_fields:
            return 0.0
        total_cells = len(records) * len(all_fields)
        filled_cells = sum(
            1 for r in records for f in all_fields if r.get(f) is not None
        )
        return filled_cells / total_cells

    def _compute_missing_fields(self, records: List[Dict[str, Any]], all_fields: List[str]) -> List[str]:
        """Identify fields where >50% of records have null values."""
        missing = []
        if not records:
            return missing
        threshold = len(records) * 0.5
        for f in all_fields:
            null_count = sum(1 for r in records if r.get(f) is None)
            if null_count > threshold:
                missing.append(f)
        return missing
