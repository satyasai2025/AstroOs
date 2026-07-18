"""
AstroOS — Geocoding Service (v2 Phase A Stabilization)

Two responsibilities, deliberately kept in one small service since both
exist purely to remove "the user must already know their lat/lon/UTC
offset" from the birth-data entry flow:

1. Place-name search — proxies OpenStreetMap Nominatim (free, no API
   key). Proxied through this backend rather than called directly from
   the browser because Nominatim's usage policy requires a descriptive
   User-Agent header, which browser `fetch` cannot reliably set, and
   because centralizing the call here is the natural place to add
   caching/rate-limiting later without touching the frontend.

2. Timezone + DST resolution — `timezonefinder` maps a coordinate to an
   IANA zone name entirely offline (bundled spatial index, no network
   call), then `zoneinfo` (stdlib) resolves the actual UTC offset for
   that zone on a *specific date* — critical for historical accuracy,
   since a fixed "current UTC offset" would be wrong for a birth date
   before a DST rule change or zone boundary change. This is exactly
   the "DST information (historical if applicable)" gap flagged during
   Platform Alpha validation.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from timezonefinder import TimezoneFinder

from apps.api.domain.geocoding import PlaceResult, TimezoneResolution

_SEARCH_TIMEOUT_SECONDS = 8.0


class GeocodingService:
    """
    Constructed once per process (like EphemerisWrapper/TimezoneFinder's
    own spatial index are expensive to build) and shared via app.state —
    see apps/api/main.py's lifespan. Routers depend on
    apps.api.dependencies.get_geocoding_service instead of constructing
    their own instance.
    """

    def __init__(
        self,
        provider_url: str,
        user_agent: str,
        http_client: httpx.AsyncClient,
        timezone_finder: Optional[TimezoneFinder] = None,
    ) -> None:
        self._provider_url = provider_url
        self._user_agent = user_agent
        self._client = http_client
        self._tf = timezone_finder or TimezoneFinder()

    async def search_places(self, query: str, limit: int = 8) -> list[PlaceResult]:
        response = await self._client.get(
            self._provider_url,
            params={
                "q": query,
                "format": "jsonv2",
                "limit": limit,
                "addressdetails": 1,
            },
            headers={"User-Agent": self._user_agent},
            timeout=_SEARCH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        raw = response.json()

        results: list[PlaceResult] = []
        for item in raw:
            address = item.get("address", {})
            results.append(PlaceResult(
                display_name=item.get("display_name", ""),
                latitude=float(item["lat"]),
                longitude=float(item["lon"]),
                country=address.get("country"),
                state=address.get("state"),
            ))
        return results

    def resolve_timezone(
        self, latitude: float, longitude: float, local_date: date
    ) -> TimezoneResolution:
        """
        Raises ValueError if the coordinate doesn't map to a known
        timezone (open ocean, invalid coordinate) — a real "we can't
        resolve this" case the caller should surface, not paper over
        with a guessed offset.
        """
        tz_name = self._tf.timezone_at(lat=latitude, lng=longitude)
        if tz_name is None:
            raise ValueError(
                f"No timezone found for coordinates ({latitude}, {longitude})."
            )
        try:
            tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown IANA timezone {tz_name!r}.") from exc

        # Noon avoids the ambiguous/nonexistent local-time edge cases that
        # exist right at a DST transition instant (e.g. 02:30 on a
        # spring-forward day doesn't exist at all) — the offset at local
        # noon is what a birth-time UTC conversion actually needs.
        reference = datetime.combine(local_date, time(12, 0), tzinfo=tz)
        offset = reference.utcoffset()
        if offset is None:
            raise ValueError(f"Could not resolve UTC offset for {tz_name} on {local_date}.")

        dst = reference.dst()
        return TimezoneResolution(
            iana_name=tz_name,
            utc_offset_minutes=int(offset.total_seconds() // 60),
            is_dst=bool(dst),
        )
