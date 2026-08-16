"""AstroOS — Muhurta API schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class HoraResponse(BaseModel):
    index: int = Field(..., description="1–12 within its half (day or night)")
    lord: str = Field(..., description="Ruling Graha")
    start: datetime
    end: datetime
    is_day: bool


class InauspiciousPeriodResponse(BaseModel):
    name: str
    start: datetime
    end: datetime


class ChoghadiyaResponse(BaseModel):
    index: int = Field(..., description="1–8 within its half (day or night)")
    name: str
    nature: str = Field(..., description="'auspicious' or 'inauspicious'")
    start: datetime
    end: datetime
    is_day: bool


class MuhurtaResponse(BaseModel):
    sunrise: datetime
    sunset: datetime
    next_sunrise: datetime
    horas: list[HoraResponse]
    rahukalam: InauspiciousPeriodResponse
    gulikalam: InauspiciousPeriodResponse
    yamagandam: InauspiciousPeriodResponse
    choghadiya: list[ChoghadiyaResponse]
