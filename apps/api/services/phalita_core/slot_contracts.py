"""
AstroOS — Gap 3: Slot-Based Synthesis Contract.

Core invariant: The LLM never asserts. It RENDERS pre-scored findings by
filling slots. Every narrative fragment is bound to exactly one finding_id;
the binding is validated at decode time (schema stage), then re-verified
symbolically (claim-graph stage). Unbound assertion = hard reject,
deterministically, with no model in the loop.
"""
from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Annotated, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class SlotType(str, Enum):
    STATE_LEVEL      = "state_level"       # standing natal condition
    EVENT_LIKELIHOOD = "event_likelihood"  # probability-bearing prediction
    TIMING_WINDOW    = "timing_window"     # temporal localization
    CONFLICT_NOTE    = "conflict_note"     # mixed indications (bhanga)
    ABSTENTION       = "abstention"        # insufficient-confluence statement
    REMEDIATION_REF  = "remediation_ref"   # classical prescription reference


class CertaintyTier(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    TENTATIVE = "tentative"
    INSUFFICIENT = "insufficient"


class SlotRender(BaseModel):
    finding_id: str = Field(
        ..., pattern=r"^FND-[A-Z0-9-]+$",
        description="MUST exist in the finding set injected into the prompt.",
    )
    slot_type: SlotType
    text: str = Field(..., min_length=15, max_length=1200)
    citations: List[str] = Field(
        default_factory=list,
        description="Citation IDs — must be a SUBSET of the finding's attached citations.",
    )
    temporal_refs: List[str] = Field(
        default_factory=list,
        description="ISO dates/years asserted in this slot text.",
    )
    tier_echo: CertaintyTier


class SlotManifest(BaseModel):
    """Top-level LLM output — nothing else is accepted."""
    subject_ref: str
    domain: Literal["career", "marriage", "health", "finance", "accident"]
    slots: List[SlotRender] = Field(..., min_length=1)

    has_likelihood_slot: bool
    has_abstention_if_insufficient: bool

    @model_validator(mode="after")
    def structural(self) -> SlotManifest:
        types = [s.slot_type for s in self.slots]
        if self.has_likelihood_slot != (SlotType.EVENT_LIKELIHOOD in types):
            raise ValueError("has_likelihood_slot flag inconsistent with slots")
        if self.has_abstention_if_insufficient and SlotType.ABSTENTION not in types:
            raise ValueError("Findings include insufficient-tier claims; manifest must carry an explicit ABSTENTION slot.")
        return self
