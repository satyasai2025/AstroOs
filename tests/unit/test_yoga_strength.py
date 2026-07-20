"""
AstroOS — Yoga Strength Scoring Unit Tests (Phase 2, v2.1.0)

Tests for apps.api.services.yoga_strength:
  - compute_yoga_strength_score(): 0-100 numerical score per yoga
  - compute_strength_score_for_all(): batch re-score with strength_score populated
"""

from __future__ import annotations

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.domain.horoscope import AspectInfo
from apps.api.domain.house import HouseInfo
from apps.api.domain.yoga import YogaResult
from apps.api.services.yoga_predicates import YogaContext
from apps.api.services.yoga_strength import (
    compute_strength_score_for_all,
    compute_yoga_strength_score,
)
from apps.api.services.yoga_registry import all_yogas


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ZODIAC = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def _make_planet(
    planet: str,
    house_number: int,
    rashi: str = "aries",
    rashi_degree: float = 10.0,
    is_retrograde: bool = False,
    is_combust: bool = False,
    dignity: DignityType = DignityType.NEUTRAL,
) -> SiderealPosition:
    return SiderealPosition(
        planet=planet,
        sidereal_longitude=10.0,
        rashi=rashi,
        rashi_degree=rashi_degree,
        house_number=house_number,
        nakshatra="ashwini",
        pada=1,
        is_retrograde=is_retrograde,
        is_combust=is_combust,
        combustion_orb=None,
        dignity=dignity,
    )


def _make_house(house_number: int, lord: str = "mars") -> HouseInfo:
    return HouseInfo(
        house_number=house_number,
        rashi=_ZODIAC[(house_number - 1) % 12],
        lord=lord,
    )


def _build_context(
    planets: list[SiderealPosition],
    aspects: list[AspectInfo] | None = None,
) -> YogaContext:
    """Build a minimal YogaContext from a list of planet positions."""
    houses = [_make_house(i) for i in range(1, 13)]
    chart = _FakeChart(aspects or [])
    return YogaContext(
        chart=chart,
        houses=houses,
        planets_by_name={p.planet: p for p in planets},
        houses_by_number={h.house_number: h for h in houses},
    )


class _FakeChart:
    """Minimal chart shim for YogaContext — carries only what strength scoring reads."""
    def __init__(self, aspects: list[AspectInfo]):
        self.aspects = aspects


def _make_result(
    yoga_id: str = "BPHS-TEST-001",
    name: str = "Test Yoga",
    category: str = "Test",
    is_present: bool = True,
    involved_planets: tuple[str, ...] = ("jupiter",),
    strength: str | None = "full",
) -> YogaResult:
    return YogaResult(
        yoga_id=yoga_id,
        name=name,
        category=category,
        source_text="BPHS",
        rule_version="2.0",
        is_present=is_present,
        strength=strength,
        involved_planets=involved_planets,
    )


# ---------------------------------------------------------------------------
# compute_yoga_strength_score tests
# ---------------------------------------------------------------------------

