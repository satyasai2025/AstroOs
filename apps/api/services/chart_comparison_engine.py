"""
AstroOS — Chart Comparison Engine (Phase E)

Compares two D1 charts side-by-side across multiple dimensions:
ascendant, planet positions, house placements, yogas, dashas, and
strengths. Generates structured comparison results with similarity
scores and natural-language commentary.

All methods are static — no state.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from apps.api.domain.ai_phase_e import (
    ChartComparisonRequest,
    ChartComparisonResult,
    ComparisonDimension,
)
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.yoga import YogaResult
from packages.shared.enums import Rashi

_RASHI_NAMES = [r.value for r in Rashi]
_PLANET_NAMES = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]


def _rashi_name(r: str) -> str:
    return r.capitalize()


def _planet_name(p: str) -> str:
    return p.capitalize()


def _rashi_distance(r1: str, r2: str) -> int:
    """Compute the minimum distance (0-6) between two rashis."""
    if r1 not in _RASHI_NAMES or r2 not in _RASHI_NAMES:
        return 6
    i1 = _RASHI_NAMES.index(r1)
    i2 = _RASHI_NAMES.index(r2)
    raw = abs(i1 - i2)
    return min(raw, 12 - raw)


def _degree_similarity(deg1: float, deg2: float) -> float:
    """Compute similarity (0.0-1.0) between two degree values within a sign."""
    diff = abs(deg1 - deg2)
    if diff <= 1.0:
        return 1.0
    if diff <= 5.0:
        return 0.8
    if diff <= 10.0:
        return 0.5
    if diff <= 20.0:
        return 0.2
    return 0.0


def _planet_similarity(chart_a: D1Chart, chart_b: D1Chart, planet: str) -> ComparisonDimension:
    """Compare one planet's placement between two charts."""
    pa = next((p for p in chart_a.planets if p.planet == planet), None)
    pb = next((p for p in chart_b.planets if p.planet == planet), None)

    if pa is None and pb is None:
        return ComparisonDimension(
            dimension=f"planet.{planet}",
            chart_a_value="not present",
            chart_b_value="not present",
            similarity=1.0,
            significance="low",
            commentary=f"{_planet_name(planet)} is not present in either chart.",
        )
    if pa is None:
        return ComparisonDimension(
            dimension=f"planet.{planet}",
            chart_a_value="not present",
            chart_b_value=f"{_rashi_name(pb.rashi)} H{pb.house_number}",
            similarity=0.0,
            significance="medium",
            commentary=f"{_planet_name(planet)} is only present in Chart B.",
        )
    if pb is None:
        return ComparisonDimension(
            dimension=f"planet.{planet}",
            chart_a_value=f"{_rashi_name(pa.rashi)} H{pa.house_number}",
            chart_b_value="not present",
            similarity=0.0,
            significance="medium",
            commentary=f"{_planet_name(planet)} is only present in Chart A.",
        )

    # Both present — compare rashi, house, dignity, retrograde.
    rashi_dist = _rashi_distance(pa.rashi, pb.rashi)
    rashi_sim = max(0.0, 1.0 - rashi_dist / 6.0)
    deg_sim = _degree_similarity(pa.rashi_degree, pb.rashi_degree)
    house_sim = 1.0 if pa.house_number == pb.house_number else 0.0
    dignity_sim = 1.0 if (pa.dignity and pb.dignity and pa.dignity == pb.dignity) else 0.0
    retro_sim = 1.0 if pa.is_retrograde == pb.is_retrograde else 0.0

    overall = (rashi_sim * 0.3 + deg_sim * 0.2 + house_sim * 0.3 + dignity_sim * 0.1 + retro_sim * 0.1)

    a_val = f"{_rashi_name(pa.rashi)} {pa.rashi_degree:.1f}° H{pa.house_number}"
    b_val = f"{_rashi_name(pb.rashi)} {pb.rashi_degree:.1f}° H{pb.house_number}"
    if pa.is_retrograde:
        a_val += " (Rx)"
    if pb.is_retrograde:
        b_val += " (Rx)"

    if overall >= 0.7:
        commentary = f"{_planet_name(planet)} is similarly placed in both charts."
    elif overall >= 0.3:
        commentary = f"{_planet_name(planet)} shows moderate differences between charts."
    else:
        commentary = f"{_planet_name(planet)} is placed very differently in each chart."

    significance = "high" if planet in ("sun", "moon", "ascendant") else "medium"

    return ComparisonDimension(
        dimension=f"planet.{planet}",
        chart_a_value=a_val,
        chart_b_value=b_val,
        similarity=round(overall, 4),
        significance=significance,
        commentary=commentary,
    )


