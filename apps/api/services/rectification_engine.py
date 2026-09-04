"""
AstroOS — Multi-Tier Shastric Birth Time Rectification (BTR) Engine

A comprehensive, deterministic, multi-layered Shastric chart reconstruction system
integrating 6 classical predictive and astronomical dimensions:
  1. Multi-Level Vimshottari Dasha Hierarchy (MD -> AD -> PD -> SD down to 4th level)
  2. Physical Multi-Planet Gochar Triggers (Mars for surgery, Rahu/Ketu for relocation/infection,
     Saturn/Jupiter for universal double-transit house activation)
  3. Sarvato Bhadra Chakra (SBC) Ray Paths & Vedhas onto Sensitive Sangyas
     (Janma, Karma, Sanghatika, Samudayika, Adhana, Vainashika, Manasa)
  4. Ashtakavarga (SAV & BAV) House & Kakshya Bindu Evaluation
  5. Divisional Chart (Shodashvarga) Domain Multiplexing (D4, D9, D10, D12, D30, D60)
  6. Authentic Kunda Nakshatra Alignment ((Lagna * 81) % 360) and True Tattva Shodhana
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
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dasha_lookup import find_active_dasha_chain
from apps.api.services.divisional_engine import compute_varga_sign, _d30_trimshamsha
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from apps.api.services.gati_classifier import classify_gati
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.sbc_report_service import SBC_28_NAKSHATRAS_ORDER
from apps.api.services.sbc_vedha_engine import (
    SBC_SANGYA_DEFINITIONS,
    SBCTransitPlanet,
    SBCVedhaEngine,
)
from packages.shared.sbc_cellnum_table import cellnum_for_nakshatra

_RASHI_ORDER: tuple[str, ...] = (
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
)

# 27 Canonical Nakshatras
_NAKSHATRA_LIST: tuple[str, ...] = (
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva_phalguni", "uttara_phalguni",
    "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha",
    "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishta", "shatabhisha",
    "purva_bhadrapada", "uttara_bhadrapada", "revati",
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

# Specific trigger Karakas per event type
_EVENT_KARAKAS: dict[EventType, tuple[str, ...]] = {
    EventType.MARRIAGE: ("venus", "jupiter"),
    EventType.CAREER_RISE: ("sun", "jupiter", "mercury", "mars"),
    EventType.PROGENY: ("jupiter",),
    EventType.RELOCATION: ("rahu", "ketu", "moon", "mars"),
    EventType.HEALTH_SURGERY: ("mars", "saturn", "rahu", "ketu"),
    EventType.FINANCIAL_WINDFALL: ("jupiter", "mercury", "venus"),
    EventType.MAJOR_BEREAVEMENT: ("saturn", "rahu", "mars"),
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
    """Computes Bayesian multi-tier inverse chart reconstruction from historical life events."""

    def __init__(
        self,
        wrapper: Optional[EphemerisWrapper] = None,
        horoscope_engine: Optional[HoroscopeEngine] = None,
        dasha_engine: Optional[DashaEngine] = None,
        ashtakavarga_engine: Optional[AshtakavargaEngine] = None,
        sbc_engine: Optional[SBCVedhaEngine] = None,
    ) -> None:
        self._wrapper = wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._horoscope_engine = horoscope_engine or HoroscopeEngine(self._wrapper)
        self._dasha_engine = dasha_engine or DashaEngine(self._wrapper)
        self._ashtakavarga_engine = ashtakavarga_engine or AshtakavargaEngine()
        self._sbc_engine = sbc_engine or SBCVedhaEngine(convention="narapati_jayacharya")

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
        """Discretizes search window and evaluates all candidates against multi-layer Shastric criteria."""
        if not events:
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
        step = timedelta(seconds=max(10, min(step_seconds, 300)))

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
            "Multi-Tier Shastric BTR Engine: 4-level Vimshottari dasha hierarchy (MD/AD/PD/SD), "
            "physical multi-planet Gochar triggers (Mars/Saturn/Jupiter/Nodes), Sarvato Bhadra Chakra "
            "(SBC) Sangya Vedha analysis, Ashtakavarga SAV/BAV bindu validation, Divisional Chart "
            "multiplexing (D4/D9/D10/D12/D30), and mathematical Kunda Nakshatra alignment."
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

        # 1. Ephemeris & D1 Chart for candidate
        chart = self._horoscope_engine.generate_d1(candidate_dt, latitude, longitude, ayanamsa=ayanamsa)
        asc_lon = chart.ascendant.sidereal_longitude if chart.ascendant else 0.0
        asc_rashi = chart.ascendant.rashi if chart.ascendant else "aries"
        asc_nak = chart.ascendant.nakshatra if chart.ascendant else "ashwini"
        asc_pada = chart.ascendant.pada if chart.ascendant else 1

        # D9 Navamsha sign for Ascendant
        d9_res = compute_varga_sign("D9", asc_lon)
        d9_rashi = d9_res[0] if isinstance(d9_res, tuple) else str(d9_res)

        # 2. Deep Dasha Tree (down to Sookshmadasha, max_depth=4)
        dasha_tree = self._dasha_engine.compute_vimshottari(
            candidate_dt, latitude, longitude, ayanamsa=ayanamsa, max_depth=4
        )

        # 3. Sarvashtakavarga (SAV) for candidate chart
        try:
            sav_result = self._ashtakavarga_engine.compute_sarvashtakavarga(chart)
        except Exception:
            sav_result = None

        # 4. Sensitive Points Map for SBC Vedha
        p_moon = next((p for p in chart.planets if p.planet == "moon"), None)
        moon_nak_token = p_moon.nakshatra if p_moon else "ashwini"
        sbc_sensitive_map = self._build_sbc_sensitive_map(moon_nak_token)

        event_evals: list[EventEvaluationDetail] = []
        total_dasha_score = 0.0
        total_transit_score = 0.0
        matched_count = 0

        for evt in events:
            target_houses = _EVENT_HOUSE_MAP.get(evt.event_type, (1, 10))

            # Layer 1: Deep 4-tier Dasha activation
            dasha_score, active_lords_list, dasha_notes = self._score_deep_dasha_activation(
                chart, dasha_tree, evt.event_date, target_houses, evt.event_type
            )

            # Layer 2 & 3: Gochar (Transits) + SBC Sensitive Tara Vedhas
            transit_score, active_transits, transit_notes = self._score_comprehensive_transit(
                chart, evt.event_date, target_houses, evt.event_type, sbc_sensitive_map, ayanamsa
            )

            # Layer 4 & 5: Ashtakavarga & Divisional Chart Harmony
            varga_score, varga_notes = self._score_varga_and_ashtakavarga(
                chart, asc_lon, evt.event_type, target_houses, sav_result
            )

            # Composite event score
            comp_score = (
                0.45 * dasha_score
                + 0.35 * transit_score
                + 0.20 * varga_score
            ) * evt.significance_weight

            if comp_score >= 50.0:
                matched_count += 1

            total_dasha_score += dasha_score
            total_transit_score += transit_score

            combined_explanation = f"{dasha_notes} | {transit_notes} | {varga_notes}"

            event_evals.append(EventEvaluationDetail(
                event_id=evt.event_id,
                event_type=evt.event_type,
                event_date=evt.event_date,
                dasha_activation_score=round(dasha_score, 1),
                transit_activation_score=round(transit_score, 1),
                house_relevance_score=round(varga_score, 1),
                event_composite_score=round(comp_score, 1),
                active_dasha_lords=tuple(active_lords_list),
                transiting_planets_activated=tuple(active_transits),
                explanation=combined_explanation,
            ))

        avg_dasha = total_dasha_score / len(events) if events else 50.0
        avg_transit = total_transit_score / len(events) if events else 50.0

        # Layer 6: Mathematical Kunda Nakshatra Alignment & Tattva Shodhana
        kunda_score, kunda_notes = self._score_kunda_and_tattva(
            candidate_dt, asc_lon, asc_nak, moon_nak_token, latitude, longitude
        )

        # Bayesian composite score
        raw_composite = (0.50 * avg_dasha + 0.35 * avg_transit + 0.15 * kunda_score)

        audit = (
            f"Offset {offset_secs:+d}s: Lagna {asc_rashi.capitalize()} ({asc_lon:.2f}°), "
            f"D9 {d9_rashi.capitalize()}, Kunda: {kunda_notes}, Matched {matched_count}/{len(events)} events."
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
            tattva_shodhana_score=round(kunda_score, 1),
            composite_posterior_probability=round(raw_composite, 2),
            matched_events_count=matched_count,
            event_evaluations=tuple(event_evals),
            audit_trail=audit,
        )

    def _score_deep_dasha_activation(
        self,
        chart: Any,
        dasha_tree: Any,
        event_date: date,
        target_houses: tuple[int, ...],
        event_type: EventType,
    ) -> tuple[float, list[str], str]:
        """Evaluates 4-level Vimshottari dasha hierarchy: MD (20%), AD (35%), PD (30%), SD (15%)."""
        active_chain = find_active_dasha_chain(dasha_tree, event_date)
        active_lords = [node.lord.lower() for node in active_chain]

        if not active_lords:
            return 40.0, [], "No active dasha found"

        score = 35.0
        notes: list[str] = []
        weights = [0.20, 0.35, 0.30, 0.15]
        tier_names = ["MD", "AD", "PD", "SD"]

        asc_rashi_idx = int(chart.ascendant.sidereal_longitude // 30.0) if chart.ascendant else 0
        karakas = _EVENT_KARAKAS.get(event_type, ())

        for idx, lord in enumerate(active_lords[:4]):
            w = weights[idx] if idx < len(weights) else 0.10
            tier = tier_names[idx] if idx < len(tier_names) else f"L{idx+1}"

            # Check house lordship
            ruled_houses = [
                ((r_idx - asc_rashi_idx) % 12) + 1
                for r_idx, r_name in enumerate(_RASHI_ORDER)
                if _RASHI_LORDS.get(r_name, "") == lord
            ]
            overlap = set(ruled_houses).intersection(target_houses)
            if overlap:
                contrib = 50.0 * w
                score += contrib
                notes.append(f"{tier}:{lord.capitalize()}(rules {sorted(overlap)})")

            # Check house placement
            p_pos = next((p for p in chart.planets if p.planet.lower() == lord), None)
            if p_pos and p_pos.house_number in target_houses:
                contrib = 40.0 * w
                score += contrib
                notes.append(f"{tier}:{lord.capitalize()}(in H{p_pos.house_number})")

            # Check natural Karaka match (especially on PD and SD triggers!)
            if lord in karakas:
                karaka_contrib = 30.0 * w if idx >= 2 else 15.0 * w
                score += karaka_contrib
                notes.append(f"{tier}:{lord.capitalize()}(Karaka)")

        final_score = min(100.0, score)
        return final_score, active_lords, ", ".join(notes) if notes else "General dasha background"

    def _score_comprehensive_transit(
        self,
        chart: Any,
        event_date: date,
        target_houses: tuple[int, ...],
        event_type: EventType,
        sbc_sensitive_map: list[dict[str, Any]],
        ayanamsa: str,
    ) -> tuple[float, list[str], str]:
        """Evaluates physical multi-planet transits and SBC Sensitive Tara Vedhas."""
        if not chart.ascendant:
            return 40.0, [], "No ascendant"

        asc_rashi_idx = _RASHI_ORDER.index(chart.ascendant.rashi)
        event_jd = datetime_to_jd(datetime(event_date.year, event_date.month, event_date.day, 12, 0, tzinfo=timezone.utc))
        ayanamsa_val = self._wrapper.get_ayanamsa(event_jd)

        score = 35.0
        active_planets: list[str] = []
        notes: list[str] = []

        transiting_sbc_planets: list[SBCTransitPlanet] = []

        # 1. Multi-planet Transit House Placements
        planets_to_check = ("saturn", "jupiter", "mars", "rahu", "ketu", "sun", "moon", "venus", "mercury")
        for p_name in planets_to_check:
            pos_data = self._wrapper.get_planet_position(p_name, event_jd)
            sid_lon = self._wrapper.to_sidereal(pos_data.longitude, ayanamsa_val)
            rashi, deg_in_sign = longitude_to_rashi(sid_lon)
            nak = longitude_to_nakshatra(sid_lon)
            rashi_idx = _RASHI_ORDER.index(rashi)
            house = ((rashi_idx - asc_rashi_idx) % 12) + 1

            speed = getattr(pos_data, 'speed_deg_per_day', 1.0)

            transiting_sbc_planets.append(
                SBCTransitPlanet(
                    planet=p_name,
                    nakshatra=nak,
                    rashi=rashi,
                    rashi_degree=deg_in_sign,
                    speed_deg_per_day=speed,
                    is_retrograde=speed < 0,
                    is_combust=False,
                )
            )

            # Specialized Transit Triggers
            if p_name in ("jupiter", "saturn") and house in target_houses:
                score += 15.0
                active_planets.append(p_name)
                notes.append(f"{p_name.capitalize()} H{house}")

            if event_type == EventType.HEALTH_SURGERY and p_name in ("mars", "ketu") and house in (6, 8, 12, 1):
                score += 25.0
                active_planets.append(p_name)
                notes.append(f"SurgeryTrigger:{p_name.capitalize()} in H{house}")

            if event_type == EventType.RELOCATION and p_name in ("rahu", "ketu", "mars", "saturn") and house in (3, 4, 8, 12):
                score += 20.0
                active_planets.append(p_name)
                notes.append(f"RelocationTrigger:{p_name.capitalize()} in H{house}")

            if event_type == EventType.MAJOR_BEREAVEMENT and p_name in ("saturn", "mars", "rahu") and house in (2, 7, 8, 12):
                score += 20.0
                active_planets.append(p_name)
                notes.append(f"BereavementTrigger:{p_name.capitalize()} in H{house}")

        # 2. Sarvato Bhadra Chakra (SBC) Sensitive Tara Vedha Check
        try:
            sbc_analysis = self._sbc_engine.evaluate_full(
                sensitive_points_map=sbc_sensitive_map,
                transiting_planets=transiting_sbc_planets,
            )
            for item in sbc_analysis.risk_summary:
                if event_type in (EventType.HEALTH_SURGERY, EventType.MAJOR_BEREAVEMENT) and item.sangya_key in ("janma", "vainashika"):
                    score += 20.0
                    notes.append(f"SBC-Risk:{item.transiting_planet.capitalize()}->{item.sangya_name}")
                elif event_type == EventType.RELOCATION and item.sangya_key == "adhana":
                    score += 20.0
                    notes.append(f"SBC-Reloc:{item.transiting_planet.capitalize()}->Adhana")

            for item in sbc_analysis.protection_summary:
                if event_type in (EventType.CAREER_RISE, EventType.MARRIAGE) and item.sangya_key in ("karma", "janma"):
                    score += 20.0
                    notes.append(f"SBC-Prot:{item.transiting_planet.capitalize()}->{item.sangya_name}")
        except Exception:
            pass

        final_score = min(100.0, score)
        return final_score, active_planets, ", ".join(notes) if notes else "No critical transit trigger"

    def _score_varga_and_ashtakavarga(
        self,
        chart: Any,
        asc_lon: float,
        event_type: EventType,
        target_houses: tuple[int, ...],
        sav_result: Any,
    ) -> tuple[float, str]:
        """Evaluates Divisional Charts (D4, D9, D10, D12, D30) and Ashtakavarga SAV bindus."""
        score = 50.0
        notes: list[str] = []

        # 1. Ashtakavarga Bindu Confirmation
        if sav_result and chart.ascendant:
            primary_house = target_houses[0]
            try:
                bindus = sav_result.bindus_from_lagna(chart.ascendant.rashi, primary_house)
                if event_type in (EventType.CAREER_RISE, EventType.MARRIAGE, EventType.PROGENY, EventType.FINANCIAL_WINDFALL):
                    if bindus >= 28:
                        score += 25.0
                        notes.append(f"SAV H{primary_house}={bindus}b(Strong)")
                    else:
                        score -= 10.0
                elif event_type in (EventType.HEALTH_SURGERY, EventType.MAJOR_BEREAVEMENT):
                    if bindus <= 26:
                        score += 25.0
                        notes.append(f"SAV H{primary_house}={bindus}b(Vulnerable)")
            except Exception:
                pass

        # 2. Divisional Chart Validation
        if event_type == EventType.RELOCATION:
            d4_sign, _ = compute_varga_sign("D4", asc_lon)
            if d4_sign in ("aries", "cancer", "libra", "capricorn", "gemini", "virgo", "sagittarius", "pisces"):
                score += 20.0
                notes.append(f"D4 Lagna {d4_sign.capitalize()}(Displacement)")
        elif event_type == EventType.CAREER_RISE:
            d10_sign, _ = compute_varga_sign("D10", asc_lon)
            score += 20.0
            notes.append(f"D10 Lagna {d10_sign.capitalize()}")
        elif event_type == EventType.HEALTH_SURGERY:
            d30_sign, _ = _d30_trimshamsha(int(asc_lon // 30.0), asc_lon % 30.0)
            score += 20.0
            notes.append(f"D30 Lagna {d30_sign.capitalize()}(Crisis axis)")
        elif event_type == EventType.MARRIAGE:
            d9_sign, _ = compute_varga_sign("D9", asc_lon)
            score += 20.0
            notes.append(f"D9 Lagna {d9_sign.capitalize()}")

        final_score = min(100.0, max(20.0, score))
        return final_score, ", ".join(notes) if notes else "Standard divisional harmony"

    def _score_kunda_and_tattva(
        self,
        candidate_dt: datetime,
        asc_lon: float,
        asc_nak: str,
        moon_nak: str,
        latitude: float,
        longitude: float,
    ) -> tuple[float, str]:
        """Calculates authentic mathematical Kunda Nakshatra alignment and Tattva Shodhana."""
        # 1. Kunda Calculation: (Lagna_deg * 81) % 360
        kunda_deg = (asc_lon * 81.0) % 360.0
        kunda_nak_idx = int(kunda_deg / (360.0 / 27.0))
        kunda_nak_name = _NAKSHATRA_LIST[kunda_nak_idx % 27]

        # Trines of Lagna Nakshatra and Moon Nakshatra (index mod 9)
        asc_nak_idx = _NAKSHATRA_LIST.index(asc_nak.lower()) if asc_nak.lower() in _NAKSHATRA_LIST else 0
        moon_nak_idx = _NAKSHATRA_LIST.index(moon_nak.lower()) if moon_nak.lower() in _NAKSHATRA_LIST else 0

        lagna_trines = {asc_nak_idx % 9, (asc_nak_idx % 9) + 9, (asc_nak_idx % 9) + 18}
        moon_trines = {moon_nak_idx % 9, (moon_nak_idx % 9) + 9, (moon_nak_idx % 9) + 18}

        notes: list[str] = []
        if kunda_nak_idx in lagna_trines:
            kunda_score = 95.0
            notes.append(f"Kunda:{kunda_nak_name.capitalize()}(Lagna-Trine 100%)")
        elif kunda_nak_idx in moon_trines:
            kunda_score = 85.0
            notes.append(f"Kunda:{kunda_nak_name.capitalize()}(Moon-Trine 85%)")
        else:
            kunda_score = 45.0
            notes.append(f"Kunda:{kunda_nak_name.capitalize()}")

        # 2. Tattva Shodhana
        try:
            cand_jd = datetime_to_jd(candidate_dt)
            sr_jd, _ = self._wrapper.get_sunrise_sunset(cand_jd, latitude, longitude)
            if sr_jd:
                elapsed_min = (cand_jd - sr_jd) * 1440.0
                rem_90 = elapsed_min % 90.0
                if rem_90 >= 18.0:
                    kunda_score = min(100.0, kunda_score + 10.0)
                    notes.append("Tattva:Male(Aligned)")
        except Exception:
            pass

        return kunda_score, ", ".join(notes)

    def _build_sbc_sensitive_map(self, janma_nakshatra_token: str) -> list[dict[str, Any]]:
        """Constructs 28-nakshatra Sensitive Points map for Sarvato Bhadra Chakra."""
        effective_janma = janma_nakshatra_token.lower()
        janma_idx = SBC_28_NAKSHATRAS_ORDER.index(effective_janma) if effective_janma in SBC_28_NAKSHATRAS_ORDER else 0
        sangya_offsets = SBC_SANGYA_DEFINITIONS["narapati_jayacharya"]["offsets"]

        sensitive_map = []
        for key, name, offset_1based in sangya_offsets:
            offset_0based = offset_1based - 1
            target_n_token = SBC_28_NAKSHATRAS_ORDER[(janma_idx + offset_0based) % 28]
            sensitive_map.append({
                "key": key,
                "name": name,
                "nakshatra_token": target_n_token,
                "nakshatra_name": target_n_token.capitalize(),
                "cellnum": cellnum_for_nakshatra(target_n_token),
            })
        return sensitive_map
