"""
AstroOS — Pattern Discovery Engine (Module 27, Phase 3b)

Finds statistically notable astrological patterns behind real-life events.

Input:  normalised ExtractedFeature rows (see feature_extraction.py).
Output: DiscoveredPattern objects grouping one or more dimension/value
        observations (e.g. mahadasha=Jupiter, transit=Sa_7th_house) that
        co-occur across research cases of a given KP Master event type.

Statistical Methodology & Architecture Framework:
------------------------------------------------
Classical Jyotish provides the hypotheses; AstroOS statistically evaluates
their observed associations in the available dataset across 5 distinct pillars:

1. Support / Occurrence Rate (k / n):
   Raw point-estimate frequency of cases exhibiting the feature.

2. Uncertainty / Wilson Confidence Interval (CI_lower):
   Quantifies proportion point-estimate uncertainty under small sample sizes (Wilson 1927).
   Note: Wilson lower bound quantifies estimation uncertainty; it is NOT a hypothesis significance test.

3. Effect Size / Base Rate Lift Ratio (p / p0):
   Effect size metric comparing observed event-type frequency (p) to global population baseline (p0).
   Note: Base Rate Lift (p / p0) is mathematically distinct from Odds Ratio ((a/b)/(c/d)).

4. Hypothesis Testing & Significance Complement (1 - p):
   One-tailed Z-test evaluating whether observed frequency exceeds global baseline chance
   expectation under null hypothesis assumptions.
   Screening threshold: p <= 0.10 (represented internally as Significance Complement 1 - p >= 0.90).
   Note: Configured threshold p <= 0.10 specifies screening alpha for a one-tailed test against global baseline,
   NOT a universal claim of empirical astrological validity.

5. Evidence Ranking / Composite Research Score:
   Weighted rank combining confidence lower bounds and effect size lift.

Approach (documented so results are reproducible):
  * Base rate (expected_by_chance) — for each (dimension, value), the
    share of ALL research cases in the dataset that exhibit it.
  * Event-type rate                 — the share of cases of the target event type.
  * Significance                    — the event-type rate is Wilson-shrunk (CI_lower)
    before testing via a one-tailed normal-approximation test (p-value computation).
  * Combinations                    — enumerate co-occurring pairs/triples.
  * Significance Complement         — per-dimension 1 - p_value complement score.
"""

from __future__ import annotations

import hashlib
import itertools
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional

from apps.api.domain.research_case import (
    DiscoveredPattern,
    ExtractedFeature,
    PatternDimension,
)

# Bumped by hand whenever the significance/combination logic below changes
# materially. Stamped onto every persisted DiscoveredPattern row so a pattern
# can be traced back to the exact algorithm that produced it.
ALGORITHM_VERSION = "1.5.2"

# Only dimension-values whose rate clears this share of cases are
# considered candidates for combination discovery.
MIN_FREQUENCY = 0.10
# Internal Significance Complement threshold (1 - p >= 0.90, corresponding to screening p <= 0.10 for one-tailed test)
MIN_SIGNIFICANCE = 0.90
# z used for the Wilson score lower bound that shrinks small-count rates
# before testing significance.
WILSON_Z = 1.0
# Cap on candidate pool before combinatorial enumeration.
MAX_CANDIDATES_PER_DIMENSION = 12
MAX_COMBO_LEVELS = 2  # pairs (2) and triples (3)

_PLANET_CODE_TO_NAME = {
    "Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury",
    "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn", "Ra": "Rahu", "Ke": "Ketu",
}
_PLANET_NAME_TOKENS = {name.lower(): name for name in _PLANET_CODE_TO_NAME.values()}

_EVENT_TYPE_DISPLAY_OVERRIDES = {
    "job_change": "Job Change",
    "child_birth": "Child Birth",
    "death_parent": "Death of Parent",
    "death_spouse": "Death of Spouse",
    "foreign_travel": "Foreign Travel",
}


def _display_event_type(event_type: str) -> str:
    return _EVENT_TYPE_DISPLAY_OVERRIDES.get(event_type, event_type.replace("_", " ").title())


