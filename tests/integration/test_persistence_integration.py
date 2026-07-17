"""
AstroOS — Persistence Integration Tests

End-to-end coverage of the new persistence flow:

    Input -> Swiss Ephemeris -> Calculation -> Persist to PostgreSQL -> Response

Unlike tests/integration/test_ephemeris_wrapper_concurrency.py, these tests
do not require live PostgreSQL or real .se1 data files — they run
EphemerisWrapper in its Moshier fallback mode (same pattern already used by
tests/unit/test_dasha_engine.py and test_horoscope_engine.py) against the
shared in-memory SQLite fixture from tests/conftest.py. They are placed
under tests/integration/ because they exercise the full engine -> repository
-> database round trip end-to-end, rather than one repository in isolation
— not because they need live infrastructure. They are NOT marked
pytest.mark.integration (that marker means "requires real external
dependencies" per pytest.ini) so they still run in default CI.

Covers the four things task #9 asked for:
  - Birth charts are saved      (test_generate_d1_persists_birth_chart, and
                                  indirectly by every other test here)
  - Planet positions are saved  (test_generate_d1_persists_all_9_planets)
  - Divisional charts are saved (test_compute_divisional_persists_chart,
                                  test_compute_all_persists_all_15_vargas)
  - Dasha calculations are saved (test_persist_tree_all_six_systems, and
                                  the max_depth-levels test)
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from apps.api.models.astrology import (
    BirthChartModel,
    DashaModel,
    DivisionalChartModel,
    DivisionalPlanetPositionModel,
    HouseModel,
    PlanetPositionModel,
)
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.dasha_repository import DashaRepository
from apps.api.repositories.divisional_chart_repository import DivisionalChartRepository
from apps.api.repositories.divisional_planet_repository import DivisionalPlanetRepository
from apps.api.repositories.house_repository import HouseRepository
from apps.api.repositories.planet_position_repository import PlanetPositionRepository
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

pytestmark = pytest.mark.asyncio

_EPHE_PATH = "data/ephemeris"
_BIRTH_DT = datetime(1986, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
_LAT = 28.6139
_LON = 77.2090

_ALL_DASHA_SYSTEMS = [
    "vimshottari", "yogini", "ashtottari", "kalachakra", "chara", "narayana",
]


@pytest.fixture
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


# ── HoroscopeEngine persistence ───────────────────────────────────────────────


async def test_generate_d1_persists_birth_chart(wrapper, db_session):
    engine = HoroscopeEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        planet_position_repo=PlanetPositionRepository(db_session),
        house_repo=HouseRepository(db_session),
    )
    chart = engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    chart_id = await engine.persist_d1(
        chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )

    row = (
        await db_session.execute(
            select(BirthChartModel).where(BirthChartModel.id == chart_id)
        )
    ).scalar_one()
    assert row.lagna_rashi == chart.ascendant.rashi
    assert row.moon_nakshatra == chart.panchanga.nakshatra.nakshatra


async def test_generate_d1_persists_all_9_planets(wrapper, db_session):
    engine = HoroscopeEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        planet_position_repo=PlanetPositionRepository(db_session),
        house_repo=HouseRepository(db_session),
    )
    chart = engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    chart_id = await engine.persist_d1(
        chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )

    planet_rows = (
        await db_session.execute(
            select(PlanetPositionModel).where(PlanetPositionModel.chart_id == chart_id)
        )
    ).scalars().all()
    assert len(planet_rows) == 9
    assert {r.graha for r in planet_rows} == {p.planet for p in chart.planets}

    house_rows = (
        await db_session.execute(
            select(HouseModel).where(HouseModel.chart_id == chart_id)
        )
    ).scalars().all()
    assert len(house_rows) == 12


async def test_persist_d1_without_repos_raises(wrapper):
    """Constructing without repos and calling persist_d1 fails loudly."""
    engine = HoroscopeEngine(wrapper)  # no repos — existing single-arg form
    chart = engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    with pytest.raises(RuntimeError):
        await engine.persist_d1(
            chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
        )


async def test_repeated_d1_requests_reuse_birth_chart_row(wrapper, db_session):
    """Same birth input requested twice must not create two birth_charts rows."""
    engine = HoroscopeEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        planet_position_repo=PlanetPositionRepository(db_session),
        house_repo=HouseRepository(db_session),
    )
    chart = engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    first_id = await engine.persist_d1(
        chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    second_id = await engine.persist_d1(
        chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    assert first_id == second_id

    all_charts = (
        await db_session.execute(select(BirthChartModel))
    ).scalars().all()
    assert len(all_charts) == 1


# ── DivisionalEngine persistence ──────────────────────────────────────────────


async def test_compute_divisional_persists_chart(wrapper, db_session):
    engine = DivisionalEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        divisional_chart_repo=DivisionalChartRepository(db_session),
        divisional_planet_repo=DivisionalPlanetRepository(db_session),
    )
    chart = engine.compute(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON, varga="D9",
    )
    birth_chart_id, divisional_chart_id = await engine.persist_chart(
        chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )

    div_row = (
        await db_session.execute(
            select(DivisionalChartModel).where(DivisionalChartModel.id == divisional_chart_id)
        )
    ).scalar_one()
    assert div_row.chart_type == "D9"
    assert div_row.birth_chart_id == birth_chart_id

    planet_rows = (
        await db_session.execute(
            select(DivisionalPlanetPositionModel).where(
                DivisionalPlanetPositionModel.divisional_chart_id == divisional_chart_id
            )
        )
    ).scalars().all()
    assert len(planet_rows) == 9


async def test_compute_all_persists_all_15_vargas(wrapper, db_session):
    engine = DivisionalEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        divisional_chart_repo=DivisionalChartRepository(db_session),
        divisional_planet_repo=DivisionalPlanetRepository(db_session),
    )
    charts = engine.compute_all(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    birth_chart_id = await engine.persist_all(
        charts, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )

    div_rows = (
        await db_session.execute(
            select(DivisionalChartModel).where(
                DivisionalChartModel.birth_chart_id == birth_chart_id
            )
        )
    ).scalars().all()
    assert len(div_rows) == 15
    assert {r.chart_type for r in div_rows} == set(charts.keys())

    total_planets = (
        await db_session.execute(select(DivisionalPlanetPositionModel))
    ).scalars().all()
    assert len(total_planets) == 15 * 9


async def test_divisional_and_horoscope_share_birth_chart_row(wrapper, db_session):
    """
    A D1 request and a divisional-only request for the same birth input
    must resolve to the same birth_charts row, not two separate ones.
    """
    horoscope_engine = HoroscopeEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        planet_position_repo=PlanetPositionRepository(db_session),
        house_repo=HouseRepository(db_session),
    )
    divisional_engine = DivisionalEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        divisional_chart_repo=DivisionalChartRepository(db_session),
        divisional_planet_repo=DivisionalPlanetRepository(db_session),
    )

    d1_chart = horoscope_engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    d1_chart_id = await horoscope_engine.persist_d1(
        d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )

    varga_chart = divisional_engine.compute(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON, varga="D9",
    )
    varga_birth_chart_id, _ = await divisional_engine.persist_chart(
        varga_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )

    assert d1_chart_id == varga_birth_chart_id


# ── DashaEngine persistence ───────────────────────────────────────────────────


@pytest.mark.parametrize("system", _ALL_DASHA_SYSTEMS)
async def test_persist_tree_all_six_systems(wrapper, db_session, system):
    """
    All six systems must persist correctly — this is the specific
    regression test for migration 0003 (chara/narayana weren't in the
    dasha_type enum at all; yogini/kalachakra/chara/narayana lord names
    aren't Graha names and didn't fit the old `lord` column type).
    """
    engine = DashaEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        dasha_repo=DashaRepository(db_session),
    )
    compute_fn = getattr(engine, f"compute_{system}")
    tree = compute_fn(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON, max_depth=2,
    )
    chart_id = await engine.persist_tree(
        tree, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )

    rows = (
        await db_session.execute(
            select(DashaModel)
            .where(DashaModel.chart_id == chart_id)
            .where(DashaModel.dasha_type == system)
        )
    ).scalars().all()
    assert len(rows) > 0
    mahadasha_rows = [r for r in rows if r.level == 1]
    assert len(mahadasha_rows) == len(tree.mahadashas)
    assert all(r.parent_id is None for r in mahadasha_rows)


async def test_persist_tree_depth_matches_requested_max_depth(wrapper, db_session):
    engine = DashaEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        dasha_repo=DashaRepository(db_session),
    )
    tree = engine.compute_vimshottari(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON, max_depth=3,
    )
    chart_id = await engine.persist_tree(
        tree, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )

    rows = (
        await db_session.execute(
            select(DashaModel)
            .where(DashaModel.chart_id == chart_id)
            .where(DashaModel.dasha_type == "vimshottari")
        )
    ).scalars().all()
    levels_present = {r.level for r in rows}
    assert levels_present == {1, 2, 3}


async def test_dasha_and_horoscope_share_birth_chart_row(wrapper, db_session):
    horoscope_engine = HoroscopeEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        planet_position_repo=PlanetPositionRepository(db_session),
        house_repo=HouseRepository(db_session),
    )
    dasha_engine = DashaEngine(
        wrapper,
        birth_chart_repo=BirthChartRepository(db_session),
        dasha_repo=DashaRepository(db_session),
    )

    d1_chart = horoscope_engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    d1_chart_id = await horoscope_engine.persist_d1(
        d1_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )

    tree = dasha_engine.compute_vimshottari(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON, max_depth=1,
    )
    dasha_chart_id = await dasha_engine.persist_tree(
        tree, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )

    assert d1_chart_id == dasha_chart_id
