"""Full Vedic Astrology Schema

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-08 00:00:00.000000

Tables added:
  birth_charts, planet_positions, signs, houses, nakshatras, padas,
  divisional_charts, divisional_planet_positions,
  dashas, transits, events, rules, books, verses, karakatvas,
  research_projects, research_snapshots
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _create_enum(conn, name: str, values: list[str]) -> None:
    placeholders = ", ".join(f"'{v}'" for v in values)
    conn.execute(sa.text(
        f"DO $$ BEGIN "
        f"  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN "
        f"    CREATE TYPE {name} AS ENUM ({placeholders}); "
        f"  END IF; "
        f"END $$"
    ))


def _trigger(conn, table: str) -> None:
    conn.execute(sa.text(
        f"CREATE TRIGGER trg_{table}_updated_at "
        f"BEFORE UPDATE ON {table} "
        f"FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))


def upgrade() -> None:
    conn = op.get_bind()

    # ── Enums ────────────────────────────────────────────────────────────────
    _create_enum(conn, "rashi", [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ])
    _create_enum(conn, "graha", [
        "sun", "moon", "mars", "mercury", "jupiter",
        "venus", "saturn", "rahu", "ketu",
    ])
    _create_enum(conn, "nakshatra_name", [
        "ashwini", "bharani", "krittika", "rohini", "mrigashira",
        "ardra", "punarvasu", "pushya", "ashlesha", "magha",
        "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati",
        "vishakha", "anuradha", "jyeshtha", "mula", "purva_ashadha",
        "uttara_ashadha", "shravana", "dhanishtha", "shatabhisha",
        "purva_bhadrapada", "uttara_bhadrapada", "revati",
    ])
    _create_enum(conn, "chart_type", [
        "D1", "D2", "D3", "D4", "D7", "D9", "D10",
        "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
    ])
    _create_enum(conn, "ayanamsa_system", [
        "lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra",
    ])
    _create_enum(conn, "dignity_type", [
        "exalted", "own", "moolatrikona", "friendly", "neutral", "enemy", "debilitated",
    ])
    _create_enum(conn, "dasha_type", [
        "vimshottari", "ashtottari", "yogini", "kalachakra",
    ])
    _create_enum(conn, "aspect_type", [
        "conjunction", "opposition", "trine", "square",
        "sextile", "special_graha",
    ])

    # ── signs (rashis) — reference table ─────────────────────────────────────
    op.create_table(
        "signs",
        sa.Column("id", sa.SmallInteger, primary_key=True),
        sa.Column("name", postgresql.ENUM("aries", "taurus", "gemini", "cancer",
                  "leo", "virgo", "libra", "scorpio", "sagittarius",
                  "capricorn", "aquarius", "pisces",
                  name="rashi", create_type=False), nullable=False),
        sa.Column("sanskrit_name", sa.String(40), nullable=False),
        sa.Column("lord", postgresql.ENUM("sun", "moon", "mars", "mercury",
                  "jupiter", "venus", "saturn", "rahu", "ketu",
                  name="graha", create_type=False), nullable=False),
        sa.Column("element", sa.String(10), nullable=False),     # fire/earth/air/water
        sa.Column("modality", sa.String(10), nullable=False),    # movable/fixed/dual
        sa.Column("gender", sa.String(10), nullable=False),      # masculine/feminine
        sa.Column("direction", sa.String(10), nullable=True),
        sa.Column("start_degree", sa.Numeric(6, 4), nullable=False),
        sa.Column("end_degree", sa.Numeric(6, 4), nullable=False),
    )
    op.create_index("ix_signs_name", "signs", ["name"], unique=True)

    # ── nakshatras — reference table ──────────────────────────────────────────
    op.create_table(
        "nakshatras",
        sa.Column("id", sa.SmallInteger, primary_key=True),
        sa.Column("name", postgresql.ENUM(
            "ashwini", "bharani", "krittika", "rohini", "mrigashira",
            "ardra", "punarvasu", "pushya", "ashlesha", "magha",
            "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati",
            "vishakha", "anuradha", "jyeshtha", "mula", "purva_ashadha",
            "uttara_ashadha", "shravana", "dhanishtha", "shatabhisha",
            "purva_bhadrapada", "uttara_bhadrapada", "revati",
            name="nakshatra_name", create_type=False), nullable=False),
        sa.Column("lord", postgresql.ENUM("sun", "moon", "mars", "mercury",
                  "jupiter", "venus", "saturn", "rahu", "ketu",
                  name="graha", create_type=False), nullable=False),
        sa.Column("number", sa.SmallInteger, nullable=False),  # 1–27
        sa.Column("start_degree", sa.Numeric(8, 6), nullable=False),
        sa.Column("end_degree", sa.Numeric(8, 6), nullable=False),
        sa.Column("deity", sa.String(60), nullable=True),
        sa.Column("symbol", sa.String(60), nullable=True),
        sa.Column("gana", sa.String(20), nullable=True),   # deva/manushya/rakshasa
        sa.Column("nadi", sa.String(20), nullable=True),   # vata/pitta/kapha
        sa.Column("varna", sa.String(20), nullable=True),
        sa.Column("yoni", sa.String(30), nullable=True),
        sa.Column("shakti", sa.String(100), nullable=True),
    )
    op.create_index("ix_nakshatras_name", "nakshatras", ["name"], unique=True)
    op.create_index("ix_nakshatras_number", "nakshatras", ["number"], unique=True)

    # ── padas — reference table ───────────────────────────────────────────────
    op.create_table(
        "padas",
        sa.Column("id", sa.SmallInteger, primary_key=True),   # 1–108
        sa.Column("nakshatra_id", sa.SmallInteger,
                  sa.ForeignKey("nakshatras.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pada_number", sa.SmallInteger, nullable=False),   # 1–4
        sa.Column("navamsha_rashi", postgresql.ENUM("aries", "taurus", "gemini",
                  "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius",
                  "capricorn", "aquarius", "pisces",
                  name="rashi", create_type=False), nullable=False),
        sa.Column("start_degree", sa.Numeric(8, 6), nullable=False),
        sa.Column("end_degree", sa.Numeric(8, 6), nullable=False),
    )
    op.create_index("ix_padas_nakshatra_pada", "padas",
                    ["nakshatra_id", "pada_number"], unique=True)

    # ── birth_charts ──────────────────────────────────────────────────────────
    op.create_table(
        "birth_charts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Owner
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Subject
        sa.Column("subject_name", sa.String(200), nullable=False),
        sa.Column("birth_datetime_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("birth_latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("birth_longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("birth_altitude_m", sa.Numeric(7, 2), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("timezone_offset_minutes", sa.Integer, nullable=False),
        sa.Column("place_name", sa.String(300), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=True),
        # Calculation parameters
        sa.Column("ayanamsa", postgresql.ENUM("lahiri", "kp", "raman",
                  "yukteshwar", "fagan_bradley", "true_chitra",
                  name="ayanamsa_system", create_type=False), nullable=False,
                  server_default="lahiri"),
        sa.Column("house_system", sa.String(20), nullable=False,
                  server_default="whole_sign"),
        sa.Column("ayanamsa_value_deg", sa.Numeric(10, 8), nullable=True),
        # D1 summary fields (denormalised for quick access)
        sa.Column("lagna_rashi", postgresql.ENUM("aries", "taurus", "gemini",
                  "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius",
                  "capricorn", "aquarius", "pisces",
                  name="rashi", create_type=False), nullable=True),
        sa.Column("lagna_degree", sa.Numeric(8, 6), nullable=True),
        sa.Column("moon_nakshatra", postgresql.ENUM(
            "ashwini", "bharani", "krittika", "rohini", "mrigashira",
            "ardra", "punarvasu", "pushya", "ashlesha", "magha",
            "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati",
            "vishakha", "anuradha", "jyeshtha", "mula", "purva_ashadha",
            "uttara_ashadha", "shravana", "dhanishtha", "shatabhisha",
            "purva_bhadrapada", "uttara_bhadrapada", "revati",
            name="nakshatra_name", create_type=False), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        # Full text search
        sa.Column("fts_vector", postgresql.TSVECTOR, nullable=True),
    )
    op.create_index("ix_birth_charts_user_id", "birth_charts", ["user_id"])
    op.create_index("ix_birth_charts_birth_datetime",
                    "birth_charts", ["birth_datetime_utc"])
    conn.execute(sa.text(
        "CREATE INDEX ix_birth_charts_fts ON birth_charts "
        "USING GIN(fts_vector)"
    ))
    _trigger(conn, "birth_charts")

    # ── planet_positions ──────────────────────────────────────────────────────
    op.create_table(
        "planet_positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("birth_charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("graha", postgresql.ENUM("sun", "moon", "mars", "mercury",
                  "jupiter", "venus", "saturn", "rahu", "ketu",
                  name="graha", create_type=False), nullable=False),
        # Coordinates
        sa.Column("longitude_deg", sa.Numeric(11, 8), nullable=False),
        sa.Column("latitude_deg", sa.Numeric(11, 8), nullable=True),
        sa.Column("speed_deg_per_day", sa.Numeric(11, 8), nullable=True),
        sa.Column("distance_au", sa.Numeric(15, 10), nullable=True),
        # Sidereal position
        sa.Column("sidereal_longitude_deg", sa.Numeric(11, 8), nullable=False),
        sa.Column("rashi", postgresql.ENUM("aries", "taurus", "gemini", "cancer",
                  "leo", "virgo", "libra", "scorpio", "sagittarius",
                  "capricorn", "aquarius", "pisces",
                  name="rashi", create_type=False), nullable=False),
        sa.Column("rashi_degree", sa.Numeric(8, 6), nullable=False),   # 0–30
        sa.Column("house_number", sa.SmallInteger, nullable=False),     # 1–12
        # Nakshatra
        sa.Column("nakshatra_id", sa.SmallInteger,
                  sa.ForeignKey("nakshatras.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("pada_number", sa.SmallInteger, nullable=True),
        # Status flags
        sa.Column("is_retrograde", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_combust", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("combustion_orb_deg", sa.Numeric(6, 4), nullable=True),
        # Dignity
        sa.Column("dignity", postgresql.ENUM("exalted", "own", "moolatrikona",
                  "friendly", "neutral", "enemy", "debilitated",
                  name="dignity_type", create_type=False), nullable=True),
        sa.Column("shadbala_score", sa.Numeric(8, 4), nullable=True),
    )
    op.create_index("ix_planet_positions_chart_id",
                    "planet_positions", ["chart_id"])
    op.create_index("ix_planet_positions_chart_graha",
                    "planet_positions", ["chart_id", "graha"], unique=True)

    # ── houses ────────────────────────────────────────────────────────────────
    op.create_table(
        "houses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("birth_charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("house_number", sa.SmallInteger, nullable=False),   # 1–12
        sa.Column("rashi", postgresql.ENUM("aries", "taurus", "gemini", "cancer",
                  "leo", "virgo", "libra", "scorpio", "sagittarius",
                  "capricorn", "aquarius", "pisces",
                  name="rashi", create_type=False), nullable=False),
        sa.Column("cusp_degree", sa.Numeric(11, 8), nullable=False),
        sa.Column("mid_degree", sa.Numeric(11, 8), nullable=True),
    )
    op.create_index("ix_houses_chart_id", "houses", ["chart_id"])
    op.create_index("ix_houses_chart_house",
                    "houses", ["chart_id", "house_number"], unique=True)

    # ── divisional_charts ─────────────────────────────────────────────────────
    op.create_table(
        "divisional_charts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("birth_chart_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("birth_charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chart_type", postgresql.ENUM("D1", "D2", "D3", "D4", "D7",
                  "D9", "D10", "D12", "D16", "D20", "D24", "D27",
                  "D30", "D40", "D45", "D60",
                  name="chart_type", create_type=False), nullable=False),
        sa.Column("lagna_rashi", postgresql.ENUM("aries", "taurus", "gemini",
                  "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius",
                  "capricorn", "aquarius", "pisces",
                  name="rashi", create_type=False), nullable=True),
        sa.Column("lagna_degree", sa.Numeric(8, 6), nullable=True),
    )
    op.create_index("ix_divisional_charts_birth_chart_id",
                    "divisional_charts", ["birth_chart_id"])
    op.create_index("ix_divisional_charts_birth_chart_type",
                    "divisional_charts", ["birth_chart_id", "chart_type"], unique=True)
    _trigger(conn, "divisional_charts")

    # ── divisional_planet_positions ───────────────────────────────────────────
    op.create_table(
        "divisional_planet_positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("divisional_chart_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("divisional_charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("graha", postgresql.ENUM("sun", "moon", "mars", "mercury",
                  "jupiter", "venus", "saturn", "rahu", "ketu",
                  name="graha", create_type=False), nullable=False),
        sa.Column("rashi", postgresql.ENUM("aries", "taurus", "gemini", "cancer",
                  "leo", "virgo", "libra", "scorpio", "sagittarius",
                  "capricorn", "aquarius", "pisces",
                  name="rashi", create_type=False), nullable=False),
        sa.Column("house_number", sa.SmallInteger, nullable=False),
        sa.Column("rashi_degree", sa.Numeric(8, 6), nullable=True),
        sa.Column("dignity", postgresql.ENUM("exalted", "own", "moolatrikona",
                  "friendly", "neutral", "enemy", "debilitated",
                  name="dignity_type", create_type=False), nullable=True),
    )
    op.create_index("ix_div_planet_pos_chart_id",
                    "divisional_planet_positions", ["divisional_chart_id"])
    op.create_index("ix_div_planet_pos_chart_graha",
                    "divisional_planet_positions",
                    ["divisional_chart_id", "graha"], unique=True)

    # ── dashas ────────────────────────────────────────────────────────────────
    op.create_table(
        "dashas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("birth_charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dasha_type", postgresql.ENUM("vimshottari", "ashtottari",
                  "yogini", "kalachakra",
                  name="dasha_type", create_type=False), nullable=False,
                  server_default="vimshottari"),
        sa.Column("level", sa.SmallInteger, nullable=False),   # 1=mahadasha, 2=antardasha, etc.
        sa.Column("parent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("dashas.id", ondelete="CASCADE"), nullable=True),
        sa.Column("lord", postgresql.ENUM("sun", "moon", "mars", "mercury",
                  "jupiter", "venus", "saturn", "rahu", "ketu",
                  name="graha", create_type=False), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("duration_days", sa.Integer, nullable=False),
    )
    op.create_index("ix_dashas_chart_id", "dashas", ["chart_id"])
    op.create_index("ix_dashas_parent_id", "dashas", ["parent_id"])
    op.create_index("ix_dashas_chart_date", "dashas", ["chart_id", "start_date"])

    # ── transits ──────────────────────────────────────────────────────────────
    op.create_table(
        "transits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("birth_charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transit_datetime_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("graha", postgresql.ENUM("sun", "moon", "mars", "mercury",
                  "jupiter", "venus", "saturn", "rahu", "ketu",
                  name="graha", create_type=False), nullable=False),
        sa.Column("transit_rashi", postgresql.ENUM("aries", "taurus", "gemini",
                  "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius",
                  "capricorn", "aquarius", "pisces",
                  name="rashi", create_type=False), nullable=False),
        sa.Column("transit_longitude_deg", sa.Numeric(11, 8), nullable=False),
        sa.Column("natal_house_number", sa.SmallInteger, nullable=True),
        sa.Column("is_retrograde", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ayanamsa", postgresql.ENUM("lahiri", "kp", "raman",
                  "yukteshwar", "fagan_bradley", "true_chitra",
                  name="ayanamsa_system", create_type=False), nullable=False,
                  server_default="lahiri"),
    )
    op.create_index("ix_transits_chart_id", "transits", ["chart_id"])
    op.create_index("ix_transits_datetime", "transits", ["transit_datetime_utc"])

    # ── events ────────────────────────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("birth_charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("fts_vector", postgresql.TSVECTOR, nullable=True),
    )
    op.create_index("ix_events_chart_id", "events", ["chart_id"])
    op.create_index("ix_events_date", "events", ["event_date"])
    conn.execute(sa.text(
        "CREATE INDEX ix_events_fts ON events USING GIN(fts_vector)"
    ))
    _trigger(conn, "events")

    # ── books ─────────────────────────────────────────────────────────────────
    op.create_table(
        "books",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("author", sa.String(300), nullable=True),
        sa.Column("language", sa.String(50), nullable=True),
        sa.Column("period_ce", sa.String(50), nullable=True),
        sa.Column("tradition", sa.String(100), nullable=True),   # BPHS / KP / etc.
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("fts_vector", postgresql.TSVECTOR, nullable=True),
    )
    conn.execute(sa.text(
        "CREATE INDEX ix_books_fts ON books USING GIN(fts_vector)"
    ))
    _trigger(conn, "books")

    # ── verses ────────────────────────────────────────────────────────────────
    op.create_table(
        "verses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chapter", sa.SmallInteger, nullable=True),
        sa.Column("verse_number", sa.SmallInteger, nullable=True),
        sa.Column("original_text", sa.Text, nullable=False),
        sa.Column("transliteration", sa.Text, nullable=True),
        sa.Column("translation", sa.Text, nullable=True),
        sa.Column("commentary", sa.Text, nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("fts_vector", postgresql.TSVECTOR, nullable=True),
    )
    op.create_index("ix_verses_book_id", "verses", ["book_id"])
    conn.execute(sa.text(
        "CREATE INDEX ix_verses_fts ON verses USING GIN(fts_vector)"
    ))
    _trigger(conn, "verses")

    # ── rules ─────────────────────────────────────────────────────────────────
    op.create_table(
        "rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("verse_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("verses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("condition_dsl", sa.Text, nullable=True),
        sa.Column("interpretation", sa.Text, nullable=False),
        sa.Column("tradition", sa.String(100), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("fts_vector", postgresql.TSVECTOR, nullable=True),
    )
    op.create_index("ix_rules_user_id", "rules", ["user_id"])
    conn.execute(sa.text(
        "CREATE INDEX ix_rules_fts ON rules USING GIN(fts_vector)"
    ))
    _trigger(conn, "rules")

    # ── karakatvas ────────────────────────────────────────────────────────────
    op.create_table(
        "karakatvas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("graha", postgresql.ENUM("sun", "moon", "mars", "mercury",
                  "jupiter", "venus", "saturn", "rahu", "ketu",
                  name="graha", create_type=False), nullable=True),
        sa.Column("sign_id", sa.SmallInteger,
                  sa.ForeignKey("signs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("house_number", sa.SmallInteger, nullable=True),
        sa.Column("tradition", sa.String(100), nullable=True),
        sa.Column("source_verse_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("verses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
    )
    op.create_index("ix_karakatvas_graha", "karakatvas", ["graha"])
    op.create_index("ix_karakatvas_house", "karakatvas", ["house_number"])

    # ── research_projects ─────────────────────────────────────────────────────
    op.create_table(
        "research_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("hypothesis", sa.Text, nullable=True),
        sa.Column("methodology", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("conclusions", sa.Text, nullable=True),
        sa.Column("fts_vector", postgresql.TSVECTOR, nullable=True),
    )
    op.create_index("ix_research_projects_user_id", "research_projects", ["user_id"])
    conn.execute(sa.text(
        "CREATE INDEX ix_research_projects_fts ON research_projects USING GIN(fts_vector)"
    ))
    _trigger(conn, "research_projects")

    # ── research_snapshots ────────────────────────────────────────────────────
    op.create_table(
        "research_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("birth_charts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(300), nullable=True),
        sa.Column("snapshot_json", sa.Text, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index("ix_research_snapshots_project_id",
                    "research_snapshots", ["project_id"])
    op.create_index("ix_research_snapshots_chart_id",
                    "research_snapshots", ["chart_id"])


def downgrade() -> None:
    conn = op.get_bind()

    for table in [
        "research_snapshots", "research_projects",
        "karakatvas", "rules", "verses", "books",
        "events", "transits", "dashas",
        "divisional_planet_positions", "divisional_charts",
        "houses", "planet_positions", "birth_charts",
        "padas", "nakshatras", "signs",
    ]:
        op.drop_table(table)

    for enum in [
        "aspect_type", "dasha_type", "dignity_type",
        "ayanamsa_system", "chart_type", "nakshatra_name",
        "graha", "rashi",
    ]:
        conn.execute(sa.text(f"DROP TYPE IF EXISTS {enum}"))