def _title(raw: str) -> str:
    return raw.replace("_", " ").strip().title()


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _humanize_dimension(dimension: str, value: str) -> str:
    """Turn one raw (dimension, value) pair into a natural-language phrase
    for pattern descriptions — e.g. dimension="active yoga_Durudhara Yoga",
    value="True" becomes "Durudhara Yoga", not a literal
    "active yoga_Durudhara Yoga=True" dump of the internal feature name.
    """
    is_bool = value.strip().lower() in ("true", "false")
    present = value.strip().lower() == "true"

    if dimension.startswith("active yoga_"):
        yoga = dimension[len("active yoga_"):]
        return yoga if present else f"the absence of {yoga}"

    if dimension.startswith("transit_"):
        rest = dimension[len("transit_"):]
        planet_token, _, rashi_token = rest.partition("_")
        if rashi_token:
            planet = _PLANET_NAME_TOKENS.get(planet_token, planet_token.title())
            rashi = _title(rashi_token)
            return f"{planet} transiting {rashi}" if present else f"{planet} not transiting {rashi}"
        return _title(rest)

    if dimension.startswith("dasha_"):
        period_key = dimension[len("dasha_"):]
        period = {"mahadasha": "main", "antardasha": "sub", "pratyantar": "sub-sub"}.get(period_key, period_key)
        planet = _PLANET_CODE_TO_NAME.get(value, value)
        return f"a {planet} {period} dasha period"

    if dimension.startswith("house_"):
        key = dimension[len("house_"):]
        house_label = f"{_ordinal(int(key))} house" if key.isdigit() else f"{key} house"
        return f"the {house_label} lord in {value.strip()} dignity"

    if dimension.startswith("varga_"):
        return f"{_title(dimension[len('varga_'):])} showing {value}"

    if dimension.startswith("nakshatra activation_"):
        rest = dimension[len("nakshatra activation_"):]
        planet_token, _, nak_token = rest.partition("_")
        planet = _PLANET_NAME_TOKENS.get(planet_token, planet_token.title())
        nak = _title(nak_token)
        return f"{planet} in {nak} nakshatra" if present else f"{planet} not in {nak} nakshatra"

    if dimension.startswith("shadbala_"):
        planet_token = dimension[len("shadbala_"):]
        planet = _PLANET_CODE_TO_NAME.get(planet_token, planet_token)
        return f"{planet} shadbala of {value}"

    label = _title(dimension)
    if is_bool:
        return label if present else f"the absence of {label}"
    return f"{label} of {value}"


def _join_phrases(phrases: list[str]) -> str:
    if len(phrases) == 1:
        return phrases[0]
    if len(phrases) == 2:
        return f"{phrases[0]} and {phrases[1]}"
    return ", ".join(phrases[:-1]) + f", and {phrases[-1]}"


def _wilson_lower_bound(successes: int, n: int, z: float = WILSON_Z) -> float:
    """Lower bound of the Wilson score confidence interval (CI_lower) for binomial proportion (Wilson 1927).

    Distinction Note:
    - Wilson lower bound quantifies estimation uncertainty under small sample sizes.
    - It is NOT a hypothesis significance test (p-value).
    - It shrinks small-sample point estimates (e.g. 2/12) to a conservative lower bound.
    """
    if n <= 0:
        return 0.0
    p_hat = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p_hat + z2 / (2 * n)) / denom
    margin = (z / denom) * math.sqrt((p_hat * (1.0 - p_hat) / n) + z2 / (4 * n * n))
    return max(0.0, center - margin)


def _significance(observed: float, expected: float, n: int) -> float:
    """Significance Complement (1 - p_value) via one-tailed Z-test against global baseline.

    Calculates the Significance Complement (1 - p_value) under the null hypothesis
    that observed event rate does not exceed expected global baseline chance.
    Returns value in [0..1]. Configured threshold 0.90 corresponds to one-tailed p <= 0.10.
    """
    if n <= 1 or expected <= 0.0 or expected >= 1.0:
        return 0.0
    se = math.sqrt(expected * (1.0 - expected) / n)
    if se == 0.0:
        return 0.0
    z = (observed - expected) / se
    if z <= 0.0:
        return 0.0
    pvalue = 0.5 * math.erfc(z / math.sqrt(2.0))
    return max(0.0, min(1.0, 1.0 - pvalue))