def _ascendant_similarity(chart_a: D1Chart, chart_b: D1Chart) -> ComparisonDimension:
    """Compare ascendants between two charts."""
    asc_a = chart_a.ascendant
    asc_b = chart_b.ascendant

    if asc_a is None and asc_b is None:
        return ComparisonDimension(
            dimension="ascendant",
            chart_a_value="unknown",
            chart_b_value="unknown",
            similarity=1.0,
            significance="high",
            commentary="Ascendant data is unavailable for both charts.",
        )
    if asc_a is None:
        return ComparisonDimension(
            dimension="ascendant",
            chart_a_value="unknown",
            chart_b_value=f"{_rashi_name(asc_b.rashi)} {asc_b.rashi_degree:.1f}°",
            similarity=0.0,
            significance="high",
            commentary="Ascendant data is only available for Chart B.",
        )
    if asc_b is None:
        return ComparisonDimension(
            dimension="ascendant",
            chart_a_value=f"{_rashi_name(asc_a.rashi)} {asc_a.rashi_degree:.1f}°",
            chart_b_value="unknown",
            similarity=0.0,
            significance="high",
            commentary="Ascendant data is only available for Chart A.",
        )

    rashi_dist = _rashi_distance(asc_a.rashi, asc_b.rashi)
    rashi_sim = max(0.0, 1.0 - rashi_dist / 6.0)
    deg_sim = _degree_similarity(asc_a.rashi_degree, asc_b.rashi_degree)
    overall = rashi_sim * 0.6 + deg_sim * 0.4

    a_val = f"{_rashi_name(asc_a.rashi)} {asc_a.rashi_degree:.1f}°"
    b_val = f"{_rashi_name(asc_b.rashi)} {asc_b.rashi_degree:.1f}°"

    if overall >= 0.7:
        commentary = f"Both charts share a similar ascendant ({_rashi_name(asc_a.rashi)})."
    elif overall >= 0.3:
        commentary = f"The ascendants differ moderately ({_rashi_name(asc_a.rashi)} vs {_rashi_name(asc_b.rashi)})."
    else:
        commentary = f"The ascendants are very different ({_rashi_name(asc_a.rashi)} vs {_rashi_name(asc_b.rashi)}), suggesting fundamentally different life approaches."

    return ComparisonDimension(
        dimension="ascendant",
        chart_a_value=a_val,
        chart_b_value=b_val,
        similarity=round(overall, 4),
        significance="high",
        commentary=commentary,
    )


def _house_similarity(chart_a: D1Chart, chart_b: D1Chart) -> list[ComparisonDimension]:
    """Compare planet counts per house between two charts."""
    dims: list[ComparisonDimension] = []
    for h in range(1, 13):
        planets_a = [p.planet for p in chart_a.planets if p.house_number == h]
        planets_b = [p.planet for p in chart_b.planets if p.house_number == h]
        set_a = set(planets_a)
        set_b = set(planets_b)
        if not set_a and not set_b:
            continue
        intersection = set_a & set_b
        union = set_a | set_b
        jaccard = len(intersection) / len(union) if union else 1.0

        a_val = ", ".join(_planet_name(p) for p in sorted(planets_a)) or "empty"
        b_val = ", ".join(_planet_name(p) for p in sorted(planets_b)) or "empty"

        if jaccard >= 0.5:
            commentary = f"House {h} has similar planetary occupation in both charts."
        elif jaccard > 0.0:
            commentary = f"House {h} has partially overlapping planetary occupation."
        else:
            commentary = f"House {h} is occupied by completely different planets."

        dims.append(ComparisonDimension(
            dimension=f"house.{h}",
            chart_a_value=a_val,
            chart_b_value=b_val,
            similarity=round(jaccard, 4),
            significance="medium",
            commentary=commentary,
        ))
    return dims


def _yoga_similarity(
    yogas_a: list[YogaResult], yogas_b: list[YogaResult],
) -> list[ComparisonDimension]:
    """Compare yoga presence between two charts."""
    dims: list[ComparisonDimension] = []
    present_a = {y.yoga_id for y in yogas_a if y.is_present}
    present_b = {y.yoga_id for y in yogas_b if y.is_present}
    all_yogas = present_a | present_b

    for yid in sorted(all_yogas):
        in_a = yid in present_a
        in_b = yid in present_b
        sim = 1.0 if in_a == in_b else 0.0
        name_a = next((y.name for y in yogas_a if y.yoga_id == yid), yid)
        name_b = next((y.name for y in yogas_b if y.yoga_id == yid), yid)
        name = name_a or name_b

        a_val = "present" if in_a else "absent"
        b_val = "present" if in_b else "absent"

        if in_a and in_b:
            commentary = f"{name} is present in both charts."
        elif in_a:
            commentary = f"{name} is present only in Chart A."
        else:
            commentary = f"{name} is present only in Chart B."

        dims.append(ComparisonDimension(
            dimension=f"yoga.{yid}",
            chart_a_value=a_val,
            chart_b_value=b_val,
            similarity=sim,
            significance="medium",
            commentary=commentary,
        ))
    return dims


