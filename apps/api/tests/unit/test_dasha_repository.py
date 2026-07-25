"""
AstroOS — DashaRepository Unit Tests

Covers the tree structure (parent_id chaining), idempotent replace, and
specifically the two systems (Yogini, Chara/Narayana) that motivated
migration 0003 — their `lord` values are not Graha names, and Chara/
Narayana are not in the original dasha_type enum.
"""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.models.astrology import DashaModel

_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)


def _leaf(lord: str, level: int, start: date, end: date) -> DashaPeriod:
    return DashaPeriod(
        lord=lord, start_date=start, end_date=end,
        duration_days=(end - start).days, level=level, sub_periods=(),
    )


def _make_simple_tree(system: str, lord_name: str) -> DashaTree:
    """A minimal 2-level tree: one Mahadasha with two Antardashas."""
    antardashas = (
        _leaf(lord_name, 2, date(2000, 1, 1), date(2005, 1, 1)),
        _leaf(lord_name, 2, date(2005, 1, 1), date(2010, 1, 1)),
    )
    mahadasha = DashaPeriod(
        lord=lord_name,
        start_date=date(2000, 1, 1),
        end_date=date(2010, 1, 1),
        duration_days=3653,
        level=1,
        sub_periods=antardashas,
    )
    return DashaTree(
        system=system,
        birth_date=date(1990, 6, 15),
        trigger_planet=lord_name,
        trigger_nakshatra="pushya",
        trigger_nakshatra_number=8,
        mahadashas=(mahadasha,),
        max_depth=2,
        total_cycle_years=120,
    )


async def _make_chart_id(birth_chart_repo) -> "uuid.UUID":
    return await birth_chart_repo.get_or_create(
        birth_datetime_utc=_BIRTH_DT,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="W",
    )


async def test_save_tree_persists_mahadasha_and_antardashas(
    birth_chart_repo, dasha_repo, db_session
):
    chart_id = await _make_chart_id(birth_chart_repo)
    tree = _make_simple_tree("vimshottari", "jupiter")

    await dasha_repo.save_tree(chart_id, tree)

    rows = (
        await db_session.execute(
            select(DashaModel)
            .where(DashaModel.chart_id == chart_id)
            .where(DashaModel.dasha_type == "vimshottari")
        )
    ).scalars().all()
    assert len(rows) == 3  # 1 mahadasha + 2 antardashas

    mahadasha_rows = [r for r in rows if r.level == 1]
    antardasha_rows = [r for r in rows if r.level == 2]
    assert len(mahadasha_rows) == 1
    assert len(antardasha_rows) == 2
    assert mahadasha_rows[0].parent_id is None
    assert all(r.parent_id == mahadasha_rows[0].id for r in antardasha_rows)


async def test_save_tree_persists_yogini_lord_name(
    birth_chart_repo, dasha_repo, db_session
):
    """
    Yogini lords (e.g. 'siddha') are not Graha names — this is exactly why
    migration 0003 widened `lord` from the graha enum to a plain string.
    """
    chart_id = await _make_chart_id(birth_chart_repo)
    tree = _make_simple_tree("yogini", "siddha")

    await dasha_repo.save_tree(chart_id, tree)

    rows = (
        await db_session.execute(
            select(DashaModel)
            .where(DashaModel.chart_id == chart_id)
            .where(DashaModel.dasha_type == "yogini")
        )
    ).scalars().all()
    assert all(r.lord == "siddha" for r in rows)


async def test_save_tree_persists_chara_system_and_rashi_lord(
    birth_chart_repo, dasha_repo, db_session
):
    """
    Chara dasha is one of the two systems migration 0003 added to the
    dasha_type enum, and its lord is a Rashi name (e.g. 'aries'), not a
    Graha name.
    """
    chart_id = await _make_chart_id(birth_chart_repo)
    tree = _make_simple_tree("chara", "aries")

    await dasha_repo.save_tree(chart_id, tree)

    rows = (
        await db_session.execute(
            select(DashaModel)
            .where(DashaModel.chart_id == chart_id)
            .where(DashaModel.dasha_type == "chara")
        )
    ).scalars().all()
    assert len(rows) == 3
    assert all(r.lord == "aries" for r in rows)


async def test_save_tree_persists_narayana_system(
    birth_chart_repo, dasha_repo, db_session
):
    chart_id = await _make_chart_id(birth_chart_repo)
    tree = _make_simple_tree("narayana", "cancer")

    await dasha_repo.save_tree(chart_id, tree)

    rows = (
        await db_session.execute(
            select(DashaModel)
            .where(DashaModel.chart_id == chart_id)
            .where(DashaModel.dasha_type == "narayana")
        )
    ).scalars().all()
    assert len(rows) == 3


async def test_save_tree_is_idempotent_per_system(
    birth_chart_repo, dasha_repo, db_session
):
    chart_id = await _make_chart_id(birth_chart_repo)
    tree = _make_simple_tree("vimshottari", "jupiter")

    await dasha_repo.save_tree(chart_id, tree)
    await dasha_repo.save_tree(chart_id, tree)  # re-persist same tree

    rows = (
        await db_session.execute(
            select(DashaModel)
            .where(DashaModel.chart_id == chart_id)
            .where(DashaModel.dasha_type == "vimshottari")
        )
    ).scalars().all()
    assert len(rows) == 3  # not 6 — old rows replaced, not accumulated


async def test_save_tree_does_not_disturb_other_systems(
    birth_chart_repo, dasha_repo, db_session
):
    """Saving a Vimshottari tree must not touch a Yogini tree for the same chart."""
    chart_id = await _make_chart_id(birth_chart_repo)
    await dasha_repo.save_tree(chart_id, _make_simple_tree("vimshottari", "jupiter"))
    await dasha_repo.save_tree(chart_id, _make_simple_tree("yogini", "siddha"))

    all_rows = (
        await db_session.execute(
            select(DashaModel).where(DashaModel.chart_id == chart_id)
        )
    ).scalars().all()
    assert len(all_rows) == 6  # 3 + 3, both systems intact

    # Re-save vimshottari only
    await dasha_repo.save_tree(chart_id, _make_simple_tree("vimshottari", "saturn"))

    yogini_rows = (
        await db_session.execute(
            select(DashaModel)
            .where(DashaModel.chart_id == chart_id)
            .where(DashaModel.dasha_type == "yogini")
        )
    ).scalars().all()
    assert len(yogini_rows) == 3  # untouched
