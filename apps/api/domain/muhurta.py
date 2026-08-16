"""
AstroOS — Muhurta domain models.

Hora (planetary hours) and the three classical inauspicious day-segments
(Rahukalam, Gulikalam, Yamagandam), all derived from sunrise/sunset —
not clock time — matching the method used by Drik Panchang and other
mainstream panchang references.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HoraPeriod:
    """One of the 24 unequal-length planetary hours spanning a solar day+night."""
    index: int            # 1–12 within its half (day or night)
    lord: str              # ruling Graha
    start_jd: float
    end_jd: float
    is_day: bool            # True = between sunrise and sunset


@dataclass(frozen=True)
class InauspiciousPeriod:
    """A single 1/8-of-daylight inauspicious segment (Rahukalam / Gulikalam / Yamagandam)."""
    name: str               # "rahukalam" | "gulikalam" | "yamagandam"
    start_jd: float
    end_jd: float


@dataclass(frozen=True)
class ChoghadiyaPeriod:
    """One of the 8 day or 8 night Choghadiya segments (1/8 of daylight or night)."""
    index: int              # 1–8 within its half (day or night)
    name: str               # Udveg | Chal | Labh | Amrit | Kaal | Shubh | Rog
    nature: str              # "auspicious" | "inauspicious" — the 7 Choghadiya names split 4/3
    start_jd: float
    end_jd: float
    is_day: bool


@dataclass(frozen=True)
class MuhurtaResult:
    """Muhurta timings for one calendar day at a given location."""
    sunrise_jd: float
    sunset_jd: float
    next_sunrise_jd: float
    horas: list[HoraPeriod]
    rahukalam: InauspiciousPeriod
    gulikalam: InauspiciousPeriod
    yamagandam: InauspiciousPeriod
    choghadiya: list[ChoghadiyaPeriod]
