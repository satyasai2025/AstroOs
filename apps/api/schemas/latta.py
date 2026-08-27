"""
AstroOS — Latta Dosha API Schemas

Note the two sourcing-status fields carried on the response
(``verification`` and ``named_combinations_status``). They are part of
the payload rather than documentation because a client rendering a
Latta reading needs to state the tier alongside it — see
``packages/shared/latta.py`` for what each tier means.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from apps.api.schemas.ai import DisclosedEventInput
from apps.api.schemas.sbc import SBCEventMatchResponse, SBCStancePolicyResponse
from packages.shared.enums import Nakshatra

_VALID_NAKSHATRAS = frozenset(n.value for n in Nakshatra)


class LattaReportRequest(BaseModel):
    janma_nakshatra: Annotated[
        str,
        Field(description="Standard 27-system nakshatra token to test for Latta affliction, e.g. 'rohini'."),
    ]
    moment_utc: Annotated[
        Optional[datetime],
        Field(default=None, description="UTC moment to compute Latta at. Defaults to the current UTC time."),
    ] = None
    now_utc: Annotated[
        Optional[datetime],
        Field(
            default=None,
            description="Reference 'now' for past/present/future classification. Defaults to current UTC.",
        ),
    ] = None
    subject_status: Annotated[
        Literal["living", "deceased_historical"],
        Field(
            default="living",
            description="'deceased_historical' selects research/backtesting mode for a documented figure.",
        ),
    ] = "living"
    disclosed_events: Annotated[
        list[DisclosedEventInput],
        Field(
            default_factory=list,
            description=(
                "Life events the native reported themselves. An event in a struck life domain, "
                "overlapping this moment, lets the reading be stated in the native's own terms."
            ),
        ),
    ]

    @field_validator("moment_utc", "now_utc")
    @classmethod
    def _require_tz(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("janma_nakshatra")
    @classmethod
    def _require_27_system_token(cls, v: str) -> str:
        """Reject 28-system tokens at the edge rather than deep in the engine.

        Latta is reckoned on the 27-star circle, so 'abhijit' is a category
        error here — a 422 says that far more usefully than a 500 would.
        """
        token = v.strip().lower()
        if token not in _VALID_NAKSHATRAS:
            raise ValueError(
                f"{v!r} is not a standard 27-system nakshatra token "
                "(Latta is reckoned on the 27-star circle, so 'abhijit' is not valid here)"
            )
        return token


class LattaHitResponse(BaseModel):
    planet: str
    from_nakshatra: str
    struck_nakshatra: str
    offset: int
    direction: str  # "forward" | "backward"
    is_malefic: bool
    #: Malefic graha kicking forward — the heavier of the two axes.
    is_severe: bool
    domains: list[str] = Field(default_factory=list)
    verification: str


class LattaReportResponse(BaseModel):
    janma_nakshatra: str
    moment_utc: datetime
    is_afflicted: bool
    hits: list[LattaHitResponse] = Field(default_factory=list)
    severe_hit_count: int = 0
    #: Where each Latta-carrying graha currently stands.
    transit_nakshatras: dict[str, str] = Field(default_factory=dict)
    #: Life areas struck. This is the finest granularity the technique reports;
    #: naming a specific event is governed by ``policy``.
    domains_struck: list[str] = Field(default_factory=list)
    policy: SBCStancePolicyResponse
    event_matches: list[SBCEventMatchResponse] = Field(default_factory=list)
    confirmed_by_disclosure: bool = False
    #: Sourcing tier of the offset table actually used for this computation.
    verification: str = "standard_unverified"
    #: The seven named Sun-reckoned combinations remain unsourced; this states so.
    named_combinations_status: dict[str, Any] = Field(default_factory=dict)
