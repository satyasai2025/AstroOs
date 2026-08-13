"""
AstroOS — Transit Timeline Engine (Module 11 Extension)

Calculates temporal keyframes for animated transit visualization.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from apps.api.domain.transit import TransitPlanetResult
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from apps.api.services.transit_engine import TransitEngine
from packages.shared.degrees import normalize_degrees
from packages.shared.enums import Rashi

logger = logging.getLogger(__name__)

_RASHI_LIST = [r.value for r in Rashi]
_ALL_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]


def _longitude_to_navamsha(longitude: float) -> str:
    """Calculate D9 Navamsha rashi from sidereal longitude."""
    normalized = normalize_degrees(longitude)
    sign_index = int(normalized // 30)
    degree_in_sign = normalized % 30
    navamsha_size = 30.0 / 9.0
    navamsha_index = int(degree_in_sign // navamsha_size)
    
    if sign_index % 2 == 0:
        navamsha_sign = (sign_index + navamsha_index) % 12
    else:
        navamsha_sign = (sign_index + 8 + navamsha_index) % 12
    
    return _RASHI_LIST[navamsha_sign]


class TransitTimelineEngine:
    def __init__(self, wrapper: EphemerisWrapper, transit_engine: TransitEngine) -> None:
        self._wrapper = wrapper
        self._transit_engine = transit_engine

    def compute_timeline(self, natal_chart, start_datetime_utc: datetime, end_datetime_utc: datetime,
                         latitude: float, longitude: float,
                         interval_minutes: int = 60, adaptive: bool = True,
                         include_panchanga: bool = True, include_navamsha: bool = True,
                         include_combustion: bool = True, include_dignity: bool = True,
                         planets: Optional[list[str]] = None) -> dict:
        planets_to_track = planets or _ALL_PLANETS
        base_interval = timedelta(minutes=interval_minutes)
        candidate_times = self._generate_keyframe_times(start_datetime_utc, end_datetime_utc, base_interval, adaptive)
        
        keyframes = []
        actual_intervals = []
        previous_state = None

        for i, dt in enumerate(candidate_times):
            transit_results = self._transit_engine.compute_transit(natal_chart=natal_chart, transit_datetime_utc=dt)
            kf_planets = []
            
            for result in transit_results:
                if result.planet not in planets_to_track:
                    continue
                
                is_combust = getattr(result, 'is_combust', False)
                combustion_orb = getattr(result, 'combustion_orb', None)
                
                planet_data = {
                    "planet": result.planet,
                    "sidereal_longitude": self._get_sidereal_longitude(result.planet, dt),
                    "rashi": result.transit_rashi,
                    "rashi_degree": result.transit_rashi_degree,
                    "rashi_minute": int((result.transit_rashi_degree % 1) * 60),
                    "rashi_second": int(((result.transit_rashi_degree % 1) * 60 % 1) * 60),
                    "is_direct": not result.is_retrograde,
                    "is_station": self._is_station(result),
                    "speed_deg_per_day": result.speed_deg_per_day,
                    "nakshatra": result.transit_nakshatra,
                    "pada": result.transit_pada,
                    "degree_in_nakshatra": self._get_degree_in_nakshatra(result.planet, dt),
                    "navamsha_rashi": _longitude_to_navamsha(self._get_sidereal_longitude(result.planet, dt)) if include_navamsha else "",
                    "navamsha_lord": "",
                    "is_combust": is_combust if include_combustion else False,
                    "combustion_orb": combustion_orb if include_combustion else None,
                    "dignity": getattr(result, 'dignity', None) if include_dignity else None,
                    "house_from_natal_moon": result.house_from_natal_moon,
                    "house_from_natal_ascendant": result.house_from_natal_moon,
                    "aspects": [],
                }
                kf_planets.append(planet_data)

            panchanga = self._get_panchanga(dt, latitude, longitude) if include_panchanga else None
            
            keyframe = {"datetime_utc": dt.isoformat(), "planets": kf_planets, "panchanga": panchanga}
            keyframes.append(keyframe)
            
            if i > 0:
                actual_intervals.append(int((dt - candidate_times[i - 1]).total_seconds() / 60))
            
            if previous_state and adaptive:
                events = self._detect_events(previous_state, kf_planets, candidate_times[i - 1], dt)
                if events:
                    keyframe["events"] = events
            
            previous_state = {p["planet"]: p for p in kf_planets}

        all_events = []
        for kf in keyframes:
            if "events" in kf:
                all_events.extend(kf["events"])
        
        if adaptive:
            boundary_events = self._detect_boundary_events_precise(natal_chart, keyframes, start_datetime_utc, end_datetime_utc, planets_to_track, include_combustion, include_dignity)
            all_events.extend(boundary_events)

        return {
            "keyframes": keyframes,
            "events": sorted(all_events, key=lambda e: e["datetime_utc"]),
            "computed_range": {
                "start": start_datetime_utc.isoformat(),
                "end": end_datetime_utc.isoformat(),
                "keyframe_count": len(keyframes),
                "event_count": len(all_events),
            },
            "actual_intervals": actual_intervals,
        }

    def _generate_keyframe_times(self, start: datetime, end: datetime, base_interval: timedelta, adaptive: bool) -> list[datetime]:
        times = []
        current = start
        while current <= end:
            times.append(current)
            current += base_interval
        
        if adaptive:
            extra_times = []
            for planet in _ALL_PLANETS:
                try:
                    extra_times.extend(self._estimate_sign_boundaries(planet, start, end))
                except Exception:
                    pass
            times.extend(extra_times)
            times = sorted(set(times))
        
        return times

    def _estimate_sign_boundaries(self, planet: str, start: datetime, end: datetime) -> list[datetime]:
        boundaries = []
        check_interval = timedelta(hours=6)
        current = start
        prev_rashi = None
        
        while current <= end:
            try:
                jd = datetime_to_jd(current)
                tropical = self._wrapper.get_planet_position(planet, jd)
                ayanamsa = self._wrapper.get_ayanamsa(jd)
                sidereal = self._wrapper.to_sidereal(tropical.longitude, ayanamsa)
                rashi, _ = longitude_to_rashi(sidereal)
                
                if prev_rashi is not None and prev_rashi != rashi:
                    boundaries.append(current)
                prev_rashi = rashi
                current += check_interval
            except Exception:
                current += check_interval
        
        return boundaries

    def _detect_events(self, previous_state: dict, current_planets: list[dict], previous_time: datetime, current_time: datetime) -> list[dict]:
        events = []
        for planet_data in current_planets:
            planet = planet_data["planet"]
            prev = previous_state.get(planet)
            if not prev:
                continue
            
            if prev["rashi"] != planet_data["rashi"]:
                events.append({"datetime_utc": current_time.isoformat(), "planet": planet, "event_type": "sign_ingress", "description": f"{planet.capitalize()} enters {planet_data['rashi']}", "from_value": prev["rashi"], "to_value": planet_data["rashi"]})
            
            if prev["nakshatra"] != planet_data["nakshatra"]:
                events.append({"datetime_utc": current_time.isoformat(), "planet": planet, "event_type": "nakshatra_change", "description": f"{planet.capitalize()} enters {planet_data['nakshatra']}", "from_value": prev["nakshatra"], "to_value": planet_data["nakshatra"]})
            
            if prev["pada"] != planet_data["pada"]:
                events.append({"datetime_utc": current_time.isoformat(), "planet": planet, "event_type": "pada_change", "description": f"{planet.capitalize()} enters Pada {planet_data['pada']}", "from_value": str(prev["pada"]), "to_value": str(planet_data["pada"])})
            
            if prev["is_direct"] != planet_data["is_direct"] and planet_data["is_station"]:
                event_type = "station_retrograde" if not planet_data["is_direct"] else "station_direct"
                events.append({"datetime_utc": current_time.isoformat(), "planet": planet, "event_type": event_type, "description": f"{planet.capitalize()} stations {event_type.replace('station_', '')}", "from_value": "direct" if planet_data["is_direct"] else "retrograde", "to_value": "retrograde" if planet_data["is_direct"] else "direct"})
            
            if prev["is_combust"] != planet_data["is_combust"]:
                event_type = "combustion_start" if planet_data["is_combust"] else "combustion_end"
                events.append({"datetime_utc": current_time.isoformat(), "planet": planet, "event_type": event_type, "description": f"{planet.capitalize()} {'becomes' if planet_data['is_combust'] else 'is relieved from'} combustion", "from_value": str(prev["is_combust"]), "to_value": str(planet_data["is_combust"])})
        
        return events

    def _detect_boundary_events_precise(self, natal_chart, keyframes: list[dict], start: datetime, end: datetime, planets: list[str], include_combustion: bool, include_dignity: bool) -> list[dict]:
        events = []
        for planet in planets:
            try:
                events.extend(self._find_sign_ingress_precise(planet, start, end))
                events.extend(self._find_station_precise(planet, start, end))
                if include_combustion:
                    events.extend(self._find_combustion_precise(planet, start, end))
            except Exception as e:
                logger.debug(f"Could not compute precise events for {planet}: {e}")
        return events

    def _find_sign_ingress_precise(self, planet: str, start: datetime, end: datetime) -> list[dict]:
        events = []
        try:
            start_rashi = self._get_rashi_at_time(planet, start)
            end_rashi = self._get_rashi_at_time(planet, end)
            if start_rashi != end_rashi:
                exact_time = self._binary_search_event(planet, start, end, lambda dt: self._get_rashi_at_time(planet, dt) != start_rashi)
                if exact_time:
                    new_rashi = self._get_rashi_at_time(planet, exact_time)
                    events.append({"datetime_utc": exact_time.isoformat(), "planet": planet, "event_type": "sign_ingress", "description": f"{planet.capitalize()} enters {new_rashi}", "from_value": start_rashi, "to_value": new_rashi})
        except Exception as e:
            logger.debug(f"Sign ingress detection failed for {planet}: {e}")
        return events

    def _find_station_precise(self, planet: str, start: datetime, end: datetime) -> list[dict]:
        events = []
        try:
            start_speed = self._get_speed_at_time(planet, start)
            end_speed = self._get_speed_at_time(planet, end)
            if (start_speed > 0 and end_speed < 0) or (start_speed < 0 and end_speed > 0):
                station_time = self._binary_search_event(planet, start, end, lambda dt: abs(self._get_speed_at_time(planet, dt)) < 0.5)
                if station_time:
                    event_type = "station_retrograde" if end_speed < 0 else "station_direct"
                    events.append({"datetime_utc": station_time.isoformat(), "planet": planet, "event_type": event_type, "description": f"{planet.capitalize()} stations {event_type.replace('station_', '')}", "from_value": "direct" if start_speed > 0 else "retrograde", "to_value": "retrograde" if end_speed < 0 else "direct"})
        except Exception as e:
            logger.debug(f"Station detection failed for {planet}: {e}")
        return events

    def _find_combustion_precise(self, planet: str, start: datetime, end: datetime) -> list[dict]:
        events = []
        try:
            start_combust = self._is_combust_at_time(planet, start)
            end_combust = self._is_combust_at_time(planet, end)
            if start_combust != end_combust:
                event_time = self._binary_search_event(planet, start, end, lambda dt: self._is_combust_at_time(planet, dt) != start_combust)
                if event_time:
                    event_type = "combustion_start" if end_combust else "combustion_end"
                    events.append({"datetime_utc": event_time.isoformat(), "planet": planet, "event_type": event_type, "description": f"{planet.capitalize()} {'becomes' if end_combust else 'is relieved from'} combustion", "from_value": str(start_combust), "to_value": str(end_combust)})
        except Exception as e:
            logger.debug(f"Combustion detection failed for {planet}: {e}")
        return events

    def _binary_search_event(self, planet: str, start: datetime, end: datetime, condition_fn, max_iterations: int = 20) -> Optional[datetime]:
        low = start
        high = end
        for _ in range(max_iterations):
            if (high - low).total_seconds() < 60:
                break
            mid = low + (high - low) / 2
            if condition_fn(mid):
                high = mid
            else:
                low = mid
        return high

    def _get_rashi_at_time(self, planet: str, dt: datetime) -> str:
        jd = datetime_to_jd(dt)
        tropical = self._wrapper.get_planet_position(planet, jd)
        ayanamsa = self._wrapper.get_ayanamsa(jd)
        sidereal = self._wrapper.to_sidereal(tropical.longitude, ayanamsa)
        rashi, _ = longitude_to_rashi(sidereal)
        return rashi

    def _get_speed_at_time(self, planet: str, dt: datetime) -> float:
        jd = datetime_to_jd(dt)
        tropical = self._wrapper.get_planet_position(planet, jd)
        return tropical.speed_deg_per_day

    def _is_combust_at_time(self, planet: str, dt: datetime) -> bool:
        try:
            jd = datetime_to_jd(dt)
            tropical = self._wrapper.get_planet_position(planet, jd)
            sun_tropical = self._wrapper.get_planet_position("sun", jd)
            angular_separation = abs(tropical.longitude - sun_tropical.longitude)
            combustion_orbs = {"mercury": 12.0, "venus": 10.0, "mars": 17.0, "jupiter": 11.0, "saturn": 15.0}
            orb = combustion_orbs.get(planet, 10.0)
            return angular_separation < orb
        except Exception:
            return False

    def _get_sidereal_longitude(self, planet: str, dt: datetime) -> float:
        jd = datetime_to_jd(dt)
        tropical = self._wrapper.get_planet_position(planet, jd)
        ayanamsa = self._wrapper.get_ayanamsa(jd)
        return self._wrapper.to_sidereal(tropical.longitude, ayanamsa)

    def _get_degree_in_nakshatra(self, planet: str, dt: datetime) -> float:
        lon = self._get_sidereal_longitude(planet, dt)
        nak_info = longitude_to_nakshatra(lon)
        return nak_info.degree_in_nakshatra

    def _is_station(self, result: TransitPlanetResult) -> bool:
        return abs(result.speed_deg_per_day) < 0.1

    def _get_panchanga(self, dt: datetime, latitude: float, longitude: float) -> dict:
        try:
            result = self._wrapper.calculate(dt, latitude, longitude, ayanamsa="lahiri", house_system="W")
            if result and result.panchanga:
                p = result.panchanga
                # Sunrise/sunset aren't exposed as datetimes on EphemerisResult
                # (only sunrise_jd/sunset_jd, used internally by Kala Bala) —
                # left blank rather than guessing a conversion.
                sunrise = ""
                sunset = ""

                return {
                    "tithi": {"number": p.tithi.number, "name": p.tithi.name, "paksha": p.tithi.paksha, "completion_percent": p.tithi.completion_percent},
                    "nakshatra": {"nakshatra": p.nakshatra.nakshatra, "nakshatra_number": p.nakshatra.nakshatra_number, "pada": p.nakshatra.pada, "lord": p.nakshatra.lord, "degree_in_nakshatra": p.nakshatra.degree_in_nakshatra, "degree_in_pada": p.nakshatra.degree_in_pada},
                    "yoga": {"number": p.yoga.number, "name": p.yoga.name, "completion_percent": p.yoga.completion_percent},
                    "karana": {"number": p.karana.number, "name": p.karana.name, "is_fixed": p.karana.is_fixed},
                    "vara": {"number": p.vara.number, "name": p.vara.name, "lord": p.vara.lord},
                    "sunrise": sunrise,
                    "sunset": sunset,
                    "rahu_kalam": {"start": "", "end": ""},
                    "gulika": {"start": "", "end": ""},
                    "yamaganda": {"start": "", "end": ""},
                    "hora": [],
                }
            return {}
        except Exception as e:
            logger.warning(f"Failed to get Panchanga for {dt}: {e}")
            return {}

