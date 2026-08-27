"""
AstroOS — Sarvatobhadra Chakra (SBC) API Schemas
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Optional


from pydantic import BaseModel, Field, field_validator

from apps.api.schemas.ai import DisclosedEventInput


class SBCReportRequest(BaseModel):
    moment_utc: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description=(
                "UTC moment to compute the SBC grid at (ISO-8601, must "
                "include timezone offset). Defaults to the current UTC time."
            ),
        ),
    ] = None
    janma_nakshatra: Annotated[
        Optional[str],
        Field(
            default=None,
            description=(
                "28-system (Abhijit-aware) nakshatra token of the natal/"
                "Janma element to check Vedha hits against, e.g. "
                "'ashwini' or 'abhijit'. Omit to use birth chart or grid snapshot only."
            ),
        ),
    ] = None
    birth_datetime_utc: Annotated[
        Optional[datetime],
        Field(default=None, description="Native's birth datetime in UTC if deriving natal points."),
    ] = None
    birth_latitude: Annotated[Optional[float], Field(default=None, description="Native's birth latitude.")] = None
    birth_longitude: Annotated[Optional[float], Field(default=None, description="Native's birth longitude.")] = None
    ayanamsa: Annotated[Optional[str], Field(default="lahiri", description="Ayanamsa system.")] = "lahiri"
    chart_id: Annotated[Optional[str], Field(default=None, description="Saved chart ID to derive natal points from.")] = None

    @field_validator("moment_utc", "birth_datetime_utc")
    @classmethod
    def _require_tz(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v



class SBCGridPlanetResponse(BaseModel):
    planet: str
    nakshatra: str
    pada: int = 1
    cellnum: int
    rashi: str
    rashi_degree: float
    is_retrograde: bool
    is_combust: bool
    speed_deg_per_day: float
    motion: str = "normal"  # "normal" | "retrograde" | "fast" | "stationary"
    ray_direction: str = "Front"  # "Front" | "Right" | "Left" | "All 3"


class SBCVedhaHitResponse(BaseModel):
    planet: str
    direction: str
    from_nakshatra: str
    score: float


class SBCVedhaResultResponse(BaseModel):
    hits: list[SBCVedhaHitResponse]
    total_score: float
    zeroed_by_malefic_conjunction: bool


class SBCNatalAttributesResponse(BaseModel):
    nama_akshara: str
    janma_rashi: str
    janma_rashi_icon: str
    tithi_name: str
    tithi_group: str
    tithi_number: int
    vara_name: str
    vara_lord: str


class SBCSensitivePointResponse(BaseModel):
    key: str
    name: str
    nakshatra_number: int
    nakshatra_token: str
    nakshatra_name: str
    status: str  # "activated" | "afflicted" | "mixed" | "neutral"
    vedhas_received: list[str] = Field(default_factory=list)
    benefic_hits: list[str] = Field(default_factory=list)
    malefic_hits: list[str] = Field(default_factory=list)


class SBCRawVedhaHitResponse(BaseModel):
    planet: str
    direction: str
    from_nakshatra: str
    target_type: str
    target_key: str
    target_name: str
    nature: str
    strength_factors: dict[str, Any] = Field(default_factory=dict)
    source_convention: str = "narapati_jayacharya"


class SBCVedhaEntryResponse(BaseModel):
    planet: str
    direction: str
    from_nakshatra: str
    target_points: list[str] = Field(default_factory=list)
    score: float = 0.0
    nature: str  # "benefic" | "malefic"
    strength_factors: dict[str, Any] = Field(default_factory=dict)


class SBCRiskItemResponse(BaseModel):
    sangya_key: str
    sangya_name: str
    sangya_offset: int
    nakshatra_name: str
    transiting_planet: str
    transiting_nakshatra: str
    aspect_ray: str
    domain: str
    impact: str


class SBCProtectionItemResponse(BaseModel):
    sangya_key: str
    sangya_name: str
    sangya_offset: int
    nakshatra_name: str
    transiting_planet: str
    transiting_nakshatra: str
    aspect_ray: str
    domain: str
    impact: str


class SBCSynthesisResponse(BaseModel):
    high_risk_areas: list[SBCRiskItemResponse] = Field(default_factory=list)
    protective_shields: list[SBCProtectionItemResponse] = Field(default_factory=list)
    executive_summary: str = ""
    saving_grace: str = ""
    practical_advice: list[str] = Field(default_factory=list)


class SBCReportResponse(BaseModel):
    moment_utc: datetime
    tithi_number: int
    positions: list[SBCGridPlanetResponse]
    janma_nakshatra: Optional[str] = None
    natal_attributes: Optional[SBCNatalAttributesResponse] = None
    sensitive_points: list[SBCSensitivePointResponse] = Field(default_factory=list)
    benefic_vedhas: list[SBCVedhaEntryResponse] = Field(default_factory=list)
    malefic_vedhas: list[SBCVedhaEntryResponse] = Field(default_factory=list)
    raw_hits: list[SBCRawVedhaHitResponse] = Field(default_factory=list)
    synthesis: Optional[SBCSynthesisResponse] = None
    convention_used: str = "narapati_jayacharya"
    total_benefic_score: float = 0.0
    total_malefic_score: float = 0.0
    vedha_result: Optional[SBCVedhaResultResponse] = None




class SBCScanRequest(BaseModel):
    janma_nakshatra: Annotated[
        str,
        Field(description="28-system (Abhijit-aware) nakshatra token of the natal/Janma element to scan for."),
    ]
    start_utc: Annotated[datetime, Field(description="UTC start of the scan range (ISO-8601, must include timezone offset).")]
    end_utc: Annotated[datetime, Field(description="UTC end of the scan range (ISO-8601, must include timezone offset).")]
    step_days: Annotated[
        int,
        Field(default=1, ge=1, le=30, description="Days between samples. Daily by default; see SBCScanEngine's granularity caveat."),
    ] = 1

    subject_status: Annotated[
        Literal["living", "deceased_historical"],
        Field(
            default="living",
            description=(
                "Who the scan is about. 'deceased_historical' selects research/backtesting "
                "mode against a documented historical figure."
            ),
        ),
    ] = "living"
    disclosed_events: Annotated[
        list[DisclosedEventInput],
        Field(
            default_factory=list,
            description=(
                "Life events the native reported themselves. Windows overlapping one of these "
                "in a matching life domain are reported as confirmed rather than inferred."
            ),
        ),
    ]
    now_utc: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="Reference 'now' for past/present/future classification. Defaults to current UTC.",
        ),
    ] = None
    window_gap_days: Annotated[
        float,
        Field(
            default=3.0,
            ge=0.0,
            le=365.0,
            description="Hits no further apart than this are grouped into one reported window.",
        ),
    ] = 3.0

    @field_validator("start_utc", "end_utc")
    @classmethod
    def _require_tz_scan(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("start_utc/end_utc must include a timezone offset")
        return v

    @field_validator("now_utc")
    @classmethod
    def _require_tz_now(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class SBCStancePolicyResponse(BaseModel):
    """What an output about this window is permitted to say."""

    direction: str  # "past" | "present" | "future"
    voice: str  # "retrodictive" | "advisory" | "prospective"
    may_name_specific_event: bool
    requires_invitation_to_confirm: bool
    requires_confidence_qualifier: bool = True
    longevity_formula_allowed: bool = False
    prohibited_categories: list[str] = Field(default_factory=list)
    rationale: str = ""


class SBCEventMatchResponse(BaseModel):
    event_id: str
    domain: str
    description: str = ""
    overlap_days: float
    domain_matches: bool
    matched_sangyas: list[str] = Field(default_factory=list)
    is_confirmation: bool


class SBCScanHitResponse(BaseModel):
    moment_utc: datetime
    vedha_result: SBCVedhaResultResponse
    temporal_direction: str = "present"
    tier: str = "none"
    afflicted_sangyas: list[str] = Field(default_factory=list)
    activated_sangyas: list[str] = Field(default_factory=list)
    policy: Optional[SBCStancePolicyResponse] = None
    event_matches: list[SBCEventMatchResponse] = Field(default_factory=list)


class SBCScanWindowResponse(BaseModel):
    """Consecutive hits collapsed into one contiguous period."""

    start_utc: datetime
    end_utc: datetime
    duration_days: float
    hit_count: int
    temporal_direction: str
    tier: str
    afflicted_sangyas: list[str] = Field(default_factory=list)
    policy: SBCStancePolicyResponse
    event_matches: list[SBCEventMatchResponse] = Field(default_factory=list)
    confirmed_by_disclosure: bool = False


class SBCScanResponse(BaseModel):
    janma_nakshatra: str
    start_utc: datetime
    end_utc: datetime
    step_days: int
    hits: list[SBCScanHitResponse]
    windows: list[SBCScanWindowResponse] = Field(default_factory=list)

