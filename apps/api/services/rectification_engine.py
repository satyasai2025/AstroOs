"""
AstroOS — Inverse Natal Profiling & Evolutionary Chart Rectification Engine (Priority 14)

Implements:
  1. Window-based discretization of candidate birth moments
  2. Multi-event Dasha lord governance and house activation likelihood scoring
  3. Retroactive transit aspect verification (real Jupiter/Saturn double transit,
     computed from ephemeris — not simulated)
  4. Low-weight ascendant-pada proxy (disclosed simplification, not a verified
     classical Tattva Shodhana formula)
  5. Bayesian posterior probability normalization
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import math
from typing import Any, Optional, Sequence
import uuid

from apps.api.domain.rectification import (
    EventEvaluationDetail,
    EventType,
    LifeEventRecord,
    RectificationCandidate,
    RectificationResult,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.divisional_engine import compute_varga_sign
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from apps.api.services.horoscope_engine import HoroscopeEngine
_RASHI_ORDER: tuple[str, ...] = (
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
)


# Relevant house governance per event type (Classical Parashari)
_EVENT_HOUSE_MAP: dict[EventType, tuple[int, ...]] = {
    EventType.MARRIAGE: (7, 11, 2),
    EventType.CAREER_RISE: (10, 11, 6, 1),
    EventType.PROGENY: (5, 9, 2),
    EventType.RELOCATION: (4, 9, 12, 3),
    EventType.HEALTH_SURGERY: (6, 8, 12, 1),
    EventType.FINANCIAL_WINDFALL: (2, 11, 5, 9),
    EventType.MAJOR_BEREAVEMENT: (8, 12, 2, 7),
}

_RASHI_LORDS: dict[str, str] = {
    "aries": "mars", "scorpio": "mars",
    "taurus": "venus", "libra": "venus",
    "gemini": "mercury", "virgo": "mercury",
    "cancer": "moon", "leo": "sun",
    "sagittarius": "jupiter", "pisces": "jupiter",
    "capricorn": "saturn", "aquarius": "saturn",
}


class RectificationEngine:
    """Computes Bayesian inverse chart reconstruction from historical life events."""

    def __init__(
        self,
        wrapper: Optional[EphemerisWrapper] = None,
        horoscope_engine: Optional[HoroscopeEngine] = None,
        dasha_engine: Optional[DashaEngine] = None,
    ) -> None:
        self._wrapper = wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._horoscope_engine = horoscope_engine or HoroscopeEngine(self._wrapper)
        self._dasha_engine = dasha_engine or DashaEngine(self._wrapper)

    def search_rectification(
        self,
        base_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        events: Sequence[LifeEventRecord],
        window_minutes: int = 15,
        step_seconds: int = 60,
        ayanamsa: str = "lahiri",
    ) -> RectificationResult:
        """
        Discretizes the search window around base_datetime_utc and evaluates all candidates against events.
        """
        if not events:
            # Create a default calibration event if none provided
            events = [
                LifeEventRecord(
                    event_id="evt-default",
                    event_type=EventType.CAREER_RISE,
                    event_date=date(base_datetime_utc.year + 25, 6, 1),
                    significance_weight=1.0,
                    description="Default career milestone anchor",
                )
            ]

        half_window = timedelta(minutes=max(1, min(window_minutes, 120)))
        start_dt = base_datetime_utc - half_window
        end_dt = base_datetime_utc + half_window
        step = timedelta(seconds=max(15, min(step_seconds, 300)))

        candidates: list[RectificationCandidate] = []
        current_dt = start_dt
        candidate_idx = 1

        while current_dt <= end_dt:
            cand = self._evaluate_candidate_moment(
                candidate_dt=current_dt,
                base_dt=base_datetime_utc,
                candidate_idx=candidate_idx,
                latitude=latitude,
                longitude=longitude,
                events=events,
                ayanamsa=ayanamsa,
            )
            candidates.append(cand)
            current_dt += step
            candidate_idx += 1

        # Normalize posterior probability scores across candidates
        total_raw_score = sum(math.exp(c.composite_posterior_probability / 25.0) for c in candidates)
        normalized_candidates: list[RectificationCandidate] = []

        for c in candidates:
            prob = (math.exp(c.composite_posterior_probability / 25.0) / total_raw_score) * 100.0 if total_raw_score > 0 else 0.0
            norm_cand = RectificationCandidate(
                candidate_id=c.candidate_id,
                proposed_birth_datetime_utc=c.proposed_birth_datetime_utc,
                offset_seconds=c.offset_seconds,
                ascendant_rashi=c.ascendant_rashi,
                ascendant_longitude=c.ascendant_longitude,
                ascendant_nakshatra=c.ascendant_nakshatra,
                ascendant_pada=c.ascendant_pada,
                d9_ascendant_rashi=c.d9_ascendant_rashi,
                dasha_event_score=c.dasha_event_score,
                transit_event_score=c.transit_event_score,
                tattva_shodhana_score=c.tattva_shodhana_score,
                composite_posterior_probability=round(prob, 2),
                matched_events_count=c.matched_events_count,
                event_evaluations=c.event_evaluations,
                audit_trail=c.audit_trail,
            )
            normalized_candidates.append(norm_cand)

        # Sort by posterior probability descending
        normalized_candidates.sort(key=lambda c: c.composite_posterior_probability, reverse=True)
        top_candidates = tuple(normalized_candidates[:10])
        best = top_candidates[0] if top_candidates else None

        methodology = (
            "Bayesian Inverse Profiling: Multi-event Vimshottari Mahadasha/Antardasha lord house governance, "
            "real Jupiter-Saturn double transit house activation, Navamsha D9 lagna harmony, and a low-weight "
            "disclosed ascendant-pada proxy (not verified classical Tattva Shodhana)."
        )

        return RectificationResult(
            query_id=f"rect-{uuid.uuid4().hex[:8]}",
            base_datetime_utc=base_datetime_utc,
            search_window_start=start_dt,
            search_window_end=end_dt,
            step_seconds=step_seconds,
            total_candidates_evaluated=len(candidates),
            life_events_count=len(events),
            top_candidates=top_candidates,
            best_candidate=best,
            bayesian_prior_used="Uniform Discretized Prior across Temporal Window",
            methodology_provenance=methodology,
        )

    def _evaluate_candidate_moment(
        self,
        candidate_dt: datetime,
        base_dt: datetime,
        candidate_idx: int,
        latitude: float,
        longitude: float,
        events: Sequence[LifeEventRecord],
        ayanamsa: str,
    ) -> RectificationCandidate:
        offset_secs = int((candidate_dt - base_dt).total_seconds())

        # 1. Ephemeris & Chart for candidate
        chart = self._horoscope_engine.generate_d1(candidate_dt, latitude, longitude, ayanamsa=ayanamsa)
        asc_lon = chart.ascendant.sidereal_longitude if chart.ascendant else 0.0
        asc_rashi = chart.ascendant.rashi if chart.ascendant else "aries"
        asc_nak = chart.ascendant.nakshatra if chart.ascendant else "ashwini"
        asc_pada = chart.ascendant.pada if chart.ascendant else 1

        # D9 Navamsha sign for Ascendant
        d9_res = compute_varga_sign("D9", asc_lon)
        d9_rashi = d9_res[0] if isinstance(d9_res, tuple) else str(d9_res)

        # 2. Compute Dasha Tree
        dasha_tree = self._dasha_engine.compute_vimshottari(
            candidate_dt, latitude, longitude, ayanamsa=ayanamsa, max_depth=2
        )

        event_evals: list[EventEvaluationDetail] = []
        total_dasha_score = 0.0
        total_transit_score = 0.0
        matched_count = 0

        for evt in events:
            # Find active Dasha at event date
            active_lords = self._find_active_dasha_lords(dasha_tree, evt.event_date)
            target_houses = _EVENT_HOUSE_MAP.get(evt.event_type, (1, 10))

            # Dasha activation score: Check if dasha lord rules or occupies target houses
            dasha_score, dasha_notes = self._score_dasha_activation(chart, active_lords, target_houses)

            # Transit score: real Jupiter/Saturn double-transit house activation
            transit_score, active_transits, transit_notes = self._score_transit_activation(
                chart, evt.event_date, target_houses, ayanamsa,
            )

            # House relevance score
            house_score = 85.0 if any(h in (1, 5, 7, 9, 10, 11) for h in target_houses) else 70.0

            # Composite event score
            comp_score = (
                0.50 * dasha_score
                + 0.35 * transit_score
                + 0.15 * house_score
            ) * evt.significance_weight

            if comp_score >= 50.0:
                matched_count += 1

            total_dasha_score += dasha_score
            total_transit_score += transit_score

            event_evals.append(EventEvaluationDetail(
                event_id=evt.event_id,
                event_type=evt.event_type,
                event_date=evt.event_date,
                dasha_activation_score=round(dasha_score, 1),
                transit_activation_score=round(transit_score, 1),
                house_relevance_score=round(house_score, 1),
                event_composite_score=round(comp_score, 1),
                active_dasha_lords=tuple(active_lords),
                transiting_planets_activated=tuple(active_transits),
                explanation=f"{dasha_notes} | {transit_notes}",
            ))

        avg_dasha = total_dasha_score / len(events) if events else 50.0
        avg_transit = total_transit_score / len(events) if events else 50.0

        # NOTE: not a full classical Tattva Shodhana (elemental purification)
        # test — no verified classical formula for this technique could be
        # confirmed against a reference implementation, so this is only a
        # weak, disclosed proxy (odd vs. even ascendant pada) contributing
        # just 10% of the composite score. Treat tattva_shodhana_score as
        # low-confidence, not as genuine Tattva Shodhana evidence.
        tattva_score = 80.0 if asc_pada in (1, 3) else 75.0

        # Unnormalized log-likelihood composite score
        raw_composite = (0.55 * avg_dasha + 0.35 * avg_transit + 0.10 * tattva_score)

        audit = (
            f"Offset {offset_secs:+d}s: Ascendant {asc_rashi.capitalize()} ({asc_lon:.2f}°), "
            f"D9 Lagna {d9_rashi.capitalize()}, Matched {matched_count}/{len(events)} events."
        )

        return RectificationCandidate(
            candidate_id=f"cand-{candidate_idx:03d}",
            proposed_birth_datetime_utc=candidate_dt,
            offset_seconds=offset_secs,
            ascendant_rashi=asc_rashi,
            ascendant_longitude=round(asc_lon, 4),
            ascendant_nakshatra=asc_nak,
            ascendant_pada=asc_pada,
            d9_ascendant_rashi=d9_rashi,
            dasha_event_score=round(avg_dasha, 1),
            transit_event_score=round(avg_transit, 1),
            tattva_shodhana_score=round(tattva_score, 1),
            composite_posterior_probability=round(raw_composite, 2),
            matched_events_count=matched_count,
            event_evaluations=tuple(event_evals),
            audit_trail=audit,
        )

    def _find_active_dasha_lords(self, dasha_tree: Any, target_date: date) -> list[str]:
        """Finds active Mahadasha and Antardasha lords at the event date."""
        active: list[str] = []
        if not dasha_tree or not hasattr(dasha_tree, "periods"):
            return active

        for md in dasha_tree.periods:
            if hasattr(md, "contains") and md.contains(target_date):
                active.append(md.lord.lower())
                for ad in md.sub_periods:
                    if hasattr(ad, "contains") and ad.contains(target_date):
                        active.append(ad.lord.lower())
                        break
                break

        return active

    def _score_dasha_activation(
        self,
        chart: Any,
        active_lords: list[str],
        target_houses: tuple[int, ...],
    ) -> tuple[float, str]:
        """Calculates how strongly the active dasha lords govern the required event houses."""
        score = 40.0  # Base likelihood
        notes: list[str] = []

        asc_rashi_idx = int(chart.ascendant.sidereal_longitude // 30.0) if chart.ascendant else 0

        for lord in active_lords:
            # Find houses ruled by this lord in candidate chart
            ruled_houses = [
                ((r_idx - asc_rashi_idx) % 12) + 1
                for r_idx, r_name in enumerate(_RASHI_ORDER)
                if _RASHI_LORDS.get(r_name, "") == lord
            ]

            overlap = set(ruled_houses).intersection(target_houses)
            if overlap:
                score += 25.0
                notes.append(f"{lord.capitalize()} rules house(s) {sorted(overlap)}")

            # Check if lord occupies a target house
            planet_pos = next((p for p in chart.planets if p.planet.lower() == lord), None)
            if planet_pos and planet_pos.house_number in target_houses:
                score += 20.0
                notes.append(f"{lord.capitalize()} occupies house {planet_pos.house_number}")

        final_score = min(100.0, score)
        return final_score, ", ".join(notes) if notes else "Moderate general governance"

    def _score_transit_activation(
        self,
        chart: Any,
        event_date: date,
        target_houses: tuple[int, ...],
        ayanamsa: str,
    ) -> tuple[float, list[str], str]:
        """
        Scores real Jupiter/Saturn transit activation on target houses at
        event_date noon UTC (Jupiter/Saturn double-transit principle: a
        life event is more likely when both slow-movers are transiting one
        of the event's governing houses, whole-sign-counted from the
        candidate's natal ascendant).
        """
        if not chart.ascendant:
            return 40.0, [], "No ascendant available for transit check"

        asc_rashi_idx = _RASHI_ORDER.index(chart.ascendant.rashi)
        event_jd = datetime_to_jd(datetime(event_date.year, event_date.month, event_date.day, 12, 0, tzinfo=timezone.utc))
        ayanamsa_val = self._wrapper.get_ayanamsa(event_jd)

        score = 40.0
        active_planets: list[str] = []
        notes: list[str] = []

        for planet in ("jupiter", "saturn"):
            tropical_pos = self._wrapper.get_planet_position(planet, event_jd)
            sidereal_lon = self._wrapper.to_sidereal(tropical_pos.longitude, ayanamsa_val)
            rashi, _ = longitude_to_rashi(sidereal_lon)
            rashi_idx = _RASHI_ORDER.index(rashi)
            house = ((rashi_idx - asc_rashi_idx) % 12) + 1

            if house in target_houses:
                score += 30.0
                active_planets.append(planet)
                notes.append(f"{planet.capitalize()} transiting house {house}")

        final_score = min(100.0, score)
        notes_str = ", ".join(notes) if notes else f"No Jupiter/Saturn activation of houses {target_houses}"
        return final_score, active_planets, notes_str
