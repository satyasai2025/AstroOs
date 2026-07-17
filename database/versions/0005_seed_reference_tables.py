"""
AstroOS — Seed Reference Tables

Populates the three ReferenceBase tables created (empty) in migration
0002: `signs` (12 rows), `nakshatras` (27 rows), `padas` (108 rows).

Scope note: there is no separate "Planets" or "Houses" reference table in
this schema to seed. Graha (planet) is a fixed PostgreSQL enum type, not a
table — it needs no seed data of its own. `houses` is the transactional
per-birth-chart table already populated by HouseRepository (see the
persistence layer work) — it is not a lookup/reference table and has
nothing generic to seed; each chart's 12 rows are chart-specific.

Field provenance, to be explicit about what's asserted here:
  - signs.name/lord/start_degree/end_degree, nakshatras.name/lord/number/
    start_degree/end_degree, and all of padas: derived programmatically
    from packages/shared/constants.py and packages/shared/enums.py (the
    same source the calculation engines use), or from simple, universally
    standard classical classifications (element/modality/gender
    triplicities). Cross-checked against divisional_engine.py's actual
    D9/Navamsha formula so the padas table's navamsha_rashi assignments
    are mathematically identical to what the engine independently
    computes at request time — not just "probably consistent."
  - signs.direction and nakshatras.deity/symbol/gana/nadi/varna/yoni/
    shakti are left NULL. These are real classical attributes, but
    populating 27+ nakshatras' worth of deity names, symbols, and
    (especially) shakti descriptions accurately requires a verified
    classical source, not best-effort recall — asserting them here with
    unverified confidence into a research platform's database is a worse
    outcome than leaving them NULL for now. All of these columns are
    nullable specifically to allow exactly this kind of incremental fill.

A third instance of the same column-precision bug found in migration
0004 (combustion_orb_deg) turned up while writing this seed data:
`signs.start_degree/end_degree` (NUMERIC(6,4), max <100) and
`nakshatras`/`padas`.start_degree/end_degree (NUMERIC(8,6), still only 2
integer digits, max <100) cannot hold values up to 360 — yet a sign,
nakshatra, or pada's end_degree legitimately reaches 360 (Pisces,
Revati, and pada 108 respectively). All three are widened to
NUMERIC(9,6) here, immediately before the seed inserts that need it.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Same order the calculation engines use (apps/api/services/divisional_engine.py,
# apps/api/services/dasha_engine.py — both define an identical _RASHI_LIST).
_RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]
_SANSKRIT_NAMES = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
]
_SIGN_LORDS = {
    "aries": "mars", "taurus": "venus", "gemini": "mercury", "cancer": "moon",
    "leo": "sun", "virgo": "mercury", "libra": "venus", "scorpio": "mars",
    "sagittarius": "jupiter", "capricorn": "saturn", "aquarius": "saturn",
    "pisces": "jupiter",
}
_FIRE = {"aries", "leo", "sagittarius"}
_EARTH = {"taurus", "virgo", "capricorn"}
_AIR = {"gemini", "libra", "aquarius"}
_WATER = {"cancer", "scorpio", "pisces"}
_CARDINAL = {"aries", "cancer", "libra", "capricorn"}
_FIXED = {"taurus", "leo", "scorpio", "aquarius"}
_MUTABLE = {"gemini", "virgo", "sagittarius", "pisces"}


def _element(rashi: str) -> str:
    if rashi in _FIRE:
        return "fire"
    if rashi in _EARTH:
        return "earth"
    if rashi in _AIR:
        return "air"
    return "water"


def _modality(rashi: str) -> str:
    if rashi in _CARDINAL:
        return "cardinal"
    if rashi in _FIXED:
        return "fixed"
    return "mutable"


# 27 nakshatras in classical order (0=Ashwini ... 26=Revati) — matches
# packages/shared/enums.py's Nakshatra declaration order and
# packages/shared/constants.py's VIMSHOTTARI_NAKSHATRA_LORDS indexing.
_NAKSHATRA_LIST = [
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva_phalguni",
    "uttara_phalguni", "hasta", "chitra", "swati", "vishakha", "anuradha",
    "jyeshtha", "mula", "purva_ashadha", "uttara_ashadha", "shravana",
    "dhanishtha", "shatabhisha", "purva_bhadrapada", "uttara_bhadrapada",
    "revati",
]
# Vimshottari lord sequence, repeated 3x to cover 27 nakshatras — identical
# to packages/shared/constants.py's VIMSHOTTARI_NAKSHATRA_LORDS.
_VIMSHOTTARI_SEQUENCE = [
    "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
]
_NAKSHATRA_LORDS = _VIMSHOTTARI_SEQUENCE * 3

_DEG_PER_NAKSHATRA = 360.0 / 27.0   # 13°20'
_DEG_PER_PADA = _DEG_PER_NAKSHATRA / 4.0  # 3°20' — identical to a D9 division width


def upgrade() -> None:
    # Same precision bug as combustion_orb_deg in migration 0004: these
    # columns cap at <100 but legitimately need to reach 360 (Pisces,
    # Revati, and pada 108 all end at exactly 360 degrees).
    op.alter_column("signs", "start_degree", type_=sa.Numeric(9, 6), existing_type=sa.Numeric(6, 4))
    op.alter_column("signs", "end_degree", type_=sa.Numeric(9, 6), existing_type=sa.Numeric(6, 4))
    op.alter_column("nakshatras", "start_degree", type_=sa.Numeric(9, 6), existing_type=sa.Numeric(8, 6))
    op.alter_column("nakshatras", "end_degree", type_=sa.Numeric(9, 6), existing_type=sa.Numeric(8, 6))
    op.alter_column("padas", "start_degree", type_=sa.Numeric(9, 6), existing_type=sa.Numeric(8, 6))
    op.alter_column("padas", "end_degree", type_=sa.Numeric(9, 6), existing_type=sa.Numeric(8, 6))

    signs_table = sa.table(
        "signs",
        sa.column("id", sa.SmallInteger),
        sa.column("name", sa.String),
        sa.column("sanskrit_name", sa.String),
        sa.column("lord", sa.String),
        sa.column("element", sa.String),
        sa.column("modality", sa.String),
        sa.column("gender", sa.String),
        sa.column("start_degree", sa.Numeric),
        sa.column("end_degree", sa.Numeric),
    )
    op.bulk_insert(signs_table, [
        {
            "id": i + 1,
            "name": rashi,
            "sanskrit_name": _SANSKRIT_NAMES[i],
            "lord": _SIGN_LORDS[rashi],
            "element": _element(rashi),
            "modality": _modality(rashi),
            "gender": "male" if i % 2 == 0 else "female",  # odd sign (1st,3rd,...) = male
            "start_degree": i * 30.0,
            "end_degree": (i + 1) * 30.0,
        }
        for i, rashi in enumerate(_RASHI_LIST)
    ])

    nakshatras_table = sa.table(
        "nakshatras",
        sa.column("id", sa.SmallInteger),
        sa.column("name", sa.String),
        sa.column("lord", sa.String),
        sa.column("number", sa.SmallInteger),
        sa.column("start_degree", sa.Numeric),
        sa.column("end_degree", sa.Numeric),
    )
    op.bulk_insert(nakshatras_table, [
        {
            "id": i + 1,
            "name": nak,
            "lord": _NAKSHATRA_LORDS[i],
            "number": i + 1,
            "start_degree": i * _DEG_PER_NAKSHATRA,
            "end_degree": (i + 1) * _DEG_PER_NAKSHATRA,
        }
        for i, nak in enumerate(_NAKSHATRA_LIST)
    ])

    padas_table = sa.table(
        "padas",
        sa.column("id", sa.SmallInteger),
        sa.column("nakshatra_id", sa.SmallInteger),
        sa.column("pada_number", sa.SmallInteger),
        sa.column("navamsha_rashi", sa.String),
        sa.column("start_degree", sa.Numeric),
        sa.column("end_degree", sa.Numeric),
    )
    pada_rows = []
    for absolute_pada_index in range(108):  # 27 nakshatras x 4 padas
        nakshatra_id = (absolute_pada_index // 4) + 1
        pada_number = (absolute_pada_index % 4) + 1
        # Navamsha division width (3°20') exactly equals pada width, and
        # both start at 0° Aries, so continuous cycling through
        # _RASHI_LIST reproduces divisional_engine.py's _d9_navamsha()
        # formula exactly (verified: sign_index*9 + part, mod 12).
        navamsha_rashi = _RASHI_LIST[absolute_pada_index % 12]
        pada_rows.append({
            "id": absolute_pada_index + 1,
            "nakshatra_id": nakshatra_id,
            "pada_number": pada_number,
            "navamsha_rashi": navamsha_rashi,
            "start_degree": absolute_pada_index * _DEG_PER_PADA,
            "end_degree": (absolute_pada_index + 1) * _DEG_PER_PADA,
        })
    op.bulk_insert(padas_table, pada_rows)


def downgrade() -> None:
    op.execute("DELETE FROM padas")
    op.execute("DELETE FROM nakshatras")
    op.execute("DELETE FROM signs")

    op.alter_column("signs", "start_degree", type_=sa.Numeric(6, 4), existing_type=sa.Numeric(9, 6))
    op.alter_column("signs", "end_degree", type_=sa.Numeric(6, 4), existing_type=sa.Numeric(9, 6))
    op.alter_column("nakshatras", "start_degree", type_=sa.Numeric(8, 6), existing_type=sa.Numeric(9, 6))
    op.alter_column("nakshatras", "end_degree", type_=sa.Numeric(8, 6), existing_type=sa.Numeric(9, 6))
    op.alter_column("padas", "start_degree", type_=sa.Numeric(8, 6), existing_type=sa.Numeric(9, 6))
    op.alter_column("padas", "end_degree", type_=sa.Numeric(8, 6), existing_type=sa.Numeric(9, 6))
