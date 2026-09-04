"""
AstroOS — Divisional (Varga) chart grid builder.

Assembles the varga charts that the Detailed birth report renders as pages of
six, in the layout of the Jagannatha Hora reference output.

ARCHITECTURAL NOTE (report tier spec, section 7 "Data Integrity"):
this module does NOT compute any varga mathematics. It calls the canonical
`DivisionalEngine` and reshapes its output for the renderer. If a varga
placement is ever wrong, the fix belongs in DivisionalEngine — never here.

Layout constraint: the grid partial (`templates/reports/_varga_grid.html`)
fits exactly 6 charts per A4 page, so `page_chunks()` slices accordingly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Sequence

from apps.api.services.chart_svg_renderer import render_north_indian_svg
from apps.api.services.divisional_engine import SUPPORTED_VARGAS, DivisionalEngine

# Charts per A4 page — must stay in step with _varga_grid.html (2 cols x 3 rows).
CHARTS_PER_PAGE = 6

RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_RASHI_INDEX = {name.lower(): i for i, name in enumerate(RASHI_NAMES)}

PLANET_ABBR = {
    "sun": "Su", "moon": "Mo", "mars": "Ma", "mercury": "Me",
    "jupiter": "Ju", "venus": "Ve", "saturn": "Sa",
    "rahu": "Ra", "ketu": "Ke",
}

# Classical Shodashavarga names. D1 and D9 are excluded here because the
# Foundation page already carries them full-size; this grid covers the rest.
VARGA_NAMES: dict[str, str] = {
    "D2": "Hora", "D3": "Drekkana", "D4": "Chaturthamsha", "D5": "Panchamsha",
    "D6": "Shashthamsha", "D7": "Saptamsha", "D8": "Ashtamsha",
    "D10": "Dasamsha", "D11": "Rudramsha", "D12": "Dvadashamsha",
    "D16": "Shodashamsha", "D20": "Vimshamsha", "D24": "Chaturvimshamsha",
    "D27": "Bhamsha", "D30": "Trimshamsha", "D40": "Khavedamsha",
    "D45": "Akshavedamsha", "D60": "Shashtiamsha",
}

# Default set for the Detailed report: the Shodashavarga minus D1/D9, which is
# 14 charts -> 3 grid pages (6 + 6 + 2).
DEFAULT_VARGAS: tuple[str, ...] = (
    "D2", "D3", "D4", "D7", "D10", "D12", "D16",
    "D20", "D24", "D27", "D30", "D40", "D45", "D60",
)


def _rashi_index(rashi: str) -> int:
    """0-based index for a rashi name as emitted by DivisionalEngine."""
    try:
        return _RASHI_INDEX[rashi.strip().lower()]
    except KeyError as exc:  # pragma: no cover - guards a contract change
        raise ValueError(f"unknown rashi from DivisionalEngine: {rashi!r}") from exc


class VargaGridBuilder:
    """Builds render-ready varga chart descriptors from canonical output."""

    def __init__(self, wrapper: Any) -> None:
        self._engine = DivisionalEngine(wrapper)

    def build(
        self,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        vargas: Sequence[str] = DEFAULT_VARGAS,
        ayanamsa: str = "lahiri",
        svg_size: int = 190,
    ) -> list[dict[str, Any]]:
        """
        Return one descriptor per varga:
            {code, name, divisor, ascendant, svg}

        Unsupported codes raise rather than being silently dropped — a missing
        chart in a paid report should fail loudly, not vanish.
        """
        unknown = [v for v in vargas if v not in SUPPORTED_VARGAS]
        if unknown:
            raise ValueError(
                f"unsupported varga(s): {unknown}. "
                f"Supported: {sorted(SUPPORTED_VARGAS)}"
            )

        charts: list[dict[str, Any]] = []
        for code in vargas:
            vc = self._engine.compute(
                birth_datetime_utc=birth_datetime_utc,
                latitude=latitude,
                longitude=longitude,
                varga=code,
                ayanamsa=ayanamsa,
            )

            asc_idx = _rashi_index(vc.ascendant.varga_rashi)

            houses: dict[int, list[str]] = {}
            for pos in vc.planet_positions:
                abbr = PLANET_ABBR.get(pos.planet.lower(), pos.planet[:2].title())
                houses.setdefault(pos.varga_house_number, []).append(abbr)

            charts.append(
                {
                    "code": code,
                    "name": VARGA_NAMES.get(code, code),
                    "divisor": SUPPORTED_VARGAS[code],
                    "ascendant": RASHI_NAMES[asc_idx],
                    "svg": render_north_indian_svg(
                        ascendant_rashi_num=asc_idx + 1,
                        planets_in_houses=houses,
                        chart_title="",          # caption is drawn by the grid
                        width=svg_size,
                        height=svg_size,
                    ),
                }
            )
        return charts

    @staticmethod
    def page_chunks(
        charts: Sequence[dict[str, Any]],
        per_page: int = CHARTS_PER_PAGE,
    ) -> list[list[dict[str, Any]]]:
        """Slice charts into per-page groups matching the grid's capacity."""
        return [
            list(charts[i : i + per_page])
            for i in range(0, len(charts), per_page)
        ]