@dataclass(frozen=True)
class _DimValue:
    """An internal dimension/value observation with aggregate stats."""

    dimension: str
    value: str
    cases: frozenset[str]
    frequency: float          # rate within the target event type
    expected_by_chance: float  # global base rate across all cases
    significance: float

    @property
    def count(self) -> int:
        return len(self.cases)


class PatternDiscoveryService:
    """Pure aggregation over ExtractedFeature rows, grouped by event type.

    ``min_significance``/``min_frequency``/``wilson_z`` default to the
    shared module constants (what every researcher sees on the
    dashboard). A caller MAY override them to run a personal, ephemeral
    "what-if" exploration with looser/stricter thresholds — see
    routers/research.py's /cases/patterns/explore endpoint, which never
    persists its results, so a personalised threshold can't change what
    anyone else sees. The formulas themselves (Wilson shrinkage, the
    significance test, combo joint-testing) are never parameterised —
    only where the bar is set.
    """

    def __init__(
        self,
        *,
        min_significance: float = MIN_SIGNIFICANCE,
        min_frequency: float = MIN_FREQUENCY,
        wilson_z: float = WILSON_Z,
    ) -> None:
        self._min_significance = min_significance
        self._min_frequency = min_frequency
        self._wilson_z = wilson_z

    def discover(
        self,
        features: list[ExtractedFeature],
        *,
        event_type: Optional[str] = None,
        top_combos: int = 5,
    ) -> list[DiscoveredPattern]:
        """Discover patterns over the feature list.

        If ``event_type`` is given, only patterns for that type are returned;
        otherwise patterns for every event type present are returned.
        """
        base_rates, by_type = self._build_stats(features)

        target_types = [event_type] if event_type is not None else list(by_type)
        patterns: list[DiscoveredPattern] = []
        for etype in target_types:
            stats = by_type.get(etype)
            if stats is not None:
                patterns.extend(
                    self._discover_for_type(etype, stats, base_rates, top_combos)
                )
        return patterns

    # ── internals ─────────────────────────────────────────────────────────

    def _build_stats(
        self,
        features: list[ExtractedFeature],
    ) -> tuple[dict[tuple[str, str], float], dict[str, "_TypeStats"]]:
        """Compute global base rates + per-event-type stats in one pass."""
        type_cases: dict[str, dict[str, set[tuple[str, str]]]] = defaultdict(
            lambda: defaultdict(set)
        )
        all_case_sets: dict[str, set[tuple[str, str]]] = defaultdict(set)

        for feat in features:
            pair = (feat.feature_name, str(feat.feature_value))
            type_cases[feat.event_type][feat.research_case_id].add(pair)
            all_case_sets[feat.research_case_id].add(pair)

        total_cases = len(all_case_sets)
        base_rates: dict[tuple[str, str], float] = {}
        dim_values_global: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        for case_id, pairs in all_case_sets.items():
            for dimension, value in pairs:
                dim_values_global[dimension][value].add(case_id)
        for dimension, value_map in dim_values_global.items():
            for value, case_set in value_map.items():
                base_rates[(dimension, value)] = (
                    len(case_set) / total_cases if total_cases else 0.0
                )

        by_type: dict[str, _TypeStats] = {}
        for etype, cases in type_cases.items():
            stats = _TypeStats(
                total_cases=len(cases),
                total_events=sum(len(v) for v in cases.values()),
            )
            dim_values: dict[str, dict[str, set[str]]] = defaultdict(
                lambda: defaultdict(set)
            )
            for case_id, pairs in cases.items():
                for dimension, value in pairs:
                    dim_values[dimension][value].add(case_id)
            for dimension, value_map in dim_values.items():
                for value, case_set in value_map.items():
                    freq = len(case_set) / stats.total_cases
                    base = base_rates.get((dimension, value), 0.0)
                    # Significance is tested against a Wilson-shrunk rate,
                    # not the raw point estimate — `frequency` below stays
                    # the raw rate (what's displayed to the user); only the
                    # significance gate uses the small-sample-aware one.
                    shrunk = _wilson_lower_bound(len(case_set), stats.total_cases, self._wilson_z)
                    stats.dim_values.append(
                        _DimValue(
                            dimension=dimension,
                            value=value,
                            cases=frozenset(case_set),
                            frequency=freq,
                            expected_by_chance=base,
                            significance=_significance(shrunk, base, stats.total_cases),
                        )
                    )
            by_type[etype] = stats
        return base_rates, by_type

    def _candidates(self, stats: "_TypeStats", max_total: int = 60) -> list[_DimValue]:
        """Significant, high-rate dimension-values, capped for enumeration."""
        pool = [
            dv
            for dv in stats.dim_values
            if dv.frequency >= self._min_frequency and dv.significance >= self._min_significance
        ]
        pool.sort(key=lambda dv: (dv.significance, dv.frequency), reverse=True)
        by_dim: dict[str, list[_DimValue]] = defaultdict(list)
        for dv in pool:
            if len(by_dim[dv.dimension]) < MAX_CANDIDATES_PER_DIMENSION:
                by_dim[dv.dimension].append(dv)
        flattened = [dv for group in by_dim.values() for dv in group]
        flattened.sort(key=lambda dv: (dv.significance, dv.frequency), reverse=True)
        return flattened[:max_total]

    @staticmethod
    def _dimension(dv: _DimValue) -> PatternDimension:
        return PatternDimension(
            dimension=dv.dimension,
            value=dv.value,
            frequency=round(dv.frequency, 4),
            count=dv.count,
            expected_by_chance=round(dv.expected_by_chance, 4),
            significance=round(dv.significance, 4),
        )

    @staticmethod
    def _make_pattern(
        *,
        event_type: str,
        dimensions: list[PatternDimension],
        sample_size: int,
        case_ids: frozenset[str] = frozenset(),
        joint_significance: Optional[float] = None,
    ) -> DiscoveredPattern:
        joined = "; ".join(f"{d.dimension}={d.value}" for d in dimensions)
        # event_type is part of the hash input, not just `joined`: two
        # different event types can independently discover the identical
        # dimension/value combo (e.g. "Neecha Bhanga Raja Yoga (Ketu)" can
        # be significant for both Marriage and Divorce). Without event_type
        # in the digest, both would collide on the same pattern_id, and
        # persist_discovery's upsert-by-pattern_id would silently overwrite
        # one event type's finding with the other's on every discovery run.
        digest = hashlib.sha1(f"{event_type}|{joined}".encode()).hexdigest()[:10]
        # For combos, confidence can't exceed the joint (intersection)
        # significance — otherwise multiplying two individually-strong but
        # jointly-thin dimensions' significance scores could overstate
        # confidence in a combination the joint sample barely supports.
        confidence = round(math.prod(d.significance for d in dimensions), 4)
        if joint_significance is not None:
            confidence = round(min(confidence, joint_significance), 4)
        top = max(dimensions, key=lambda d: d.frequency)

        event_label = _display_event_type(event_type)
        factor_text = _join_phrases([_humanize_dimension(d.dimension, d.value) for d in dimensions])
        description = (
            f"{event_label} events show a statistically significant link to {factor_text}: "
            f"{round(top.frequency * 100, 1)}% of {sample_size} studied cases exhibit this "
            f"pattern, compared with a {round(top.expected_by_chance * 100, 1)}% base rate."
        )
        return DiscoveredPattern(
            event_type=event_type,
            pattern_id=f"ptn-{digest}",
            dimensions=dimensions,
            sample_size=sample_size,
            confidence_score=confidence,
            description=description,
            supporting_case_ids=case_ids,
        )

    def _discover_for_type(
        self,
        event_type: str,
        stats: "_TypeStats",
        base_rates: dict[tuple[str, str], float],
        top_combos: int,
    ) -> list[DiscoveredPattern]:
        if stats.total_cases < 2:
            return []

        patterns: list[DiscoveredPattern] = []

        # ── Single-dimension patterns ─────────────────────────────────────
        singles = [
            dv
            for dv in stats.dim_values
            if dv.frequency >= self._min_frequency and dv.significance >= self._min_significance
        ]
        singles.sort(key=lambda dv: (dv.significance, dv.frequency), reverse=True)
        for dv in singles[:top_combos]:
            patterns.append(
                self._make_pattern(
                    event_type=event_type,
                    dimensions=[self._dimension(dv)],
                    sample_size=stats.total_cases,
                    case_ids=dv.cases,
                )
            )

        # ── Combination patterns ──────────────────────────────────────────
        # Each dimension in `candidates` already cleared the Wilson-corrected
        # single-dimension significance test, but the INTERSECTION of two or
        # three already-small groups can itself be tiny (e.g. two dimensions
        # each supported by 50 cases can intersect down to 3) — a bare
        # "joint rate beats independence expectation" comparison has no
        # awareness of that at all, so it's replaced with the same
        # Wilson-shrunk significance test used for single dimensions, tested
        # against the product-of-base-rates (independence) expectation.
        candidates = self._candidates(stats)
        if len(candidates) >= 2:
            combos: list[tuple[tuple[_DimValue, ...], frozenset[str], float]] = []
            for size in range(2, MAX_COMBO_LEVELS + 1):
                for combo in itertools.combinations(candidates, size):
                    dims = [c.dimension for c in combo]
                    if len(set(dims)) != len(dims):
                        continue  # never repeat the same dimension in one combo
                    joint_cases = frozenset.intersection(*(c.cases for c in combo))
                    expected_independent = math.prod(
                        base_rates.get((c.dimension, c.value), 0.0) for c in combo
                    )
                    joint_shrunk = _wilson_lower_bound(len(joint_cases), stats.total_cases, self._wilson_z)
                    joint_significance = _significance(
                        joint_shrunk, expected_independent, stats.total_cases
                    )
                    if joint_significance >= self._min_significance:
                        combos.append((combo, joint_cases, joint_significance))
            combos.sort(key=lambda item: item[2], reverse=True)
            for combo, joint_cases, joint_significance in combos[:top_combos]:
                patterns.append(
                    self._make_pattern(
                        event_type=event_type,
                        dimensions=[self._dimension(c) for c in combo],
                        sample_size=stats.total_cases,
                        case_ids=joint_cases,
                        joint_significance=joint_significance,
                    )
                )
        return patterns

    def test_hypothesis(
        self,
        features: list[ExtractedFeature],
        *,
        event_type: str,
        conditions: dict[str, str],
    ) -> tuple[int, int, float, list[dict]]:
        """Return (matching_cases, total_cases, proportion, supporting_events)."""
        filtered = [f for f in features if f.event_type == event_type]
        case_feats: dict[str, list[ExtractedFeature]] = defaultdict(list)
        for f in filtered:
            case_feats[f.research_case_id].append(f)

        matching: list[tuple[str, list[ExtractedFeature]]] = []
        for case_id, feats in case_feats.items():
            observed = {(f.feature_name, str(f.feature_value)) for f in feats}
            if all((dim, val) in observed for dim, val in conditions.items()):
                matching.append((case_id, feats))

        total_cases = len(case_feats)
        proportion = len(matching) / total_cases if total_cases else 0.0
        supporting_events = [
            {
                "research_case_id": case_id,
                "event_type": feats[0].event_type,
                "event_date": feats[0].event_date.isoformat(),
                "matched_features": [
                    {"dimension": f.feature_name, "value": f.feature_value}
                    for f in feats
                    if (f.feature_name, str(f.feature_value)) in conditions.items()
                ],
            }
            for case_id, feats in matching
        ]
        return len(matching), total_cases, proportion, supporting_events

    def find_contradicting_cases(
        self,
        features: list[ExtractedFeature],
        *,
        event_type: str,
        dimensions: list[PatternDimension],
    ) -> list[str]:
        """Case IDs exhibiting every pattern dimension/value pair, but not
        via an ``event_type`` snapshot — i.e. the astrological signature was
        present at some point for that person, but this specific event type
        did not occur then. Evidence against the pattern's predictive value.
        """
        conditions = {(d.dimension, d.value) for d in dimensions}
        other_feats: dict[str, list[ExtractedFeature]] = defaultdict(list)
        for f in features:
            if f.event_type != event_type:
                other_feats[f.research_case_id].append(f)

        contradicting: list[str] = []
        for case_id, feats in other_feats.items():
            observed = {(f.feature_name, str(f.feature_value)) for f in feats}
            if conditions.issubset(observed):
                contradicting.append(case_id)
        return contradicting


@dataclass
class _TypeStats:
    """All per-dimension stats for one event type."""

    total_cases: int
    total_events: int
    dim_values: list[_DimValue] = field(default_factory=list)
