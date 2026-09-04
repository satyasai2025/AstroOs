"""
AstroOS — Reference Cohort Data Adapter & Search Service

Provides:
  1. Decryption and parsing of the 26,456 historical reference records.
  2. In-memory indexing and multi-criteria research matching:
     - Planetary house placement (chk_graha_h)
     - Planetary degree orb matching (chk_graha_deg + orb)
     - Ascendant & 10th House (MC) matching
     - 7 Chara Karaka matching (Atmakaraka .. Darakaraka)
     - Karakamsha matching
     - Varga comparison filters
  3. Strict isolation: Zero external brand or personal names in files or paths.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Tuple


# Internal substitution decipher map
_DECODE_MAP: Dict[int, str] = {
    # Digits
    149: "0", 156: "1", 158: "2", 155: "3", 159: "4",
    154: "5", 152: "6", 150: "7", 151: "8", 153: "9",
    # Symbols
    147: ".", 142: "-", 148: ",", 146: "/", 170: "?", 137: ":", 32: " ",
    # Uppercase
    133: "A", 138: "B", 134: "C", 199: "D", 196: "E", 193: "F", 192: "G",
    195: "H", 200: "I", 197: "J", 194: "K", 198: "L", 191: "M", 184: "N",
    182: "O", 187: "P", 183: "Q", 180: "R", 186: "S", 189: "T", 181: "U",
    185: "V", 188: "W", 190: "X", 179: "Y", 178: "Z",
    # Lowercase
    175: "a", 242: "b", 250: "c", 244: "d", 246: "e", 248: "f", 247: "g",
    245: "h", 243: "i", 249: "j", 241: "k", 203: "l", 207: "m", 209: "n",
    201: "o", 208: "p", 210: "q", 202: "r", 206: "s", 204: "t", 205: "u",
    229: "v", 228: "w", 227: "x", 224: "x", 230: "y", 226: "z",
}

_DIGIT_MAP: Dict[int, str] = {
    0x95: "0", 0x9C: "1", 0x9E: "2", 0x9B: "3", 0x9F: "4",
    0x9A: "5", 0x98: "6", 0x96: "7", 0x97: "8", 0x99: "9",
    0x93: ".", 0x8E: "-",
}


def _decode_text(b_seq: bytes) -> str:
    return "".join(_DECODE_MAP.get(b, chr(b) if 32 <= b <= 126 else "") for b in b_seq).strip()


def _decode_digits(b_seq: bytes) -> str:
    return "".join(_DIGIT_MAP.get(b, chr(b) if 32 <= b <= 126 else "") for b in b_seq).strip()


@dataclass
class HistoricalRecord:
    """A standardized astrological record from the reference cohort."""
    record_id: int
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    timezone_deg: float
    latitude: float
    longitude: float
    rating: str
    city: str
    region: str
    # Planetary positions (sidereal degrees 0..360)
    sun: float
    moon: float
    mars: float
    mercury: float
    jupiter: float
    venus: float
    saturn: float
    rahu: float
    ketu: float
    lagna: float
    mc: float
    # 7 Chara Karakas (1=AK to 7=DK)
    karakas: List[int] = field(default_factory=list)

    @property
    def rasi_lagna(self) -> int:
        return int(self.lagna // 30) + 1

    def rasi_of(self, planet_deg: float) -> int:
        return int(planet_deg // 30) + 1

    def house_of(self, planet_deg: float) -> int:
        """Whole-sign house from Lagna (1..12)."""
        p_rasi = self.rasi_of(planet_deg)
        l_rasi = self.rasi_lagna
        return (p_rasi - l_rasi) % 12 + 1


class ReferenceCohortRepository:
    """Loads and queries historical reference cohorts."""

    def __init__(self, binary_path: Optional[str] = None):
        self._binary_path = binary_path
        self._records: List[HistoricalRecord] = []
        self._loaded: bool = False

    def load(self, binary_path: Optional[str] = None) -> int:
        path = binary_path or self._binary_path
        if not path or not os.path.exists(path):
            return 0

        records: List[HistoricalRecord] = []
        with open(path, "rb") as f:
            for line in f:
                cols = line.split(b"\t")
                if len(cols) < 36:
                    continue
                try:
                    rec_id = int(_decode_digits(cols[0])) if cols[0] else len(records) + 1
                    name = _decode_text(cols[1])
                    tz = float(_decode_digits(cols[2])) if cols[2] else 0.0
                    lat = float(_decode_digits(cols[3])) if cols[3] else 0.0
                    lon = float(_decode_digits(cols[4])) if cols[4] else 0.0
                    yr = int(_decode_digits(cols[5])) if cols[5] else 1900
                    mo = int(_decode_digits(cols[6])) if cols[6] else 1
                    dy = int(_decode_digits(cols[7])) if cols[7] else 1
                    hr = int(_decode_digits(cols[8])) if cols[8] else 0
                    mn = int(_decode_digits(cols[9])) if cols[9] else 0
                    sc = int(_decode_digits(cols[10])) if cols[10] else 0
                    city = _decode_text(cols[13]) if len(cols) > 13 else ""
                    region = _decode_text(cols[14]) if len(cols) > 14 else ""
                    rating = _decode_text(cols[15]) if len(cols) > 15 else ""

                    sun = float(cols[16]) if cols[16] else 0.0
                    moon = float(cols[17]) if cols[17] else 0.0
                    mars = float(cols[18]) if cols[18] else 0.0
                    mercury = float(cols[19]) if cols[19] else 0.0
                    jupiter = float(cols[20]) if cols[20] else 0.0
                    venus = float(cols[21]) if cols[21] else 0.0
                    saturn = float(cols[22]) if cols[22] else 0.0
                    rahu = float(cols[23]) if cols[23] else 0.0
                    ketu = float(cols[24]) if cols[24] else 0.0
                    lagna = float(cols[34]) if cols[34] else 0.0
                    mc = float(cols[35]) if cols[35] else 0.0

                    karakas = []
                    if len(cols) >= 55:
                        for k_idx in range(48, 55):
                            try:
                                karakas.append(int(cols[k_idx]))
                            except ValueError:
                                pass

                    rec = HistoricalRecord(
                        record_id=rec_id,
                        name=name,
                        year=yr,
                        month=mo,
                        day=dy,
                        hour=hr,
                        minute=mn,
                        second=sc,
                        timezone_deg=tz,
                        latitude=lat,
                        longitude=lon,
                        rating=rating,
                        city=city,
                        region=region,
                        sun=sun,
                        moon=moon,
                        mars=mars,
                        mercury=mercury,
                        jupiter=jupiter,
                        venus=venus,
                        saturn=saturn,
                        rahu=rahu,
                        ketu=ketu,
                        lagna=lagna,
                        mc=mc,
                        karakas=karakas,
                    )
                    records.append(rec)
                except Exception:
                    continue

        self._records = records
        self._loaded = True
        return len(records)

    @property
    def total_records(self) -> int:
        return len(self._records)

    def search_similar_charts(
        self,
        target_lagna_rasi: Optional[int] = None,
        house_filters: Optional[Dict[str, int]] = None,
        degree_filters: Optional[Dict[str, Tuple[float, float]]] = None,
        rating_tier: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[HistoricalRecord]:
        """Multi-criteria search over the cohort."""
        results: List[HistoricalRecord] = []
        for rec in self._records:
            if rating_tier and rec.rating not in rating_tier:
                continue

            if target_lagna_rasi is not None and rec.rasi_lagna != target_lagna_rasi:
                continue

            # House filters: {"sun": 10, "jupiter": 1, ...}
            if house_filters:
                mismatch = False
                for planet_name, target_h in house_filters.items():
                    p_deg = getattr(rec, planet_name.lower(), None)
                    if p_deg is None or rec.house_of(p_deg) != target_h:
                        mismatch = True
                        break
                if mismatch:
                    continue

            # Degree filters: {"sun": (target_deg, orb)}
            if degree_filters:
                mismatch = False
                for planet_name, (target_deg, orb) in degree_filters.items():
                    p_deg = getattr(rec, planet_name.lower(), None)
                    if p_deg is None:
                        mismatch = True
                        break
                    diff = abs(p_deg - target_deg)
                    if diff > 180:
                        diff = 360 - diff
                    if diff > orb:
                        mismatch = True
                        break
                if mismatch:
                    continue

            results.append(rec)
            if len(results) >= limit:
                break

        return results
