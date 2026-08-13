"""
AstroOS — Jaimini API Schemas (Layer 7: API Integration)

Pydantic mirror of apps.api.domain.jaimini — the JSON shape the Jaimini
router (routers/jaimini.py) returns and what the frontend's JaiminiPanel
is typed against.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

from apps.api.schemas.common import BirthDataInput

CharaKarakaSchemeSchema = Literal["sapta_karaka", "ashta_karaka"]
TiebreakRuleSchema = Literal["speed", "natural_benefic"]


# ── Requests ──────────────────────────────────────────────────────────────────


class JaiminiBundleRequest(BirthDataInput):
    """Request body for computing every chart-level Jaimini result at once."""

    scheme: Annotated[
        CharaKarakaSchemeSchema,
        Field(default="sapta_karaka", description="Chara Karaka scheme: 7 or 8 karakas."),
    ] = "sapta_karaka"
    max_dasha_depth: Annotated[
        int,
        Field(default=3, ge=1, le=5, description="Deepest Chara/Narayana dasha level to compute."),
    ] = 3
    include_karakamsa: Annotated[
        bool,
        Field(default=True, description="Whether to also compute the D9 Karakamsa/Swamsa."),
    ] = True


class JaiminiArgalaRequest(JaiminiBundleRequest):
    """Request body for computing Argala/Virodhargala from a reference sign or planet."""

    reference: Annotated[
        str,
        Field(description="Reference sign (e.g. 'aries') or planet (e.g. 'moon') to count Argala from."),
    ]


class CharaKarakaSchema(BaseModel):
    rank: int = Field(description="1 = Atmakaraka ... N = Darakaraka.")
    karaka_name: str = Field(description="e.g. 'Atmakaraka', 'Darakaraka'.")
    planet: str = Field(description="Lowercase graha key, e.g. 'sun', 'rahu'.")
    rashi: str
    rashi_degree: float = Field(description="Raw 0-30° position within the occupied sign.")
    karaka_degree: float = Field(
        description="Value actually ranked on. Equals rashi_degree for every "
        "planet except Rahu, whose karaka_degree is (30 - rashi_degree)."
    )
    speed_deg_per_day: float
    is_retrograde: bool
    tiebreak_rule: Optional[TiebreakRuleSchema] = Field(
        default=None,
        description="Set only if this rank was decided by a tie-break against "
        "an immediate neighbor: 'speed' (faster daily motion wins) or "
        "'natural_benefic' (Jupiter > Venus > Mercury > Moon > Sun > Saturn "
        "> Mars > Rahu).",
    )


class CharaKarakaResultSchema(BaseModel):
    scheme: CharaKarakaSchemeSchema
    karakas: list[CharaKarakaSchema]
    atmakaraka: CharaKarakaSchema = Field(description="karakas[0] — convenience duplicate for the frontend.")
    darakaraka: CharaKarakaSchema = Field(description="karakas[-1] — convenience duplicate for the frontend.")


# ── Arudha Pada ─────────────────────────────────────────────────────────────


class ArudhaPadaSchema(BaseModel):
    house_number: int = Field(ge=1, le=12, description="Whole-sign house from Lagna this Arudha was computed for.")
    pada_name: str = Field(description="e.g. 'A1' (Arudha Lagna) ... 'A12' (= Upapada Lagna).")
    rashi: str = Field(description="Final rashi, after the same/7th-house exception shift (if any).")
    raw_rashi: str = Field(description="Rashi before the exception check.")
    lord: str
    lord_rashi: str
    exception_applied: bool = Field(
        description="True if the 'falls on itself or 7th from itself' +9-sign shift fired."
    )


class ArudhaResultSchema(BaseModel):
    padas: list[ArudhaPadaSchema] = Field(description="Exactly 12 entries, house_number 1..12 in order.")
    arudha_lagna: ArudhaPadaSchema = Field(description="padas[0] (A1) — convenience duplicate.")
    upapada_lagna: ArudhaPadaSchema = Field(description="padas[11] (A12) — convenience duplicate.")


# ── Rashi Aspect (Rashi Drishti) ─────────────────────────────────────────────


class RashiAspectSchema(BaseModel):
    from_rashi: str
    to_rashi: str
    aspecting_planets: list[str] = Field(description="Grahas occupying from_rashi (never empty).")
    aspected_planets: list[str] = Field(description="Grahas occupying to_rashi (may be empty).")


class RashiAspectResultSchema(BaseModel):
    matrix: dict[str, list[str]] = Field(
        description="Pure structural lookup: matrix[sign] = every sign it aspects. "
        "Complete for all 12 signs regardless of occupancy."
    )
    aspects: list[RashiAspectSchema] = Field(
        description="Only entries where from_rashi is actually occupied by >=1 planet."
    )


# ── Argala / Virodhargala ────────────────────────────────────────────────────


class ArgalaPairSchema(BaseModel):
    argala_house: int = Field(description="2, 4, 5, or 11 — counted inclusively from the reference.")
    virodhargala_house: int = Field(description="12, 10, 9, or 3 respectively.")
    argala_rashi: str
    virodhargala_rashi: str
    argala_planets: list[str]
    virodhargala_planets: list[str]
    is_active: bool = Field(description="argala_planets is non-empty.")
    is_cancelled: bool = Field(
        description="is_active AND len(virodhargala_planets) >= len(argala_planets)."
    )
    strength_score: float = Field(
        description="Net benefic occupancy of the argala house (benefic count - malefic "
        "count). Reported regardless of is_cancelled."
    )


class ArgalaResultSchema(BaseModel):
    reference_rashi: str
    reference_label: str = Field(description="The planet or sign name originally requested.")
    pairs: list[ArgalaPairSchema] = Field(description="Exactly 4 entries: (2,12), (4,10), (5,9), (11,3).")
    net_strength: float = Field(description="Sum of strength_score across all non-cancelled pairs.")


# ── Karakamsa / Swamsa ────────────────────────────────────────────────────────


class KarakamsaHouseEntrySchema(BaseModel):
    house_number: int = Field(ge=1, le=12, description="Counted zodiacally from Karakamsa.")
    rashi: str
    planets: list[str] = Field(description="D9 (varga) placements of grahas occupying this rashi.")


class KarakamsaResultSchema(BaseModel):
    scheme: CharaKarakaSchemeSchema = Field(description="Which Chara Karaka scheme produced the Atmakaraka used here.")
    atmakaraka: str
    karakamsa_rashi: str = Field(description="D9 sign occupied by Atmakaraka (= Atmakaraka Navamsa sign).")
    swamsa_rashi: str = Field(description="D9 sign occupied by the D1 Lagna (the D9 chart's own Ascendant).")
    d1_atmakaraka_rashi: str = Field(description="Traceability: Atmakaraka's D1 sign.")
    d1_lagna_rashi: str = Field(description="Traceability: D1 Lagna sign.")
    relative_houses: list[KarakamsaHouseEntrySchema] = Field(
        description="Exactly 12 entries — the 'Karakamsa chart', houses 1-12 counted from Karakamsa."
    )


# ── Chara / Narayana Dasha (re-shaped via jaimini_dasha_adapter) ────────────


class JaiminiDashaPeriodSchema(BaseModel):
    rashi: str = Field(description="Ruling sign for this period.")
    start_date: date
    end_date: date
    duration_days: int
    level: int = Field(description="1=Mahadasha, 2=Antardasha, ... up to the requested max_depth.")
    sub_periods: list["JaiminiDashaPeriodSchema"] = Field(default_factory=list)


class JaiminiDashaResultSchema(BaseModel):
    system: Literal["chara", "narayana"]
    lagna_rashi: str = Field(description="D1 Lagna sign (the dasha sequence's starting point).")
    periods: list[JaiminiDashaPeriodSchema]
    max_depth: int
    total_cycle_years: int = Field(description="Varies by chart — not a fixed 120 years like Vimshottari.")


# ── Prediction Evidence ──────────────────────────────────────────────────────


class PredictionReasonSchema(BaseModel):
    description: str
    matched_objects: list[str]
    is_satisfied: bool


class PredictionConfidenceSchema(BaseModel):
    score: int = Field(ge=0, le=100)
    satisfied_conditions: int
    total_conditions: int
    basis: str


class PredictionRuleSchema(BaseModel):
    rule_id: str
    name: str
    sutra_reference: str
    rule_version: str
    requires: list[str]


class PredictionEvidenceSchema(BaseModel):
    rule: PredictionRuleSchema
    is_matched: bool
    triggering_conditions: list[str]
    reasons: list[PredictionReasonSchema]
    confidence: PredictionConfidenceSchema
    explanation: str


# ── API response contracts ───────────────────────────────────────────────────


class JaiminiKarakasResponse(CharaKarakaResultSchema):
    """Chara Karaka piece of the bundle response."""


class JaiminiArudhaResponse(ArudhaResultSchema):
    """Arudha piece of the bundle response."""


class JaiminiAspectsResponse(RashiAspectResultSchema):
    """Rashi Aspect piece of the bundle response."""


class JaiminiDashaResponse(JaiminiDashaResultSchema):
    """Chara or Narayana Dasha piece of the bundle response."""


class JaiminiYogasResponse(BaseModel):
    """Yogas piece of the bundle response."""

    yogas: list[PredictionEvidenceSchema]


class JaiminiKarakamsaResponse(KarakamsaResultSchema):
    """Karakamsa/Swamsa piece of the bundle response — omitted from the
    bundle when the request's include_karakamsa is False."""


class JaiminiBundleResponse(BaseModel):
    """POST /api/v1/jaimini/bundle response — every chart-level Jaimini
    result for one birth chart, computed together in one call by
    JaiminiOrchestrator.compute_bundle(). Mirrors JaiminiBundle 1:1,
    minus the raw D1Chart (already available via /api/v1/horoscope)."""

    chara_karaka: JaiminiKarakasResponse
    arudha: JaiminiArudhaResponse
    rashi_aspect: JaiminiAspectsResponse
    karakamsa: Optional[JaiminiKarakamsaResponse] = None
    chara_dasha: JaiminiDashaResponse
    narayana_dasha: JaiminiDashaResponse
    yogas: list[PredictionEvidenceSchema]


class JaiminiArgalaResponse(ArgalaResultSchema):
    """POST /api/v1/jaimini/argala response contract."""
