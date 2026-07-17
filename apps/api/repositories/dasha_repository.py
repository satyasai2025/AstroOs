"""
AstroOS — Dasha Repository

Persistence for the `dashas` table — a self-referencing tree
(Mahadasha -> Antardasha -> Pratyantar -> Sookshma -> Prana) via
parent_id.

Requires migration 0003 (dasha_type enum extended with 'chara' and
'narayana'; `lord` widened from the graha enum to a plain string) — see
that migration's docstring. Without it, persisting a Chara, Narayana, or
Yogini tree, or a Kalachakra/Chara/Narayana lord name, fails at the
database.

Row counts scale with max_depth: a full 5-level Vimshottari tree has 9
Mahadashas, each with 9 Antardashas, each with 9 Pratyantars, and so on —
up to roughly 9^5 (~59,000) rows for one request at max_depth=5. All ids
are generated client-side (uuid.uuid4()) before insert specifically so the
whole tree can be built and added in one batch instead of needing a
round-trip flush after every parent node to learn its generated id.
"""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.models.astrology import DashaModel


class DashaRepository:
    """Data access for dasha trees. Constructor takes an AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_tree(self, chart_id: uuid.UUID, tree: DashaTree) -> None:
        """
        Replace all dashas rows for (chart_id, tree.system) with the given
        tree. Delete-then-insert makes re-persisting the same
        (chart_id, system) idempotent.
        """
        await self._session.execute(
            delete(DashaModel)
            .where(DashaModel.chart_id == chart_id)
            .where(DashaModel.dasha_type == tree.system)
        )

        rows: list[DashaModel] = []
        for mahadasha in tree.mahadashas:
            self._collect_rows(
                mahadasha, chart_id=chart_id, dasha_type=tree.system,
                parent_id=None, out=rows,
            )

        self._session.add_all(rows)
        await self._session.flush()

    def _collect_rows(
        self,
        period: DashaPeriod,
        *,
        chart_id: uuid.UUID,
        dasha_type: str,
        parent_id: Optional[uuid.UUID],
        out: list[DashaModel],
    ) -> None:
        """
        Recursively build DashaModel rows for this period and all its
        sub_periods, with parent_id chained correctly. ids are assigned
        client-side so children can reference their parent's id without a
        round trip.
        """
        node_id = uuid.uuid4()
        out.append(
            DashaModel(
                id=node_id,
                chart_id=chart_id,
                dasha_type=dasha_type,
                level=period.level,
                parent_id=parent_id,
                lord=period.lord,
                start_date=period.start_date,
                end_date=period.end_date,
                duration_days=period.duration_days,
            )
        )
        for sub in period.sub_periods:
            self._collect_rows(
                sub, chart_id=chart_id, dasha_type=dasha_type,
                parent_id=node_id, out=out,
            )
