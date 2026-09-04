"""
AstroOS — Geocoding Service (v2 Phase A Stabilization)

Two responsibilities:
1. Place-name search — multi-provider resilient search:
   - Primary: OpenStreetMap Nominatim
   - Fallback 1: Photon OSM API
   - Fallback 2: Built-in Offline Cities Database (major Indian & world cities)
2. Timezone + DST resolution — `timezonefinder` maps coordinate to IANA zone,
   then `zoneinfo` resolves exact UTC offset for the given date.
3. IP Geolocation — fallback for instant device location detection.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from timezonefinder import TimezoneFinder

from apps.api.domain.geocoding import PlaceResult, TimezoneResolution

logger = logging.getLogger(__name__)

_SEARCH_TIMEOUT_SECONDS = 6.0

# Curated offline database of prominent Indian astrological/mundane cities and global metros
_OFFLINE_CITIES: list[tuple[str, float, float, str, str]] = [
    ("New Delhi", 28.6139, 77.2090, "Delhi", "India"),
    ("Delhi", 28.6139, 77.2090, "Delhi", "India"),
    ("Varanasi", 25.3176, 82.9739, "Uttar Pradesh", "India"),
    ("Kashi", 25.3176, 82.9739, "Uttar Pradesh", "India"),
    ("Ujjain", 23.1765, 75.7885, "Madhya Pradesh", "India"),
    ("Ayodhya", 26.7922, 82.1998, "Uttar Pradesh", "India"),
    ("Mathura", 27.4924, 77.6737, "Uttar Pradesh", "India"),
    ("Haridwar", 29.9457, 78.1642, "Uttarakhand", "India"),
    ("Rishikesh", 30.0869, 78.2676, "Uttarakhand", "India"),
    ("Prayagraj", 25.4358, 81.8463, "Uttar Pradesh", "India"),
    ("Allahabad", 25.4358, 81.8463, "Uttar Pradesh", "India"),
    ("Puri", 19.8135, 85.8312, "Odisha", "India"),
    ("Dwarka", 22.2394, 68.9678, "Gujarat", "India"),
    ("Rameswaram", 9.2876, 79.3129, "Tamil Nadu", "India"),
    ("Tirupati", 13.6288, 79.4192, "Andhra Pradesh", "India"),
    ("Madurai", 9.9252, 78.1198, "Tamil Nadu", "India"),
    ("Kanchipuram", 12.8342, 79.7036, "Tamil Nadu", "India"),
    ("Gaya", 24.7914, 85.0002, "Bihar", "India"),
    ("Nashik", 19.9975, 73.7898, "Maharashtra", "India"),
    ("Shirdi", 19.7667, 74.4762, "Maharashtra", "India"),
    ("Kedarnath", 30.7346, 79.0669, "Uttarakhand", "India"),
    ("Badrinath", 30.7433, 79.4938, "Uttarakhand", "India"),
    ("Somnath", 20.8880, 70.4012, "Gujarat", "India"),
    ("Mumbai", 19.0760, 72.8777, "Maharashtra", "India"),
    ("Bombay", 19.0760, 72.8777, "Maharashtra", "India"),
    ("Pune", 18.5204, 73.8567, "Maharashtra", "India"),
    ("Nagpur", 21.1458, 79.0882, "Maharashtra", "India"),
    ("Bengaluru", 12.9716, 77.5946, "Karnataka", "India"),
    ("Bangalore", 12.9716, 77.5946, "Karnataka", "India"),
    ("Mysuru", 12.2958, 76.6394, "Karnataka", "India"),
    ("Mysore", 12.2958, 76.6394, "Karnataka", "India"),
    ("Mangalore", 12.9141, 74.8560, "Karnataka", "India"),
    ("Hyderabad", 17.3850, 78.4867, "Telangana", "India"),
    ("Secunderabad", 17.4399, 78.4983, "Telangana", "India"),
    ("Chennai", 13.0827, 80.2707, "Tamil Nadu", "India"),
    ("Madras", 13.0827, 80.2707, "Tamil Nadu", "India"),
    ("Coimbatore", 11.0168, 76.9558, "Tamil Nadu", "India"),
    ("Kolkata", 22.5726, 88.3639, "West Bengal", "India"),
    ("Calcutta", 22.5726, 88.3639, "West Bengal", "India"),
    ("Ahmedabad", 23.0225, 72.5714, "Gujarat", "India"),
    ("Surat", 21.1702, 72.8311, "Gujarat", "India"),
    ("Vadodara", 22.3072, 73.1812, "Gujarat", "India"),
    ("Rajkot", 22.3039, 70.8022, "Gujarat", "India"),
    ("Jaipur", 26.9124, 75.7873, "Rajasthan", "India"),
    ("Jodhpur", 26.2389, 73.0243, "Rajasthan", "India"),
    ("Udaipur", 24.5854, 73.7125, "Rajasthan", "India"),
    ("Kota", 25.2138, 75.8648, "Rajasthan", "India"),
    ("Bikaner", 28.0229, 73.3119, "Rajasthan", "India"),
    ("Ajmer", 26.4499, 74.6399, "Rajasthan", "India"),
    ("Lucknow", 26.8467, 80.9462, "Uttar Pradesh", "India"),
    ("Kanpur", 26.4499, 80.3319, "Uttar Pradesh", "India"),
    ("Agra", 27.1767, 78.0081, "Uttar Pradesh", "India"),
    ("Noida", 28.5355, 77.3910, "Uttar Pradesh", "India"),
    ("Ghaziabad", 28.6692, 77.4538, "Uttar Pradesh", "India"),
    ("Meerut", 28.9845, 77.7064, "Uttar Pradesh", "India"),
    ("Gorakhpur", 26.7606, 83.3732, "Uttar Pradesh", "India"),
    ("Bareilly", 28.3670, 79.4304, "Uttar Pradesh", "India"),
    ("Aligarh", 27.8974, 78.0880, "Uttar Pradesh", "India"),
    ("Jhansi", 25.4484, 78.5685, "Uttar Pradesh", "India"),
    ("Patna", 25.5941, 85.1376, "Bihar", "India"),
    ("Muzaffarpur", 26.1209, 85.3647, "Bihar", "India"),
    ("Bhagalpur", 25.2425, 86.9842, "Bihar", "India"),
    ("Darbhanga", 26.1542, 85.8918, "Bihar", "India"),
    ("Ranchi", 23.3441, 85.3096, "Jharkhand", "India"),
    ("Jamshedpur", 22.8046, 86.2029, "Jharkhand", "India"),
    ("Dhanbad", 23.7957, 86.4304, "Jharkhand", "India"),
    ("Bhopal", 23.2599, 77.4126, "Madhya Pradesh", "India"),
    ("Indore", 22.7196, 75.8577, "Madhya Pradesh", "India"),
    ("Gwalior", 26.2183, 78.1828, "Madhya Pradesh", "India"),
    ("Jabalpur", 23.1815, 79.9864, "Madhya Pradesh", "India"),
    ("Chandigarh", 30.7333, 76.7794, "Chandigarh", "India"),
    ("Ludhiana", 30.9010, 75.8573, "Punjab", "India"),
    ("Amritsar", 31.6340, 74.8723, "Punjab", "India"),
    ("Jalandhar", 31.3260, 75.5762, "Punjab", "India"),
    ("Gurugram", 28.4595, 77.0266, "Haryana", "India"),
    ("Gurgaon", 28.4595, 77.0266, "Haryana", "India"),
    ("Faridabad", 28.4089, 77.3178, "Haryana", "India"),
    ("Panipat", 29.3909, 76.9635, "Haryana", "India"),
    ("Dehradun", 30.3165, 78.0322, "Uttarakhand", "India"),
    ("Shimla", 31.1048, 77.1734, "Himachal Pradesh", "India"),
    ("Dharamshala", 32.2190, 76.3234, "Himachal Pradesh", "India"),
    ("Srinagar", 34.0837, 74.7973, "Jammu and Kashmir", "India"),
    ("Jammu", 32.7266, 74.8570, "Jammu and Kashmir", "India"),
    ("Guwahati", 26.1445, 91.7362, "Assam", "India"),
    ("Bhubaneswar", 20.2961, 85.8245, "Odisha", "India"),
    ("Cuttack", 20.4625, 85.8828, "Odisha", "India"),
    ("Raipur", 21.2514, 81.6296, "Chhattisgarh", "India"),
    ("Thiruvananthapuram", 8.5241, 76.9366, "Kerala", "India"),
    ("Trivandrum", 8.5241, 76.9366, "Kerala", "India"),
    ("Kochi", 9.9312, 76.2673, "Kerala", "India"),
    ("Cochin", 9.9312, 76.2673, "Kerala", "India"),
    ("Kozhikode", 11.2588, 75.7804, "Kerala", "India"),
    ("Calicut", 11.2588, 75.7804, "Kerala", "India"),
    ("Visakhapatnam", 17.6868, 83.2185, "Andhra Pradesh", "India"),
    ("Vijayawada", 16.5062, 80.6480, "Andhra Pradesh", "India"),
    ("Panaji", 15.4909, 73.8278, "Goa", "India"),
    ("Goa", 15.2993, 74.1240, "Goa", "India"),

    # Major World Cities & Financial Hubs
    ("London", 51.5074, -0.1278, "England", "United Kingdom"),
    ("New York", 40.7128, -74.0060, "New York", "United States"),
    ("New York City", 40.7128, -74.0060, "New York", "United States"),
    ("San Francisco", 37.7749, -122.4194, "California", "United States"),
    ("Los Angeles", 34.0522, -118.2437, "California", "United States"),
    ("Chicago", 41.8781, -87.6298, "Illinois", "United States"),
    ("Houston", 29.7604, -95.3698, "Texas", "United States"),
    ("Dallas", 32.7767, -96.7970, "Texas", "United States"),
    ("Austin", 30.2672, -97.7431, "Texas", "United States"),
    ("Seattle", 47.6062, -122.3321, "Washington", "United States"),
    ("Boston", 42.3601, -71.0589, "Massachusetts", "United States"),
    ("Washington DC", 38.9072, -77.0369, "District of Columbia", "United States"),
    ("Toronto", 43.6532, -79.3832, "Ontario", "Canada"),
    ("Vancouver", 49.2827, -123.1207, "British Columbia", "Canada"),
    ("Montreal", 45.5017, -73.5673, "Quebec", "Canada"),
    ("Dubai", 25.2048, 55.2708, "Dubai", "United Arab Emirates"),
    ("Abu Dhabi", 24.4539, 54.3773, "Abu Dhabi", "United Arab Emirates"),
    ("Doha", 25.2854, 51.5310, "Doha", "Qatar"),
    ("Riyadh", 24.7136, 46.6753, "Riyadh", "Saudi Arabia"),
    ("Singapore", 1.3521, 103.8198, "Central", "Singapore"),
    ("Tokyo", 35.6762, 139.6503, "Tokyo", "Japan"),
    ("Hong Kong", 22.3193, 114.1694, "Hong Kong", "China"),
    ("Sydney", -33.8688, 151.2093, "New South Wales", "Australia"),
    ("Melbourne", -37.8136, 144.9631, "Victoria", "Australia"),
    ("Brisbane", -27.4698, 153.0251, "Queensland", "Australia"),
    ("Auckland", -36.8485, 174.7633, "Auckland", "New Zealand"),
    ("Paris", 48.8566, 2.3522, "Île-de-France", "France"),
    ("Berlin", 52.5200, 13.4050, "Berlin", "Germany"),
    ("Frankfurt", 50.1109, 8.6821, "Hesse", "Germany"),
    ("Rome", 41.9028, 12.4964, "Lazio", "Italy"),
    ("Madrid", 40.4168, -3.7038, "Madrid", "Spain"),
    ("Amsterdam", 52.3676, 4.9041, "North Holland", "Netherlands"),
    ("Zurich", 47.3769, 8.5417, "Zurich", "Switzerland"),
    ("Geneva", 46.2044, 6.1432, "Geneva", "Switzerland"),
    ("Moscow", 55.7558, 37.6173, "Moscow", "Russia"),
    ("Bangkok", 13.7563, 100.5018, "Bangkok", "Thailand"),
    ("Kuala Lumpur", 3.1390, 101.6869, "Federal Territory", "Malaysia"),
    ("Jakarta", -6.2088, 106.8456, "Jakarta", "Indonesia"),
    ("Kathmandu", 27.7172, 85.3240, "Bagmati", "Nepal"),
    ("Colombo", 6.9271, 79.8612, "Western Province", "Sri Lanka"),
    ("Dhaka", 23.8103, 90.4125, "Dhaka", "Bangladesh"),
]


class GeocodingService:
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

    def _search_offline_cities(self, query: str, limit: int = 8) -> list[PlaceResult]:
        """Fast offline substring matching against curated cities database."""
        q = query.strip().lower()
        if not q or len(q) < 2:
            return []

        matches: list[PlaceResult] = []
        for name, lat, lon, state, country in _OFFLINE_CITIES:
            if q in name.lower() or q in state.lower() or q in f"{name} {state} {country}".lower():
                matches.append(PlaceResult(
                    display_name=f"{name}, {state}, {country}",
                    latitude=lat,
                    longitude=lon,
                    country=country,
                    state=state,
                ))
                if len(matches) >= limit:
                    break
        return matches

    async def search_places(self, query: str, limit: int = 8) -> list[PlaceResult]:
        """
        Multi-tier resilient place search:
        1. OpenStreetMap Nominatim
        2. Photon OSM API
        3. Built-in Offline Cities Database
        """
        results: list[PlaceResult] = []
        q = query.strip()
        if not q or len(q) < 2:
            return []

        # Tier 1: Try Primary Nominatim
        try:
            response = await self._client.get(
                self._provider_url,
                params={
                    "q": q,
                    "format": "jsonv2",
                    "limit": limit,
                    "addressdetails": 1,
                },
                headers={"User-Agent": self._user_agent},
                timeout=_SEARCH_TIMEOUT_SECONDS,
            )
            if response.status_code == 200:
                raw = response.json()
                for item in raw:
                    address = item.get("address", {})
                    results.append(PlaceResult(
                        display_name=item.get("display_name", ""),
                        latitude=float(item["lat"]),
                        longitude=float(item["lon"]),
                        country=address.get("country"),
                        state=address.get("state"),
                    ))
                if results:
                    return results[:limit]
        except Exception as exc:
            logger.warning("Primary geocoding (Nominatim) failed: %s", exc)

        # Tier 2: Try Photon OSM API
        try:
            photon_resp = await self._client.get(
                "https://photon.komoot.io/api/",
                params={"q": q, "limit": limit},
                headers={"User-Agent": self._user_agent},
                timeout=_SEARCH_TIMEOUT_SECONDS,
            )
            if photon_resp.status_code == 200:
                feats = photon_resp.json().get("features", [])
                for feat in feats:
                    props = feat.get("properties", {})
                    coords = feat.get("geometry", {}).get("coordinates", [0, 0])
                    name = props.get("name", "")
                    state = props.get("state")
                    country = props.get("country")
                    
                    parts = [p for p in [name, state, country] if p]
                    display_name = ", ".join(parts) if parts else name

                    results.append(PlaceResult(
                        display_name=display_name,
                        latitude=float(coords[1]),
                        longitude=float(coords[0]),
                        country=country,
                        state=state,
                    ))
                if results:
                    return results[:limit]
        except Exception as exc:
            logger.warning("Secondary geocoding (Photon) failed: %s", exc)

        # Tier 3: Offline Cities Database Fallback
        offline_matches = self._search_offline_cities(q, limit=limit)
        if offline_matches:
            return offline_matches

        return results

    async def detect_ip_location(self) -> PlaceResult:
        """Resolve client's approximate location via IP geolocation."""
        try:
            res = await self._client.get("http://ip-api.com/json/", timeout=4.0)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    city = data.get("city", "")
                    state = data.get("regionName", "")
                    country = data.get("country", "India")
                    lat = float(data.get("lat", 28.6139))
                    lon = float(data.get("lon", 77.2090))
                    
                    parts = [p for p in [city, state, country] if p]
                    display_name = ", ".join(parts) if parts else "Detected Location"
                    return PlaceResult(
                        display_name=display_name,
                        latitude=lat,
                        longitude=lon,
                        country=country,
                        state=state,
                    )
        except Exception as exc:
            logger.warning("IP geolocation lookup failed: %s", exc)

        return PlaceResult(
            display_name="New Delhi, Delhi, India",
            latitude=28.6139,
            longitude=77.2090,
            country="India",
            state="Delhi",
        )

    def _find_nearest_offline_city(self, lat: float, lon: float) -> Optional[PlaceResult]:
        """Find the closest offline city within reasonable regional radius."""
        best = None
        min_dist_sq = float("inf")
        for name, c_lat, c_lon, state, country in _OFFLINE_CITIES:
            dist_sq = (lat - c_lat) ** 2 + (lon - c_lon) ** 2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                best = (name, c_lat, c_lon, state, country)

        # Within ~1.5 degrees (~160 km)
        if best and min_dist_sq < 2.25:
            name, c_lat, c_lon, state, country = best
            return PlaceResult(
                display_name=f"{name}, {state}, {country}",
                latitude=lat,
                longitude=lon,
                country=country,
                state=state,
            )
        return None

    async def reverse_geocode(self, latitude: float, longitude: float) -> PlaceResult:
        """Reverse geocode coordinates into a human-readable place name and address."""
        reverse_url = self._provider_url.replace("/search", "/reverse")
        if not reverse_url.endswith("/reverse"):
            reverse_url = "https://nominatim.openstreetmap.org/reverse"

        try:
            response = await self._client.get(
                reverse_url,
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "format": "jsonv2",
                    "addressdetails": 1,
                },
                headers={"User-Agent": self._user_agent},
                timeout=_SEARCH_TIMEOUT_SECONDS,
            )
            if response.status_code == 200:
                data = response.json()
                display_name = data.get("display_name")
                address = data.get("address", {})
                if display_name:
                    return PlaceResult(
                        display_name=display_name,
                        latitude=latitude,
                        longitude=longitude,
                        country=address.get("country"),
                        state=address.get("state"),
                    )
        except Exception as exc:
            logger.warning("Reverse geocoding (Nominatim) failed: %s", exc)

        # Fallback: find nearest offline city
        nearest = self._find_nearest_offline_city(latitude, longitude)
        if nearest:
            return nearest

        return PlaceResult(
            display_name=f"Current Coordinates ({latitude:.4f}°, {longitude:.4f}°)",
            latitude=latitude,
            longitude=longitude,
        )

    def resolve_timezone(
        self, latitude: float, longitude: float, local_date: date
    ) -> TimezoneResolution:
        tz_name = self._tf.timezone_at(lat=latitude, lng=longitude)
        if tz_name is None:
            if 8.0 <= latitude <= 37.0 and 68.0 <= longitude <= 97.5:
                tz_name = "Asia/Kolkata"
            else:
                raise ValueError(
                    f"No timezone found for coordinates ({latitude}, {longitude})."
                )
        try:
            tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown IANA timezone {tz_name!r}.") from exc

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
