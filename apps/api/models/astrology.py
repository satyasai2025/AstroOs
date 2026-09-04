"""
AstroOS — Astrology ORM Models

Maps all Vedic astrology tables to SQLAlchemy mapped classes.
These are infrastructure objects; the service layer works with domain objects.

Design notes:
  - Reference tables (signs, nakshatras, padas) use integer PKs and a
    lightweight ReferenceBase that omits the UUID / soft-delete / updated_at
    overhead from AstroBase.
  - All transactional tables inherit from AstroBase (UUID pk + audit columns).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from apps.api.models.dataset import DatasetModel

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Integer,
    Numeric, SmallInteger, String, Text, text,
)
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import ARRAY, ENUM as PGENUM, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase

# ---------------------------------------------------------------------------
# Lightweight base for immutable reference tables (integer PKs)
# ---------------------------------------------------------------------------

class ReferenceBase(DeclarativeBase):
    """
    Minimal base for reference / lookup tables.
    No UUID, no audit columns — these tables are populated by migrations and
    never soft-deleted.

    Shares AstroBase's MetaData (rather than getting its own, which is
    DeclarativeBase's default) so that transactional tables' foreign keys
    into these reference tables (e.g. planet_positions.nakshatra_id ->
    nakshatras.id) can resolve. Without this, Base.metadata.create_all() —
    the standard SQLAlchemy way to build a schema for tests — raises
    NoReferencedTableError, because the two classes would otherwise
    register their tables in two separate, mutually invisible MetaData
    registries. Alembic's migrations are unaffected either way, since they
    create tables explicitly by name rather than via create_all().
    """
    __abstract__ = True
    metadata = AstroBase.metadata


# ---------------------------------------------------------------------------
# Enum column factories (create_type=False — DDL created via migration)
# ---------------------------------------------------------------------------

def _rashi_col():
    return PGENUM(
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        name="rashi", create_type=False,
    )


def _graha_col():
    return PGENUM(
        "sun", "moon", "mars", "mercury", "jupiter",
        "venus", "saturn", "rahu", "ketu",
        name="graha", create_type=False,
    )


def _nakshatra_col():
    return PGENUM(
        "ashwini", "bharani", "krittika", "rohini", "mrigashira",
        "ardra", "punarvasu", "pushya", "ashlesha", "magha",
        "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati",
        "vishakha", "anuradha", "jyeshtha", "mula", "purva_ashadha",
        "uttara_ashadha", "shravana", "dhanishtha", "shatabhisha",
        "purva_bhadrapada", "uttara_bhadrapada", "revati",
        name="nakshatra_name", create_type=False,
    )


def _chart_type_col():
    return PGENUM(
        "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11",
        "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60", "D81", "D108", "D144",
        name="chart_type", create_type=False,
    )


def _ayanamsa_col():
    return PGENUM(
        "lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra",
        "true_pushya",
        name="ayanamsa_system", create_type=False,
    )


def _dignity_col():
    return PGENUM(
        "exalted", "own", "moolatrikona", "friendly", "neutral", "enemy", "debilitated",
        name="dignity_type", create_type=False,
    )


def _dasha_type_col():
    return PGENUM(
        "vimshottari", "ashtottari", "yogini", "kalachakra", "chara", "narayana",
        name="dasha_type", create_type=False,
    )


# ---------------------------------------------------------------------------
# Reference tables (integer PKs, ReferenceBase)
# ---------------------------------------------------------------------------

class SignModel(ReferenceBase):
    __tablename__ = "signs"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(_rashi_col(), nullable=False, unique=True)
    sanskrit_name: Mapped[str] = mapped_column(String(40), nullable=False)
    lord: Mapped[str] = mapped_column(_graha_col(), nullable=False)
    element: Mapped[str] = mapped_column(String(10), nullable=False)
    modality: Mapped[str] = mapped_column(String(10), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    direction: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    start_degree: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    end_degree: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)


class NakshatraModel(ReferenceBase):
    __tablename__ = "nakshatras"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(_nakshatra_col(), nullable=False, unique=True)
    lord: Mapped[str] = mapped_column(_graha_col(), nullable=False)
    number: Mapped[int] = mapped_column(SmallInteger, nullable=False, unique=True)
    start_degree: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    end_degree: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    deity: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    gana: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nadi: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    varna: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    yoni: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    shakti: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    padas: Mapped[List["PadaModel"]] = relationship(
        "PadaModel", back_populates="nakshatra", cascade="all, delete-orphan"
    )


class PadaModel(ReferenceBase):
    __tablename__ = "padas"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    nakshatra_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("nakshatras.id", ondelete="RESTRICT"), nullable=False
    )
    pada_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    navamsha_rashi: Mapped[str] = mapped_column(_rashi_col(), nullable=False)
    start_degree: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    end_degree: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)

    nakshatra: Mapped["NakshatraModel"] = relationship(
        "NakshatraModel", back_populates="padas"
    )


# ---------------------------------------------------------------------------
# Chart tables (UUID PKs, AstroBase)
# ---------------------------------------------------------------------------

class BirthChartModel(AstroBase):
    __tablename__ = "birth_charts"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    subject_name: Mapped[str] = mapped_column(String(200), nullable=False)
    birth_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    birth_latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    birth_longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    birth_altitude_m: Mapped[Decimal] = mapped_column(
        Numeric(7, 2), nullable=False, server_default="0"
    )
    timezone_offset_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    place_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    ayanamsa: Mapped[str] = mapped_column(
        _ayanamsa_col(), nullable=False, server_default="lahiri"
    )
    house_system: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="whole_sign"
    )
    ayanamsa_value_deg: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 8), nullable=True
    )
    lagna_rashi: Mapped[Optional[str]] = mapped_column(_rashi_col(), nullable=True)
    lagna_degree: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 6), nullable=True)
    moon_nakshatra: Mapped[Optional[str]] = mapped_column(_nakshatra_col(), nullable=True)
    # A user's first saved chart is auto-marked default (see
    # BirthChartRepository.get_or_create); they can later switch it via
    # set_default(). At most one True row per user_id is enforced by
    # migration 0016's partial unique index, not just by application code.
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    planet_positions: Mapped[List["PlanetPositionModel"]] = relationship(
        "PlanetPositionModel", back_populates="chart", cascade="all, delete-orphan"
    )
    houses: Mapped[List["HouseModel"]] = relationship(
        "HouseModel", back_populates="chart", cascade="all, delete-orphan"
    )
    divisional_charts: Mapped[List["DivisionalChartModel"]] = relationship(
        "DivisionalChartModel", back_populates="birth_chart", cascade="all, delete-orphan"
    )
    dashas: Mapped[List["DashaModel"]] = relationship(
        "DashaModel", back_populates="chart", cascade="all, delete-orphan"
    )
    transits: Mapped[List["TransitModel"]] = relationship(
        "TransitModel", back_populates="chart", cascade="all, delete-orphan"
    )
    events: Mapped[List["EventModel"]] = relationship(
        "EventModel", back_populates="chart", cascade="all, delete-orphan"
    )


class PlanetPositionModel(AstroBase):
    __tablename__ = "planet_positions"

    chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("birth_charts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    graha: Mapped[str] = mapped_column(_graha_col(), nullable=False)
    longitude_deg: Mapped[Decimal] = mapped_column(Numeric(11, 8), nullable=False)
    latitude_deg: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8), nullable=True)
    speed_deg_per_day: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8), nullable=True)
    distance_au: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 10), nullable=True)
    sidereal_longitude_deg: Mapped[Decimal] = mapped_column(Numeric(11, 8), nullable=False)
    rashi: Mapped[str] = mapped_column(_rashi_col(), nullable=False)
    rashi_degree: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    house_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    nakshatra_id: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("nakshatras.id", ondelete="RESTRICT"), nullable=True
    )
    pada_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    is_retrograde: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_combust: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    combustion_orb_deg: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6),
        nullable=True,
        doc=(
            "True angular distance from the Sun (0-180 degrees), not just "
            "the value when combust — widened from Numeric(6,4) in "
            "migration 0004 after a real chart produced 150.03 degrees "
            "for a non-combust planet."
        ),
    )
    dignity: Mapped[Optional[str]] = mapped_column(_dignity_col(), nullable=True)
    shadbala_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)

    chart: Mapped["BirthChartModel"] = relationship(
        "BirthChartModel", back_populates="planet_positions"
    )


class HouseModel(AstroBase):
    __tablename__ = "houses"

    chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("birth_charts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    house_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rashi: Mapped[str] = mapped_column(_rashi_col(), nullable=False)
    cusp_degree: Mapped[Decimal] = mapped_column(Numeric(11, 8), nullable=False)
    mid_degree: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8), nullable=True)

    chart: Mapped["BirthChartModel"] = relationship(
        "BirthChartModel", back_populates="houses"
    )


class DivisionalChartModel(AstroBase):
    __tablename__ = "divisional_charts"

    birth_chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("birth_charts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    chart_type: Mapped[str] = mapped_column(_chart_type_col(), nullable=False)
    lagna_rashi: Mapped[Optional[str]] = mapped_column(_rashi_col(), nullable=True)
    lagna_degree: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 6), nullable=True)

    birth_chart: Mapped["BirthChartModel"] = relationship(
        "BirthChartModel", back_populates="divisional_charts"
    )
    planet_positions: Mapped[List["DivisionalPlanetPositionModel"]] = relationship(
        "DivisionalPlanetPositionModel", back_populates="divisional_chart",
        cascade="all, delete-orphan",
    )


class DivisionalPlanetPositionModel(AstroBase):
    __tablename__ = "divisional_planet_positions"

    divisional_chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("divisional_charts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    graha: Mapped[str] = mapped_column(_graha_col(), nullable=False)
    rashi: Mapped[str] = mapped_column(_rashi_col(), nullable=False)
    house_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rashi_degree: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 6), nullable=True)
    dignity: Mapped[Optional[str]] = mapped_column(_dignity_col(), nullable=True)

    divisional_chart: Mapped["DivisionalChartModel"] = relationship(
        "DivisionalChartModel", back_populates="planet_positions"
    )


class DashaModel(AstroBase):
    __tablename__ = "dashas"

    chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("birth_charts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    dasha_type: Mapped[str] = mapped_column(
        _dasha_type_col(), nullable=False, server_default="vimshottari"
    )
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dashas.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    lord: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        doc=(
            "Ruling entity for this period — meaning depends on dasha_type: "
            "Graha name (vimshottari/ashtottari), Yogini name (yogini), or "
            "Rashi name (kalachakra/chara/narayana). Widened from the graha "
            "enum in migration 0003 because only 2 of 6 systems use a "
            "Graha name here."
        ),
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)

    chart: Mapped["BirthChartModel"] = relationship(
        "BirthChartModel", back_populates="dashas"
    )


class TransitModel(AstroBase):
    __tablename__ = "transits"

    chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("birth_charts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    transit_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    graha: Mapped[str] = mapped_column(_graha_col(), nullable=False)
    transit_rashi: Mapped[str] = mapped_column(_rashi_col(), nullable=False)
    transit_longitude_deg: Mapped[Decimal] = mapped_column(Numeric(11, 8), nullable=False)
    natal_house_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    is_retrograde: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ayanamsa: Mapped[str] = mapped_column(
        _ayanamsa_col(), nullable=False, server_default="lahiri"
    )

    chart: Mapped["BirthChartModel"] = relationship(
        "BirthChartModel", back_populates="transits"
    )


class EventModel(AstroBase):
    __tablename__ = "events"

    chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("birth_charts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    chart: Mapped["BirthChartModel"] = relationship(
        "BirthChartModel", back_populates="events"
    )


# ---------------------------------------------------------------------------
# Event Analysis tables (Event Chart / muhurta consultation)
# ---------------------------------------------------------------------------

class EventAnalysisModel(AstroBase):
    """
    One persisted event analysis (muhurta consultation). The aggregate root
    of the Event Analysis feature: references (ids) to the generated
    event-chart / transit / dasha artifact snapshots rather than embedding
    large chart JSON blobs; only the compact report JSON and the numeric
    overall score live on this row. See domain/event_analysis.py.
    """

    __tablename__ = "event_analyses"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    # No separate Person table — the saved natal chart IS the person;
    # person_id mirrors birth_chart_id and reserves the field for a future
    # Person entity (see domain/event_analysis.py).
    person_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    birth_chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("birth_charts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    event_name: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    event_latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    event_longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    place_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    timezone_iana: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # User-selected analysis scope flags (subset of EVENT_ANALYSIS_SCOPE_FLAGS),
    # stored as a JSON array of strings so any stored report is reproducible.
    scope: Mapped[Optional[list]] = mapped_column(PG_JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # References to generated snapshots in event_chart_snapshots.
    event_chart_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    transit_chart_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    dasha_snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    analysis_report_json: Mapped[Optional[dict]] = mapped_column(PG_JSONB, nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)


class EventChartSnapshotModel(AstroBase):
    """
    A generated artifact snapshot for an Event Analysis — the cast event
    chart (muhurta D1), the event-moment transit read, or the active dasha
    chain, referenced by id from event_analyses. Stores the serialized JSON
    payload (see event_analysis_engine serializers).
    """

    __tablename__ = "event_chart_snapshots"

    birth_chart_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    snapshot_type: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    payload_json: Mapped[Optional[dict]] = mapped_column(PG_JSONB, nullable=True)


# ---------------------------------------------------------------------------
# Knowledge tables
# ---------------------------------------------------------------------------

class BookModel(AstroBase):
    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    period_ce: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tradition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    version_comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    superseded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
    )

    verses: Mapped[List["VerseModel"]] = relationship(
        "VerseModel", back_populates="book", cascade="all, delete-orphan"
    )


class VerseModel(AstroBase):
    __tablename__ = "verses"

    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    chapter: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    verse_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    transliteration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    translation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    commentary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    version_comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    superseded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verses.id", ondelete="SET NULL"),
        nullable=True,
    )

    book: Mapped["BookModel"] = relationship("BookModel", back_populates="verses")


class RuleModel(AstroBase):
    __tablename__ = "rules"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    verse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verses.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    condition_dsl: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    tradition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    version_comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    superseded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rules.id", ondelete="SET NULL"),
        nullable=True,
    )


class KarakatvaModel(AstroBase):
    __tablename__ = "karakatvas"

    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    graha: Mapped[Optional[str]] = mapped_column(_graha_col(), nullable=True)
    sign_id: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("signs.id", ondelete="SET NULL"), nullable=True
    )
    house_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    tradition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_verse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verses.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    version_comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    superseded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("karakatvas.id", ondelete="SET NULL"),
        nullable=True,
    )


class KnowledgeEmbeddingModel(AstroBase):
    """
    One embedding vector for one piece of knowledge-base text (a verse's
    translation, a rule's interpretation, etc.) — the retrieval index for
    RAG-grounded AI answers (Phase IV.3.1).

    Deliberately generic/polymorphic (source_type + source_id) rather than
    a dedicated FK per knowledge table, so future embeddable content
    (techniques, karakatvas, ...) doesn't need its own embeddings table.
    Not a foreign key by design — source rows use soft-append versioning
    (superseded_by) themselves, so a hard FK here would fight that model;
    orphaned embeddings (source row superseded/deleted) are pruned by the
    same backfill job that (re)creates them, not by DB cascade.
    """
    __tablename__ = "knowledge_embeddings"

    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    """e.g. "verse", "rule". Not an enum — new embeddable content types
    shouldn't require a migration."""
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    embedded_text: Mapped[str] = mapped_column(Text, nullable=False)
    """The exact text that was embedded — kept so the embedding can be
    audited/regenerated without re-deriving what was originally embedded
    (source text may itself be versioned/superseded later)."""
    embedding: Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    """Which embedding model produced this vector — different models are
    not comparable to each other, so a similarity search must only ever
    compare embeddings produced by the same model_name."""


# ---------------------------------------------------------------------------
# Research tables
# ---------------------------------------------------------------------------

class ResearchProjectModel(AstroBase):
    __tablename__ = "research_projects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    hypothesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    methodology: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    conclusions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dataset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
    )

    snapshots: Mapped[List["ResearchSnapshotModel"]] = relationship(
        "ResearchSnapshotModel", back_populates="project", cascade="all, delete-orphan"
    )
    dataset: Mapped[Optional["DatasetModel"]] = relationship(
        "DatasetModel", back_populates=None,
    )


class ResearchSnapshotModel(AstroBase):
    __tablename__ = "research_snapshots"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("birth_charts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    label: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["ResearchProjectModel"] = relationship(
        "ResearchProjectModel", back_populates="snapshots"
    )


class ResearchExperimentModel(AstroBase):
    __tablename__ = "research_experiments"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    hypothesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    methodology: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rule_registry_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    dataset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
    )


class ExperimentExecutionModel(AstroBase):
    __tablename__ = "experiment_executions"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_experiments.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    execution_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
