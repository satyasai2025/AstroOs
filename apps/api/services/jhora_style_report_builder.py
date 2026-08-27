"""
AstroOS — Jagannatha Hora style report data assembly.

The client's reference output is a JHora sheet: one dense "Body" table listing
the lagna, the nine grahas (with their chara karaka inline), the upagrahas and
the special lagnas — followed by the Rasi and Navamsa charts and the nested
Vimshottari dasa grid. It deliberately does NOT print sixteen varga charts;
that was the wrong read of the brief.

This module only RESHAPES canonical output for that presentation:

    BirthChartReportBuilder   -> lagna + graha rows, panchanga, charts, dasha
    UpagrahaEngine            -> Gulika/Maandi etc. and Bhava/Hora/Ghati lagna

No astrological quantity is computed here. Per the report tier spec's data
integrity rule, if a value is wrong the fix belongs in the engine that
produced it.

Known gap vs the JHora reference: it also prints Uranus, Neptune and Pluto.
AstroOS's ephemeris layer does not expose the outer planets, so they are
omitted rather than fabricated.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from apps.api.services.upagraha_engine import UpagrahaEngine

RASHI_ABBR = {
    "aries": "Ar", "taurus": "Ta", "gemini": "Ge", "cancer": "Cn",
    "leo": "Le", "virgo": "Vi", "libra": "Li", "scorpio": "Sc",
    "sagittarius": "Sg", "capricorn": "Cp", "aquarius": "Aq", "pisces": "Pi",
}

# Presentation order and display names, matching the reference sheet.
UPAGRAHA_LABELS = [
    ("gulika", "Gulika"),
    ("maandi", "Maandi"),
]
SPECIAL_LAGNA_LABELS = [
    ("bhava_lagna", "Bhava Lagna"),
    ("hora_lagna", "Hora Lagna"),
    ("ghati_lagna", "Ghati Lagna"),
]


def _titleise(value: str) -> str:
    """'uttara_phalguni' -> 'Uttara Phalguni'."""
    return " ".join(part.capitalize() for part in value.replace("_", " ").split())


def jhora_longitude(rashi_degree: float, rashi: str) -> str:
    """
    Format a position the way JHora prints it: ``23 Ta 38' 03"``.

    Degrees are the degrees WITHIN the sign, not the absolute longitude —
    the sign abbreviation carries the rest.
    """
    deg = int(rashi_degree)
    minutes_full = (rashi_degree - deg) * 60
    minutes = int(minutes_full)
    seconds = int(round((minutes_full - minutes) * 60))
    if seconds == 60:                      # carry, so 59'60" never prints
        seconds, minutes = 0, minutes + 1
    if minutes == 60:
        minutes, deg = 0, deg + 1
    abbr = RASHI_ABBR.get(rashi.strip().lower(), rashi[:2].title())
    return f"{deg:2d} {abbr} {minutes:02d}' {seconds:02d}\""


class JHoraStyleReportBuilder:
    """Adds the derived-point rows the JHora sheet shows below the grahas."""

    def __init__(self, wrapper: Any) -> None:
        self._upagraha_engine = UpagrahaEngine(wrapper)

    def build_derived_rows(
        self,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
    ) -> list[dict[str, Any]]:
        """
        Return the Gulika/Maandi and Bhava/Hora/Ghati-Lagna rows, shaped like
        the graha rows so one template loop renders both.

        Navamsa is intentionally blank for these points: the upagraha engine
        does not currently emit a navamsa placement for them, and inventing
        one would put an uncomputed value in a reference sheet.
        """
        result = self._upagraha_engine.compute(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )

        by_name = {u.name: u for u in result.upagrahas}
        lagnas = {l.name: l for l in result.special_lagnas}

        rows: list[dict[str, Any]] = []

        for key, label in UPAGRAHA_LABELS:
            pos = by_name.get(key)
            if pos is None:
                continue
            rows.append(self._row(label, pos))

        for key, label in SPECIAL_LAGNA_LABELS:
            pos = lagnas.get(key)
            if pos is None:
                continue
            rows.append(self._row(label, pos))

        return rows

    @staticmethod
    def _row(label: str, pos: Any) -> dict[str, Any]:
        return {
            "name": label,
            "symbol": "",
            "karaka": "",
            "longitude_jhora": jhora_longitude(pos.rashi_degree, pos.rashi),
            "nakshatra": _titleise(pos.nakshatra),
            "pada": pos.pada,
            "rashi_abbr": RASHI_ABBR.get(pos.rashi.lower(), pos.rashi[:2].title()),
            "navamsa_abbr": "",
            "house": pos.house_number,
            "is_derived": True,
        }

    @staticmethod
    def decorate_graha_rows(planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Add the JHora longitude string to rows produced by
        BirthChartReportBuilder, leaving every existing key untouched.

        `degree_dms` there is already formatted as ``08° 56' 15"``; JHora
        instead interleaves the sign, so the string is rebuilt from the parts
        rather than string-patched.
        """
        out: list[dict[str, Any]] = []
        for p in planets:
            row = dict(p)
            dms = p.get("degree_dms", "")
            abbr = p.get("rashi_abbr", "")
            # "08° 56' 15\"" -> "08 Aq 56' 15\""
            row["longitude_jhora"] = dms.replace("°", f" {abbr}", 1) if dms else ""
            row["is_derived"] = False
            out.append(row)
        return out