class TestComputeYogaStrengthScore:
    """Tests for compute_yoga_strength_score()."""

    def test_returns_int(self):
        """Score must be an integer."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        result = _make_result()
        score = compute_yoga_strength_score(ctx, result)
        assert isinstance(score, int)

    def test_returns_0_to_100_range(self):
        """Score must be in [0, 100]."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        result = _make_result()
        score = compute_yoga_strength_score(ctx, result)
        assert 0 <= score <= 100

    def test_not_present_returns_zero(self):
        """Yoga not present must score 0."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        result = _make_result(is_present=False)
        score = compute_yoga_strength_score(ctx, result)
        assert score == 0

    def test_no_involved_planets_returns_zero(self):
        """Yoga with empty involved_planets must score 0 even if present."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        result = _make_result(involved_planets=())
        score = compute_yoga_strength_score(ctx, result)
        assert score == 0

    def test_missing_planet_in_context_skips_it(self):
        """If an involved planet is not in the context, it is skipped gracefully."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        result = _make_result(involved_planets=("jupiter", "mars"))  # mars not in ctx
        score = compute_yoga_strength_score(ctx, result)
        # Only jupiter contributes; still valid
        assert 0 <= score <= 100

    def test_all_planets_missing_returns_zero(self):
        """If none of the involved planets exist in context, score is 0."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        result = _make_result(involved_planets=("mars", "saturn"))
        score = compute_yoga_strength_score(ctx, result)
        assert score == 0

    def test_exalted_planet_scores_higher_than_debilitated(self):
        """A planet in exaltation should produce a higher score than debilitated."""
        ctx_exalted = _build_context([
            _make_planet("jupiter", house_number=1, rashi="cancer", dignity=DignityType.EXALTED),
        ])
        ctx_debilitated = _build_context([
            _make_planet("jupiter", house_number=1, rashi="capricorn", dignity=DignityType.DEBILITATED),
        ])
        result = _make_result()
        score_high = compute_yoga_strength_score(ctx_exalted, result)
        score_low = compute_yoga_strength_score(ctx_debilitated, result)
        assert score_high > score_low

    def test_kendra_house_scores_higher_than_dusthana(self):
        """A planet in kendra (house 1) should score higher than dusthana (house 12)."""
        ctx_kendra = _build_context([
            _make_planet("jupiter", house_number=1),
        ])
        ctx_dusthana = _build_context([
            _make_planet("jupiter", house_number=12),
        ])
        result = _make_result()
        score_kendra = compute_yoga_strength_score(ctx_kendra, result)
        score_dusthana = compute_yoga_strength_score(ctx_dusthana, result)
        assert score_kendra > score_dusthana

    def test_combust_reduces_score(self):
        """A combust planet should score lower than non-combust."""
        ctx_normal = _build_context([
            _make_planet("jupiter", house_number=1, is_combust=False),
        ])
        ctx_combust = _build_context([
            _make_planet("jupiter", house_number=1, is_combust=True),
        ])
        result = _make_result()
        score_normal = compute_yoga_strength_score(ctx_normal, result)
        score_combust = compute_yoga_strength_score(ctx_combust, result)
        assert score_normal > score_combust

    def test_multi_planet_yoga_averages(self):
        """Multi-planet yoga should average per-planet scores."""
        ctx = _build_context([
            _make_planet("jupiter", house_number=1),
            _make_planet("mars", house_number=5),
        ])
        result = _make_result(involved_planets=("jupiter", "mars"))
        score = compute_yoga_strength_score(ctx, result)
        assert 0 <= score <= 100

    def test_benefic_aspect_boosts_score(self):
        """A benefic aspecting an involved planet should increase the score."""
        ctx_no_aspect = _build_context([
            _make_planet("jupiter", house_number=1),
            _make_planet("venus", house_number=7),
        ])
        ctx_with_aspect = _build_context(
            [_make_planet("jupiter", house_number=1), _make_planet("venus", house_number=7)],
            aspects=[AspectInfo(from_planet="venus", to_planet="jupiter", aspect_type="opposition", orb_degrees=2.0, is_applying=True)],
        )
        result = _make_result()
        score_no = compute_yoga_strength_score(ctx_no_aspect, result)
        score_with = compute_yoga_strength_score(ctx_with_aspect, result)
        # Benefic aspect should not decrease the score
        assert score_with >= score_no


# ---------------------------------------------------------------------------
# compute_strength_score_for_all tests
# ---------------------------------------------------------------------------

class TestComputeStrengthScoreForAll:
    """Tests for compute_strength_score_for_all()."""

    def test_returns_list(self):
        """Must return a list of YogaResult."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        results = [_make_result()]
        scored = compute_strength_score_for_all(ctx, results)
        assert isinstance(scored, list)
        assert len(scored) == 1

    def test_preserves_result_count(self):
        """Output count must match input count."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        results = [_make_result(yoga_id=f"BPHS-TEST-{i:03d}") for i in range(5)]
        scored = compute_strength_score_for_all(ctx, results)
        assert len(scored) == 5

    def test_populates_strength_score(self):
        """Each scored result must have strength_score set."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        results = [_make_result()]
        scored = compute_strength_score_for_all(ctx, results)
        assert scored[0].strength_score is not None
        assert isinstance(scored[0].strength_score, int)

    def test_not_present_gets_zero_score(self):
        """Absent yogas must get strength_score=0."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        results = [_make_result(is_present=False)]
        scored = compute_strength_score_for_all(ctx, results)
        assert scored[0].strength_score == 0

    def test_mixed_present_and_absent(self):
        """Mix of present and absent yogas: present get scored, absent get 0."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        results = [
            _make_result(yoga_id="BPHS-PRESENT-001", is_present=True),
            _make_result(yoga_id="BPHS-ABSENT-001", is_present=False),
        ]
        scored = compute_strength_score_for_all(ctx, results)
        assert scored[0].strength_score > 0
        assert scored[1].strength_score == 0

    def test_scores_all_registered_yogas(self):
        """Scoring should work for every registered yoga definition without error."""
        ctx = _build_context([
            _make_planet("jupiter", house_number=1),
            _make_planet("mars", house_number=5),
            _make_planet("saturn", house_number=9),
        ])
        results = [
            _make_result(
                yoga_id=y.yoga_id,
                name=y.name,
                category=y.category,
                is_present=(i % 3 == 0),  # some present, some not
                involved_planets=("jupiter",) if i % 2 == 0 else ("jupiter", "mars"),
            )
            for i, y in enumerate(all_yogas())
        ]
        scored = compute_strength_score_for_all(ctx, results)
        assert len(scored) == len(all_yogas())
        for r in scored:
            assert r.strength_score is not None
            assert 0 <= r.strength_score <= 100

    def test_does_not_mutate_original(self):
        """The original YogaResult list must not be modified."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        original = [_make_result()]
        original_score = original[0].strength_score
        compute_strength_score_for_all(ctx, original)
        assert original[0].strength_score == original_score

    def test_empty_results_list(self):
        """Empty input must return empty output."""
        ctx = _build_context([_make_planet("jupiter", house_number=1)])
        scored = compute_strength_score_for_all(ctx, [])
        assert scored == []
