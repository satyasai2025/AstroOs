"""
AstroOS — Unified Multi-System Event Timing Engine

Authoritative orchestration layer integrating:
  1. Vimshottari Dasha (DashaEngine, dasha_lookup)
  2. Gochara Transits (TransitEngine, VedhaCalculator, AshtakavargaEngine)
  3. Sarvatobhadra Chakra (SBCVedhaEngine, SBCReportService)
  4. KP Cuspal/Sub-Lord Triggers (KPEngine, CSL and Sub-Lord algorithms)

Does NOT duplicate astronomy or calculation logic. Reuses the existing AstroOS
core engines and produces a transparently synchronized timing matrix.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from apps.api.domain.dasha import DashaTree
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.transit import TransitPlanetResult
from apps.api.domain.unified_event_timing import (
    ConfluenceTier,
    DashaTimingEvidence,
    EventCategory,
    GocharaTransitEvidence,
    KPTimingEvidence,
    SBCVedhaEvidence,
    TimelineSamplePoint,
    UnifiedEventTimingScanResult,
    UnifiedEventTimingWindow,
    UnifiedTimingSnapshot,
    WindowConfluenceStatus,
)
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dasha_lookup import find_active_dasha_chain
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.kp_engine import (
    EVENT_PRIMARY_CUSP,
    KP_EVENT_HOUSE_GROUPS,
    KPEngine,
    build_kp_cusps,
    compute_all_house_significators,
    compute_event_evidence,
    compute_event_promise,
    compute_fruitful_significators,
    compute_ruling_planets,
    compute_timing_analysis,
)
from apps.api.services.sbc_report_service import SBCReportService
from apps.api.services.sbc_vedha_engine import SBCVedhaEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.vedha_calculator import VedhaCalculator
from packages.shared.enums import Rashi
from packages.shared.rashi_offset import house_offset

logger = logging.getLogger(__name__)

_RASHI_LIST = [r.value for r in Rashi]


def _house_from_reference(reference_rashi: str, target_rashi: str) -> int:
    try:
        ref_idx = _RASHI_LIST.index(reference_rashi.lower())
        tgt_idx = _RASHI_LIST.index(target_rashi.lower())
        return house_offset(ref_idx, tgt_idx)
    except (ValueError, AttributeError):
        return 1

# ── Event Definitions & Classical Configurations ─────────────────────────────

EVENT_PROFILES: dict[str, dict[str, Any]] = {
    "marriage": {
        "label": "Marriage & Partnership",
        "primary_cusp": 7,
        "required_houses": [2, 7, 11],
        "secondary_houses": [1, 5, 9],
        "karakas": ["venus", "jupiter"],
        "gochara_favorable_houses": [2, 7, 11, 1, 5, 9],
        "sbc_sangyas": ["janma", "sanghatika", "samudayika"],
    },
    "career": {
        "label": "Career & Promotion",
        "primary_cusp": 10,
        "required_houses": [2, 6, 10, 11],
        "secondary_houses": [1, 9],
        "karakas": ["sun", "saturn", "mercury", "jupiter"],
        "gochara_favorable_houses": [3, 6, 10, 11],
        "sbc_sangyas": ["karma", "abhisheka", "adhana"],
    },
    "wealth": {
        "label": "Wealth & Asset Growth",
        "primary_cusp": 2,
        "required_houses": [2, 5, 9, 11],
        "secondary_houses": [1, 4],
        "karakas": ["jupiter", "mercury", "venus"],
        "gochara_favorable_houses": [2, 5, 9, 11],
        "sbc_sangyas": ["samudayika", "karma", "abhisheka"],
    },
    "property": {
        "label": "Property & Real Estate",
        "primary_cusp": 4,
        "required_houses": [4, 11, 12],
        "secondary_houses": [2, 9],
        "karakas": ["mars", "venus", "saturn"],
        "gochara_favorable_houses": [4, 11, 9],
        "sbc_sangyas": ["desha", "adhana"],
    },
    "foreign_travel": {
        "label": "Foreign Travel & Relocation",
        "primary_cusp": 12,
        "required_houses": [3, 9, 12],
        "secondary_houses": [7, 11],
        "karakas": ["rahu", "moon"],
        "gochara_favorable_houses": [9, 12, 3, 7],
        "sbc_sangyas": ["desha"],
    },
    "health": {
        "label": "Health & Vitality",
        "primary_cusp": 1,
        "required_houses": [1, 5, 9],
        "negating_houses": [6, 8, 12],
        "karakas": ["sun", "mars", "saturn"],
        "gochara_favorable_houses": [1, 3, 5, 9, 11],
        "sbc_sangyas": ["janma", "jati", "vainashika"],
    },
    "childbirth": {
        "label": "Childbirth & Progeny",
        "primary_cusp": 5,
        "required_houses": [2, 5, 11],
        "secondary_houses": [1, 9],
        "karakas": ["jupiter", "moon", "venus"],
        "gochara_favorable_houses": [2, 5, 9, 11],
        "sbc_sangyas": ["janma", "samudayika"],
    },
    "education": {
        "label": "Education & Higher Learning",
        "primary_cusp": 5,
        "required_houses": [4, 5, 9, 11],
        "secondary_houses": [1],
        "karakas": ["mercury", "jupiter"],
        "gochara_favorable_houses": [4, 5, 9, 11],
        "sbc_sangyas": ["karma", "janma", "abhisheka"],
    },
}

_RASHI_LORDS: dict[str, str] = {
    "aries": "mars", "taurus": "venus", "gemini": "mercury", "cancer": "moon",
    "leo": "sun", "virgo": "mercury", "libra": "venus", "scorpio": "mars",
    "sagittarius": "jupiter", "capricorn": "saturn", "aquarius": "saturn",
    "pisces": "jupiter",
}


def _get_house_lord(chart: D1Chart, house_num: int) -> Optional[str]:
    for h in chart.houses:
        if h.house_number == house_num:
            return _RASHI_LORDS.get((h.rashi or "").lower())
    return None


class UnifiedEventTimingEngine:
    """
    Synchronized multi-system event timing engine.
    """

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper
        self._horoscope_engine = HoroscopeEngine(wrapper)
        self._dasha_engine = DashaEngine(wrapper)
        self._transit_engine = TransitEngine(wrapper)
        self._ashtakavarga_engine = AshtakavargaEngine()
        self._vedha_calc = VedhaCalculator()
        self._sbc_report_service = SBCReportService(wrapper)
        self._kp_engine = KPEngine()

    def evaluate_moment(
        self,
        chart: D1Chart,
        dasha_tree: DashaTree,
        event_type: str,
        target_datetime_utc: datetime,
    ) -> UnifiedTimingSnapshot:
        """
        Evaluates the 4 systems at an exact datetime moment.
        """
        cfg = EVENT_PROFILES.get(event_type.lower(), EVENT_PROFILES["marriage"])
        required_houses = cfg["required_houses"]
        primary_cusp = cfg["primary_cusp"]
        karakas = cfg["karakas"]
        target_date = target_datetime_utc.date() if isinstance(target_datetime_utc, datetime) else target_datetime_utc

        # ── 1. Vimshottari Dasha Evaluation ──────────────────────────────────
        dasha_chain_raw = find_active_dasha_chain(dasha_tree, target_date)
        house_significators = compute_all_house_significators(chart)

        # Collect event significator planets from required houses (Grades A, B, C, D)
        event_sig_planets = set(karakas)
        for h in required_houses:
            lord = _get_house_lord(chart, h)
            if lord:
                event_sig_planets.add(lord)
            if h <= len(house_significators):
                hs = house_significators[h - 1]
                event_sig_planets.update(hs.get("grade_a", []))
                event_sig_planets.update(hs.get("grade_b", []))
                event_sig_planets.update(hs.get("grade_c", []))

        active_chain_serialized: list[dict[str, Any]] = []
        dasha_score = 0.0
        active_level_matched = None
        active_lord_matched = None

        weights_by_level = [35.0, 40.0, 25.0]  # MD, AD, PD
        level_names = ["Mahadasha", "Antardasha", "Pratyantardasha"]

        for i, period in enumerate(dasha_chain_raw[:3]):
            lord_clean = period.lord.lower()
            lvl_name = level_names[min(i, len(level_names) - 1)]
            is_sig = lord_clean in event_sig_planets

            active_chain_serialized.append({
                "level": lvl_name,
                "lord": period.lord.capitalize(),
                "start_date": period.start_date.isoformat(),
                "end_date": period.end_date.isoformat(),
            })

            if is_sig:
                dasha_score += weights_by_level[i]
                if active_level_matched is None:
                    active_level_matched = lvl_name
                    active_lord_matched = period.lord.capitalize()

        dasha_score = round(min(100.0, dasha_score), 1)
        is_dasha_active = dasha_score >= 35.0
        dasha_detail = (
            f"Active Dasha chain is running {active_lord_matched or 'period lords'} ({active_level_matched or 'general'}), "
            f"which aligns with {len(event_sig_planets)} event significators (Score: {dasha_score}%)."
            if is_dasha_active
            else "Current Mahadasha/Antardasha lords do not strongly activate the event's required houses."
        )

        dasha_evidence = DashaTimingEvidence(
            active_chain=active_chain_serialized,
            significator_lords=sorted(list(event_sig_planets)),
            is_dasha_active=is_dasha_active,
            active_level=active_level_matched,
            active_lord=active_lord_matched,
            score=dasha_score,
            detail=dasha_detail,
        )

        # ── 2. Gochara Transit Evaluation ────────────────────────────────────
        transit_results = self._transit_engine.compute_transit(chart, target_datetime_utc)
        sav = self._ashtakavarga_engine.compute_sarvashtakavarga(chart)
        sav_scores = sav.total_scores if hasattr(sav, "total_scores") else [28] * 12

        key_transits_serialized: list[dict[str, Any]] = []
        gochara_score = 0.0
        vedha_clear = True
        bindu_sum = 0
        bindu_count = 0

        # Check key transits: Jupiter, Saturn, Rahu, Mars, Venus
        lagna_rashi = chart.ascendant.rashi if chart.ascendant else "aries"
        for t in transit_results:
            is_key_planet = t.planet in ("jupiter", "saturn", "rahu", "mars", "venus", "sun")
            if not is_key_planet:
                continue

            h_lagna = _house_from_reference(lagna_rashi, t.transit_rashi)
            h_moon = t.house_from_natal_moon
            is_fav_house = bool(t.is_favorable_house) or h_lagna in cfg["gochara_favorable_houses"] or h_moon in [2, 5, 7, 9, 11]

            if t.has_vedha:
                vedha_clear = False

            b_val = sav_scores[h_lagna - 1] if 1 <= h_lagna <= 12 else 28
            bindu_sum += b_val
            bindu_count += 1

            if t.planet == "jupiter" and is_fav_house and not t.has_vedha:
                gochara_score += 35.0
            elif t.planet == "saturn" and is_fav_house and not t.has_vedha:
                gochara_score += 25.0
            elif is_fav_house and not t.has_vedha:
                gochara_score += 15.0

            key_transits_serialized.append({
                "planet": t.planet.capitalize(),
                "rashi": (t.transit_rashi or "").capitalize(),
                "house_from_lagna": h_lagna,
                "house_from_moon": h_moon,
                "is_retrograde": getattr(t, "is_retrograde", False),
                "is_favorable": is_fav_house and not t.has_vedha,
                "aspects": [],
            })

        avg_bindus = round(bindu_sum / max(1, bindu_count), 1)
        if avg_bindus >= 30:
            gochara_score += 15.0
        elif avg_bindus >= 27:
            gochara_score += 10.0

        gochara_score = round(min(100.0, max(10.0, gochara_score)), 1)
        gochara_detail = (
            f"Transits provide favorable Gochara support with average {avg_bindus} Ashtakavarga bindus. "
            f"Key transiting planets are {'clear of Vedha' if vedha_clear else 'partially obstructed by Gochara Vedha'}."
        )

        gochara_evidence = GocharaTransitEvidence(
            key_transits=key_transits_serialized,
            gochara_vedha_clear=vedha_clear,
            ashtakavarga_support=avg_bindus,
            sade_sati_status=None,
            score=gochara_score,
            detail=gochara_detail,
        )

        # ── 3. Sarvatobhadra Chakra (SBC) Vedha Evaluation ───────────────────
        sbc_report = self._sbc_report_service.build_report(
            moment_utc=target_datetime_utc,
            birth_datetime_utc=chart.birth_datetime_utc if hasattr(chart, "birth_datetime_utc") else target_datetime_utc,
        )

        janma_hits_serialized: list[dict[str, Any]] = []
        sangya_hits_serialized: list[dict[str, Any]] = []
        benefic_cnt = 0
        malefic_cnt = 0

        target_sangyas = set(cfg["sbc_sangyas"])
        for raw in sbc_report.raw_hits:
            is_janma = raw.target_key == "janma"
            is_rel_sangya = raw.target_key in target_sangyas

            if raw.nature == "benefic":
                benefic_cnt += 1
            else:
                malefic_cnt += 1

            hit_item = {
                "transiting_planet": raw.planet.capitalize(),
                "ray_direction": raw.direction,
                "from_nakshatra": raw.from_nakshatra.capitalize(),
                "target_point": raw.target_key,
                "target_name": raw.target_name,
                "nature": raw.nature,
                "impact": f"{raw.direction} ray onto {raw.target_name}",
            }

            if is_janma:
                janma_hits_serialized.append(hit_item)
            elif is_rel_sangya:
                sangya_hits_serialized.append(hit_item)

        # SBC score calculation
        sbc_score = 50.0 + (benefic_cnt * 15.0) - (malefic_cnt * 12.0)
        sbc_score = round(min(100.0, max(5.0, sbc_score)), 1)
        net_protection = round(float(benefic_cnt - malefic_cnt), 1)
        sbc_detail = (
            f"Sarvatobhadra Chakra indicates {benefic_cnt} benefic Vedha rays vs {malefic_cnt} malefic rays onto sensitive Sangyas "
            f"({', '.join(cfg['sbc_sangyas'])}). Net Vedha balance is {'protective' if net_protection >= 0 else 'challenging'}."
        )

        sbc_evidence = SBCVedhaEvidence(
            janma_hits=janma_hits_serialized,
            relevant_sangya_hits=sangya_hits_serialized,
            benefic_count=benefic_cnt,
            malefic_count=malefic_cnt,
            net_protection=net_protection,
            score=sbc_score,
            detail=sbc_detail,
        )

        # ── 4. KP Cuspal / Sub-Lord Triggers Evaluation ──────────────────────
        kp_event_key = "career" if event_type.lower() == "career" else (
            "childbirth" if event_type.lower() == "childbirth" else (
                "disease" if event_type.lower() == "health" else "marriage"
            )
        )
        kp_evidence_raw = compute_event_evidence(
            chart=chart,
            dasha_tree=dasha_tree,
            transit_results=transit_results,
            transit_datetime_utc=target_datetime_utc,
            event_key=kp_event_key,
        )
        kp_timing_list = compute_timing_analysis(chart, dasha_tree, transit_results, target_datetime_utc)
        kp_timing_item = next((t for t in kp_timing_list if t["eventKey"] == kp_event_key), None)

        csl_verdict = kp_evidence_raw["csl_verdict"]
        csl = csl_verdict.get("csl", "jupiter")
        csl_star = csl_verdict.get("csl_star_lord", "mercury")
        csl_signifies = csl_verdict.get("csl_signifies", [])
        dusthana_veto = bool(csl_verdict.get("sub_lord_veto", False))
        fructification = kp_timing_item.get("fructification", "PARTIAL") if kp_timing_item else "PARTIAL"

        transit_triggers_serialized: list[dict[str, Any]] = []
        if kp_timing_item:
            for tt in kp_timing_item.get("transit_triggers", []):
                transit_triggers_serialized.append({
                    "transit_planet": tt.get("transit_planet", "").capitalize(),
                    "transit_sign": tt.get("transit_sign", "").capitalize(),
                    "transit_nakshatra_lord": tt.get("transit_nakshatra_lord", "").capitalize(),
                    "transit_sub_lord": tt.get("transit_sub_lord", "").capitalize(),
                    "trigger_type": tt.get("trigger_type", "SUB"),
                    "significator_matched": tt.get("significator_matched", "").capitalize(),
                    "detail": tt.get("detail", ""),
                })

        rp_triggers = kp_timing_item.get("rp_triggers", []) if kp_timing_item else []

        # KP score calculation
        kp_score = 30.0
        if csl_verdict.get("promise") == "POSITIVE":
            kp_score += 35.0
        elif csl_verdict.get("promise") == "PARTIAL":
            kp_score += 20.0

        if fructification == "OPEN":
            kp_score += 25.0
        elif fructification == "PARTIAL":
            kp_score += 15.0

        if len(transit_triggers_serialized) > 0:
            kp_score += 10.0

        if dusthana_veto:
            kp_score -= 20.0

        kp_score = round(min(100.0, max(10.0, kp_score)), 1)
        kp_detail = (
            f"KP CSL of House {primary_cusp} is {csl.capitalize()} (Star Lord: {csl_star.capitalize()}), signifying houses {csl_signifies}. "
            f"Timing Fructification window is {fructification} with {len(transit_triggers_serialized)} active transit sub-triggers."
        )

        kp_evidence = KPTimingEvidence(
            primary_cusp=primary_cusp,
            csl=csl,
            csl_star_lord=csl_star,
            csl_signifies=csl_signifies,
            required_houses=required_houses,
            active_transit_triggers=transit_triggers_serialized,
            rp_triggers=rp_triggers,
            dusthana_veto=dusthana_veto,
            fructification=fructification,
            score=kp_score,
            detail=kp_detail,
        )

        # ── 5. Synchronized Confluence Calculation ───────────────────────────
        weights = {"dasha": 0.30, "gochara": 0.25, "sbc": 0.20, "kp": 0.25}
        base_score = (
            weights["dasha"] * dasha_score
            + weights["gochara"] * gochara_score
            + weights["sbc"] * sbc_score
            + weights["kp"] * kp_score
        )

        # Alignment Synergy Bonus
        high_systems_count = sum(1 for s in (dasha_score, gochara_score, sbc_score, kp_score) if s >= 50.0)
        bonus = 8.0 if high_systems_count == 4 else (4.0 if high_systems_count == 3 else 0.0)

        # Inhibitor Penalties
        penalty = 0.0
        if dusthana_veto:
            penalty += 10.0
        if not vedha_clear:
            penalty += 5.0
        if malefic_cnt >= 2 and net_protection < 0:
            penalty += 8.0

        confluence_score = round(min(100.0, max(10.0, base_score + bonus - penalty)), 1)

        if confluence_score >= 75.0:
            tier = ConfluenceTier.VERY_HIGH
        elif confluence_score >= 60.0:
            tier = ConfluenceTier.HIGH
        elif confluence_score >= 45.0:
            tier = ConfluenceTier.MODERATE
        elif confluence_score >= 30.0:
            tier = ConfluenceTier.LOW
        else:
            tier = ConfluenceTier.UNFAVORABLE

        # Extract triggers & inhibitors
        triggers: list[str] = []
        inhibitors: list[str] = []

        if is_dasha_active:
            triggers.append(f"Vimshottari Dasha: {active_lord_matched} {active_level_matched} activates event houses")
        else:
            inhibitors.append("Vimshottari Dasha: Active period lord is not a primary event significator")

        if gochara_score >= 50.0:
            triggers.append(f"Gochara Transits: Auspicious house transit with {avg_bindus} SAV bindus")
        if not vedha_clear:
            inhibitors.append("Gochara Transits: Key transit obstructed by Gochara Vedha")

        if net_protection > 0:
            triggers.append(f"Sarvatobhadra Chakra: {benefic_cnt} benefic Vedha rays protecting key Sangyas")
        elif malefic_cnt > 0:
            inhibitors.append(f"Sarvatobhadra Chakra: {malefic_cnt} malefic Vedha rays crossing Janma/Sangya points")

        if fructification == "OPEN":
            triggers.append(f"KP Sub-Lord: Window OPEN with {len(transit_triggers_serialized)} active star/sub transit triggers")
        elif fructification == "PARTIAL":
            triggers.append("KP Sub-Lord: Partial timing window active")
        else:
            inhibitors.append("KP Sub-Lord: Fructification window currently CLOSED")

        if dusthana_veto:
            inhibitors.append("KP Sub-Lord: Dusthana veto flag active (6/8/12 negation)")

        summary = (
            f"Multi-System Confluence for {cfg['label']} is {tier.value} ({confluence_score}%). "
            f"{dasha_evidence.detail} {gochara_evidence.detail} {sbc_evidence.detail} {kp_evidence.detail}"
        )

        return UnifiedTimingSnapshot(
            evaluated_datetime_utc=target_datetime_utc,
            event_type=event_type,
            dasha=dasha_evidence,
            gochara=gochara_evidence,
            sbc=sbc_evidence,
            kp=kp_evidence,
            confluence_score=confluence_score,
            confidence_tier=tier,
            system_weights=weights,
            primary_positive_triggers=triggers,
            primary_inhibiting_factors=inhibitors,
            summary_narrative=summary,
        )

    def scan_event_windows(
        self,
        chart: D1Chart,
        dasha_tree: DashaTree,
        event_type: str,
        start_date: date,
        end_date: date,
        step_days: int = 15,
        evaluation_datetime_utc: Optional[datetime] = None,
        chart_id: Optional[str] = None,
    ) -> UnifiedEventTimingScanResult:
        """
        Scans across a date range to generate continuous timeline samples
        and detect candidate event timing windows.
        """
        step = max(5, step_days)
        eval_dt = evaluation_datetime_utc or datetime.now(timezone.utc)
        current_snapshot = self.evaluate_moment(chart, dasha_tree, event_type, eval_dt)

        curr = start_date
        time_series: list[TimelineSamplePoint] = []
        raw_samples: list[tuple[date, UnifiedTimingSnapshot]] = []

        while curr <= end_date:
            sample_dt = datetime(curr.year, curr.month, curr.day, 12, 0, 0, tzinfo=timezone.utc)
            snap = self.evaluate_moment(chart, dasha_tree, event_type, sample_dt)
            raw_samples.append((curr, snap))

            time_series.append(
                TimelineSamplePoint(
                    date=curr.isoformat(),
                    confluence_score=snap.confluence_score,
                    dasha_score=snap.dasha.score,
                    gochara_score=snap.gochara.score,
                    sbc_score=snap.sbc.score,
                    kp_score=snap.kp.score,
                    peak_flag=False,
                )
            )
            curr += timedelta(days=step)

        # ── Cluster contiguous intervals into Candidate Windows ─────────────
        candidate_windows: list[UnifiedEventTimingWindow] = []
        in_window = False
        window_start = None
        window_samples: list[tuple[date, UnifiedTimingSnapshot]] = []
        threshold = 55.0  # Confluence threshold for open window

        for d, snap in raw_samples:
            if snap.confluence_score >= threshold:
                if not in_window:
                    in_window = True
                    window_start = d
                    window_samples = [(d, snap)]
                else:
                    window_samples.append((d, snap))
            else:
                if in_window and window_start is not None and len(window_samples) > 0:
                    in_window = False
                    w = self._build_window(event_type, window_start, window_samples[-1][0], window_samples)
                    candidate_windows.append(w)
                    window_samples = []

        if in_window and window_start is not None and len(window_samples) > 0:
            w = self._build_window(event_type, window_start, window_samples[-1][0], window_samples)
            candidate_windows.append(w)

        # Mark peak flags in time series
        peak_dates_set = {w.peak_date.isoformat() for w in candidate_windows}
        adjusted_time_series = [
            TimelineSamplePoint(
                date=pt.date,
                confluence_score=pt.confluence_score,
                dasha_score=pt.dasha_score,
                gochara_score=pt.gochara_score,
                sbc_score=pt.sbc_score,
                kp_score=pt.kp_score,
                peak_flag=pt.date in peak_dates_set,
            )
            for pt in time_series
        ]

        summary_text = (
            f"Detected {len(candidate_windows)} candidate timing windows for {event_type.capitalize()} "
            f"between {start_date.isoformat()} and {end_date.isoformat()} across Dasha, Gochara, SBC, and KP systems."
        )

        return UnifiedEventTimingScanResult(
            chart_id=chart_id,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            evaluated_moment_snapshot=current_snapshot,
            candidate_windows=candidate_windows,
            time_series=adjusted_time_series,
            confluence_summary=summary_text,
        )

    def _build_window(
        self,
        event_type: str,
        start_d: date,
        end_d: date,
        samples: list[tuple[date, UnifiedTimingSnapshot]],
    ) -> UnifiedEventTimingWindow:
        # Find peak score and sample
        peak_date, peak_snap = max(samples, key=lambda item: item[1].confluence_score)
        w_id = f"win-{event_type[:3]}-{start_d.strftime('%Y%m')}-{int(peak_snap.confluence_score)}"

        if peak_snap.confluence_score >= 75.0:
            status = WindowConfluenceStatus.HIGH_CONFLUENCE
        elif peak_snap.confluence_score >= 60.0:
            status = WindowConfluenceStatus.MODERATE_CONFLUENCE
        elif any(f == "CLOSED" for f in [peak_snap.kp.fructification]):
            status = WindowConfluenceStatus.INHIBITED
        else:
            status = WindowConfluenceStatus.PARTIAL_WINDOW

        narrative = (
            f"Fructification window ({start_d.isoformat()} → {end_d.isoformat()}) peaking around {peak_date.isoformat()} "
            f"with {peak_snap.confluence_score}% synchronization. "
            f"Dasha: {peak_snap.dasha.active_lord or 'Active lord'} ({peak_snap.dasha.score}%), "
            f"Gochara: {peak_snap.gochara.score}%, SBC Vedha: {peak_snap.sbc.score}%, KP: {peak_snap.kp.fructification} ({peak_snap.kp.score}%)."
        )

        return UnifiedEventTimingWindow(
            window_id=w_id,
            event_type=event_type,
            start_date=start_d,
            end_date=end_d,
            peak_date=peak_date,
            peak_score=peak_snap.confluence_score,
            confluence_status=status,
            system_scores={
                "dasha": peak_snap.dasha.score,
                "gochara": peak_snap.gochara.score,
                "sbc": peak_snap.sbc.score,
                "kp": peak_snap.kp.score,
            },
            primary_drivers=peak_snap.primary_positive_triggers,
            inhibiting_factors=peak_snap.primary_inhibiting_factors,
            narrative=narrative,
        )
