"""
AstroOS — Sensitive timeline & retrodiction validation API Schemas

Two surfaces share these models:

* ``/sensitive-timeline/report`` — the reading surface. Past windows the
  native can check, future alerts they can prepare for.
* ``/sensitive-timeline/validate`` — the research surface. The same
  windows scored against events the native actually reported.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from apps.api.schemas.ai import DisclosedEventInput
from apps.api.schemas.sbc import SBCEventMatchResponse, SBCStancePolicyResponse
from packages.shared.enums import Nakshatra

_VALID_NAKSHATRAS = frozenset(n.value for n in Nakshatra)


class SensitiveTimelineRequest(BaseModel):
    janma_nakshatra: Annotated[
        str, Field(description="Standard 27-system natal Moon nakshatra token, e.g. 'rohini'.")
    ]
    birth_datetime_utc: Annotated[
        datetime, Field(description="UTC birth datetime — needed for the yearly Tara cycle's solar-return boundaries.")
    ]
    start_utc: Annotated[datetime, Field(description="UTC start of the span to scan.")]
    end_utc: Annotated[datetime, Field(description="UTC end of the span to scan.")]
    sbc_janma_nakshatra: Annotated[
        Optional[str],
        Field(
            default=None,
            description=(
                "28-system (Abhijit-aware) token for the SBC leg, if it differs from "
                "janma_nakshatra. Defaults to janma_nakshatra."
            ),
        ),
    ] = None
    step_days: Annotated[
        int,
        Field(
            default=7,
            ge=1,
            le=90,
            description=(
                "Days between samples. Weekly by default: fine enough to locate a period, "
                "coarse enough to scan a lifetime. A window opening and closing inside one "
                "step is not seen at all."
            ),
        ),
    ] = 7
    min_techniques: Annotated[
        int,
        Field(
            default=3,
            ge=1,
            le=4,
            description=(
                "Independent techniques that must agree for a YES verdict. Only three "
                "are implemented (SBC Vedha, Latta, yearly Tara), so 3 is a strict "
                "3-of-3; Progressed Saturn would make it 3-of-4."
            ),
        ),
    ] = 3
    min_grade: Annotated[
        Literal["single", "converging", "strong"],
        Field(
            default="converging",
            description=(
                "Lowest convergence grade to report. 'converging' means at least two "
                "independent techniques agree; 'single' reports one-technique findings too "
                "and is noisy across a long span."
            ),
        ),
    ] = "converging"
    now_utc: Annotated[
        Optional[datetime],
        Field(default=None, description="Reference 'now'. Defaults to current UTC."),
    ] = None
    subject_status: Annotated[
        Literal["living", "deceased_historical"],
        Field(default="living", description="'deceased_historical' selects research/backtesting mode."),
    ] = "living"
    disclosed_events: Annotated[
        list[DisclosedEventInput],
        Field(
            default_factory=list,
            description="Life events the native reported themselves, for calibration and validation.",
        ),
    ]

    @field_validator("birth_datetime_utc", "start_utc", "end_utc", "now_utc")
    @classmethod
    def _require_tz(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("janma_nakshatra")
    @classmethod
    def _require_27_system(cls, v: str) -> str:
        token = v.strip().lower()
        if token not in _VALID_NAKSHATRAS:
            raise ValueError(f"{v!r} is not a standard 27-system nakshatra token")
        return token


class RetrodictionValidationRequest(SensitiveTimelineRequest):
    events_are_exhaustive: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "Assert that disclosed_events covers the whole scanned period. Only then is "
                "precision computed — otherwise a window with no event in it is not a false "
                "positive, merely an undisclosed one."
            ),
        ),
    ] = False


class EventSignatureResponse(BaseModel):
    """One graha striking one Sangya — the sourced event category of a hit."""

    sangya_key: str
    sangya_name: str
    graha: str
    nature: str  # "benefic" | "malefic"
    #: Worded for the window's temporal direction: classical for a
    #: retrodiction, guarded for a forecast.
    described: str


class IndicatorResponse(BaseModel):
    technique: str
    detail: str
    domains: list[str] = Field(default_factory=list)
    is_severe: bool = False
    verification: str
    polarity: str = "adverse"
    signature: Optional[EventSignatureResponse] = None


class WindowNarrativeResponse(BaseModel):
    """The sentences a native reads, rendered in the window's own voice."""

    headline: str
    body: str
    #: Sourced event categories behind the window — the "kya event" layer.
    #: A category, never a predicted event.
    categories: list[str] = Field(default_factory=list)
    #: Attached to every call, in every direction — the tradition flags a
    #: period, it does not guarantee an outcome.
    qualifier: str = ""
    #: Present when the policy requires the native be invited to confirm.
    invitation: str = ""
    #: Non-empty only if a template regressed; a bug signal, not a feature.
    redactions: list[str] = Field(default_factory=list)