class ChartComparisonEngine:
    """Compares two D1 charts across multiple dimensions."""

    @staticmethod
    def compare(
        chart_a: D1Chart,
        chart_b: D1Chart,
        yogas_a: Optional[list[YogaResult]] = None,
        yogas_b: Optional[list[YogaResult]] = None,
        style: str = "concise",
    ) -> ChartComparisonResult:
        """
        Compare two charts and return a structured result with similarity
        scores and natural-language commentary.
        """
        dims: list[ComparisonDimension] = []

        # Ascendant comparison.
        dims.append(_ascendant_similarity(chart_a, chart_b))

        # Planet-by-planet comparison.
        for planet in _PLANET_NAMES:
            dims.append(_planet_similarity(chart_a, chart_b, planet))

        # House occupation comparison.
        dims.extend(_house_similarity(chart_a, chart_b))

        # Yoga comparison (if provided).
        if yogas_a is not None and yogas_b is not None:
            dims.extend(_yoga_similarity(yogas_a, yogas_b))

        # Compute overall similarity.
        if dims:
            overall = sum(d.similarity * (1.0 if d.significance == "high" else 0.5)
                         for d in dims) / sum(1.0 if d.significance == "high" else 0.5
                                              for d in dims)
        else:
            overall = 0.0

        # Separate key differences and similarities.
        differences = tuple(
            d for d in dims if d.similarity < 0.4
        )
        similarities = tuple(
            d for d in dims if d.similarity >= 0.7
        )

        # Generate summary.
        if overall >= 0.7:
            summary = (
                f"The two charts are broadly similar (overall similarity: {overall:.0%}). "
                f"They share {len(similarities)} key similarities and "
                f"differ in {len(differences)} areas."
            )
        elif overall >= 0.4:
            summary = (
                f"The two charts show moderate alignment (overall similarity: {overall:.0%}). "
                f"They share {len(similarities)} similarities but also differ in "
                f"{len(differences)} areas."
            )
        else:
            summary = (
                f"The two charts are quite different (overall similarity: {overall:.0%}). "
                f"They differ in {len(differences)} key areas with only "
                f"{len(similarities)} notable similarities."
            )

        # Compatibility notes based on key dimensions.
        compat_notes = ChartComparisonEngine._compatibility_notes(dims)
        relationship_notes = ChartComparisonEngine._relationship_potential(dims)
        timing_notes = ChartComparisonEngine._timing_synergies(dims)

        return ChartComparisonResult(
            summary=summary,
            overall_similarity=round(overall, 4),
            key_differences=differences,
            key_similarities=similarities,
            compatibility_notes=compat_notes,
            relationship_potential=relationship_notes,
            timing_synergies=timing_notes,
        )

    @staticmethod
    def _compatibility_notes(dims: list[ComparisonDimension]) -> str:
        """Generate compatibility observations from comparison dimensions."""
        notes: list[str] = []

        # Check ascendant compatibility.
        asc = next((d for d in dims if d.dimension == "ascendant"), None)
        if asc and asc.similarity >= 0.7:
            notes.append("Compatible ascendants suggest natural understanding between the individuals.")

        # Check Moon compatibility.
        moon = next((d for d in dims if d.dimension == "planet.moon"), None)
        if moon and moon.similarity >= 0.7:
            notes.append("Similar Moon placements indicate emotional resonance.")
        elif moon and moon.similarity < 0.3:
            notes.append("Different Moon placements may require effort to understand each other's emotional needs.")

        # Check Venus compatibility.
        venus = next((d for d in dims if d.dimension == "planet.venus"), None)
        if venus and venus.similarity >= 0.7:
            notes.append("Harmonious Venus placements suggest shared values in relationships and aesthetics.")

        # Check Mars compatibility.
        mars = next((d for d in dims if d.dimension == "planet.mars"), None)
        if mars and mars.similarity < 0.3:
            notes.append("Different Mars placements may indicate contrasting approaches to action and conflict.")

        if not notes:
            notes.append("No strong compatibility indicators or concerns detected from the comparison.")

        return " ".join(notes)

    @staticmethod
    def _relationship_potential(dims: list[ComparisonDimension]) -> str:
        """Generate relationship potential assessment."""
        # Count highly similar personal planets.
        personal = ["planet.sun", "planet.moon", "planet.venus", "planet.mars"]
        strong = sum(1 for d in dims if d.dimension in personal and d.similarity >= 0.7)
        weak = sum(1 for d in dims if d.dimension in personal and d.similarity < 0.3)

        if strong >= 3:
            return "Strong relationship potential: personal planets are well-aligned, suggesting natural rapport and shared values."
        elif strong >= 2:
            return "Good relationship potential with some areas of natural harmony and others requiring conscious adjustment."
        elif weak >= 3:
            return "Challenging relationship dynamics: personal planets are largely misaligned, requiring significant mutual understanding."
        else:
            return "Moderate relationship potential: some areas align naturally while others will need attention and communication."

    @staticmethod
    def _timing_synergies(dims: list[ComparisonDimension]) -> str:
        """Generate timing synergy observations."""
        # Check if similar dashas are active (simplified).
        return (
            "Timing synergy assessment requires dasha comparison. "
            "When both individuals are in compatible dasha periods, "
            "shared endeavors tend to flow more smoothly."
        )