class SensitiveWindowResponse(BaseModel):
    start_utc: datetime
    end_utc: datetime
    duration_days: float
    temporal_direction: str
    #: Binary answer to "kuch hoga ya nahi".
    verdict: str  # "yes" | "no"
    #: How many independent techniques agree. The verdict keys off this.
    techniques_agreeing: int
    #: "adverse" | "supportive" | "mixed" | "neutral".
    polarity: str
    #: Convergence grade across *distinct techniques*, not raw hit count.
    grade: str
    #: Days until this window opens; negative once it has begun.
    lead_time_days: float
    #: Domains flagged by more than one technique — the ones worth naming.
    domains: list[str] = Field(default_factory=list)
    #: Every domain touched, including single-technique ones.
    domains_all: list[str] = Field(default_factory=list)
    indicators: list[IndicatorResponse] = Field(default_factory=list)
    #: Which techniques fired, stayed silent, or were never run.
    techniques: dict[str, list[str]] = Field(default_factory=dict)
    #: A convergence is only as well-sourced as its weakest contributor.
    verification: str
    policy: SBCStancePolicyResponse
    narrative: WindowNarrativeResponse
    event_matches: list[SBCEventMatchResponse] = Field(default_factory=list)
    confirmed_by_disclosure: bool = False


class DisclosedEventResponse(BaseModel):
    event_id: str
    domain: str
    description: str = ""
    occurred_start_utc: datetime
    occurred_end_utc: Optional[datetime] = None
    significance: int = 3


class SensitiveTimelineResponse(BaseModel):
    janma_nakshatra: str
    start_utc: datetime
    end_utc: datetime
    now_utc: datetime
    step_days: int
    past_windows: list[SensitiveWindowResponse] = Field(default_factory=list)
    present_windows: list[SensitiveWindowResponse] = Field(default_factory=list)
    future_alerts: list[SensitiveWindowResponse] = Field(default_factory=list)
    #: Techniques in the source material that were not computed at all.
    unchecked_techniques: list[str] = Field(default_factory=list)
    #: Disclosed events no window explains — kept visible, never dropped.
    unexplained_events: list[DisclosedEventResponse] = Field(default_factory=list)


class EventOutcomeResponse(BaseModel):
    event: DisclosedEventResponse
    is_hit: bool
    #: Overlapped in time but flagged a different life domain.
    overlapped_wrong_domain: bool
    #: Overlapped in time and domain, but adverse-vs-supportive disagreed.
    polarity_mismatch: bool = False
    matched_window_start: Optional[datetime] = None
    matched_grade: Optional[str] = None
    techniques_present: list[str] = Field(default_factory=list)


class TechniqueScoreResponse(BaseModel):
    technique: str
    hits_contributed: int
    total_hits: int
    share: Optional[float] = None


class ValidationMetricsResponse(BaseModel):
    total_events: int
    hits: int
    misses: int
    overlapped_wrong_domain: int
    #: Right period and life area, but the window's polarity disagreed with
    #: the event's valence. Not a hit and not a miss.
    polarity_mismatch: int = 0
    #: Fraction of the elapsed span sitting inside a reported window.
    coverage: float
    recall: Optional[float] = None
    #: recall / coverage. 1.0 means no better than marking dates at random.
    lift: Optional[float] = None
    precision: Optional[float] = None
    precision_note: str = ""
    windows_examined: int = 0
    windows_with_a_disclosed_event: int = 0
    is_better_than_chance: Optional[bool] = None


class ValidationReportResponse(BaseModel):
    janma_nakshatra: str
    scanned_start_utc: datetime
    scanned_end_utc: datetime
    metrics: ValidationMetricsResponse
    outcomes: list[EventOutcomeResponse] = Field(default_factory=list)
    technique_scores: list[TechniqueScoreResponse] = Field(default_factory=list)
    unchecked_techniques: list[str] = Field(default_factory=list)
    missed_events: list[DisclosedEventResponse] = Field(default_factory=list)
    #: Conditions making these numbers weaker than they look.
    caveats: list[str] = Field(default_factory=list)
