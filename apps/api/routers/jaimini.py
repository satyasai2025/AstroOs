"""
AstroOS — Jaimini Router (Layer 7: API Integration)

Endpoints
---------
POST /api/v1/jaimini/bundle — Compute every chart-level Jaimini result
    (Chara Karaka, Arudha, Rashi Aspect, Karakamsa/Swamsa, Chara/Narayana
    Dasha, Jaimini Yogas) for one birth chart in a single call.
POST /api/v1/jaimini/argala — Compute Argala/Virodhargala from a
    reference sign or planet (needs a per-call reference point, so it is
    not part of the bundle — see JaiminiOrchestrator.compute_argala).

No business logic lives here — all computation is delegated to
JaiminiOrchestrator, which itself only composes the existing Jaimini
engines. This router is a thin HTTP adapter, matching every other
engine-wrapping router in this codebase (routers/divisional.py,
routers/dasha.py, ...).
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.jaimini import (
    ArgalaResult,
    ArudhaResult,
    CharaKarakaResult,
    JaiminiDashaResult,
    KarakamsaResult,
    RashiAspectResult,
)
from apps.api.domain.prediction_evidence import PredictionEvidence
from apps.api.schemas.jaimini import (
    ArgalaPairSchema,
    ArudhaPadaSchema,
    CharaKarakaSchema,
    JaiminiArgalaRequest,
    JaiminiArgalaResponse,
    JaiminiArudhaResponse,
    JaiminiAspectsResponse,
    JaiminiBundleRequest,
    JaiminiBundleResponse,
    JaiminiDashaResponse,
    JaiminiKarakamsaResponse,
    JaiminiKarakasResponse,
    JaiminiDashaPeriodSchema,
    KarakamsaHouseEntrySchema,
    PredictionConfidenceSchema,
    PredictionEvidenceSchema,
    PredictionReasonSchema,
    PredictionRuleSchema,
    RashiAspectSchema,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.jaimini_orchestrator import JaiminiOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jaimini", tags=["Jaimini"])


# ── DI helper ────────────────────────────────────────────────────────────────


def _get_jaimini_orchestrator(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> JaiminiOrchestrator:
    """
    Build a JaiminiOrchestrator using the process-wide EphemerisWrapper
    singleton. Does NOT construct a new EphemerisWrapper — see
    get_ephemeris_wrapper's docstring for why that would reintroduce a
    global-state race condition.
    """
    return JaiminiOrchestrator(wrapper)


# ── Serialisation helpers ──────────────────────────────────────────────────────


def _serialise_karakas(result: CharaKarakaResult) -> JaiminiKarakasResponse:
    karakas = [
        CharaKarakaSchema(
            rank=k.rank,
            karaka_name=k.karaka_name,
            planet=k.planet,
            rashi=k.rashi,
            rashi_degree=k.rashi_degree,
            karaka_degree=k.karaka_degree,
            speed_deg_per_day=k.speed_deg_per_day,
            is_retrograde=k.is_retrograde,
            tiebreak_rule=k.tiebreak_rule,
        )
        for k in result.karakas
    ]
    return JaiminiKarakasResponse(
        scheme=result.scheme,
        karakas=karakas,
        atmakaraka=karakas[0],
        darakaraka=karakas[-1],
    )


def _serialise_arudha(result: ArudhaResult) -> JaiminiArudhaResponse:
    padas = [
        ArudhaPadaSchema(
            house_number=p.house_number,
            pada_name=p.pada_name,
            rashi=p.rashi,
            raw_rashi=p.raw_rashi,
            lord=p.lord,
            lord_rashi=p.lord_rashi,
            exception_applied=p.exception_applied,
        )
        for p in result.padas
    ]
    return JaiminiArudhaResponse(
        padas=padas,
        arudha_lagna=padas[0],
        upapada_lagna=padas[11],
    )


def _serialise_aspects(result: RashiAspectResult) -> JaiminiAspectsResponse:
    return JaiminiAspectsResponse(
        matrix={sign: list(targets) for sign, targets in result.matrix.items()},
        aspects=[
            RashiAspectSchema(
                from_rashi=a.from_rashi,
                to_rashi=a.to_rashi,
                aspecting_planets=list(a.aspecting_planets),
                aspected_planets=list(a.aspected_planets),
            )
            for a in result.aspects
        ],
    )


def _serialise_karakamsa(result: KarakamsaResult) -> JaiminiKarakamsaResponse:
    return JaiminiKarakamsaResponse(
        scheme=result.scheme,
        atmakaraka=result.atmakaraka,
        karakamsa_rashi=result.karakamsa_rashi,
        swamsa_rashi=result.swamsa_rashi,
        d1_atmakaraka_rashi=result.d1_atmakaraka_rashi,
        d1_lagna_rashi=result.d1_lagna_rashi,
        relative_houses=[
            KarakamsaHouseEntrySchema(
                house_number=h.house_number,
                rashi=h.rashi,
                planets=list(h.planets),
            )
            for h in result.relative_houses
        ],
    )


def _serialise_dasha_period(period) -> JaiminiDashaPeriodSchema:
    return JaiminiDashaPeriodSchema(
        rashi=period.rashi,
        start_date=period.start_date,
        end_date=period.end_date,
        duration_days=period.duration_days,
        level=period.level,
        sub_periods=[_serialise_dasha_period(p) for p in period.sub_periods],
    )


def _serialise_dasha(result: JaiminiDashaResult) -> JaiminiDashaResponse:
    return JaiminiDashaResponse(
        system=result.system,
        lagna_rashi=result.lagna_rashi,
        periods=[_serialise_dasha_period(p) for p in result.periods],
        max_depth=result.max_depth,
        total_cycle_years=result.total_cycle_years,
    )


def _serialise_evidence(evidence: PredictionEvidence) -> PredictionEvidenceSchema:
    return PredictionEvidenceSchema(
        rule=PredictionRuleSchema(
            rule_id=evidence.rule.rule_id,
            name=evidence.rule.name,
            sutra_reference=evidence.rule.sutra_reference,
            rule_version=evidence.rule.rule_version,
            requires=list(evidence.rule.requires),
        ),
        is_matched=evidence.is_matched,
        triggering_conditions=list(evidence.triggering_conditions),
        reasons=[
            PredictionReasonSchema(
                description=r.description,
                matched_objects=list(r.matched_objects),
                is_satisfied=r.is_satisfied,
            )
            for r in evidence.reasons
        ],
        confidence=PredictionConfidenceSchema(
            score=evidence.confidence.score,
            satisfied_conditions=evidence.confidence.satisfied_conditions,
            total_conditions=evidence.confidence.total_conditions,
            basis=evidence.confidence.basis,
        ),
        explanation=evidence.explanation,
    )


def _serialise_argala(result: ArgalaResult) -> JaiminiArgalaResponse:
    return JaiminiArgalaResponse(
        reference_rashi=result.reference_rashi,
        reference_label=result.reference_label,
        pairs=[
            ArgalaPairSchema(
                argala_house=p.argala_house,
                virodhargala_house=p.virodhargala_house,
                argala_rashi=p.argala_rashi,
                virodhargala_rashi=p.virodhargala_rashi,
                argala_planets=list(p.argala_planets),
                virodhargala_planets=list(p.virodhargala_planets),
                is_active=p.is_active,
                is_cancelled=p.is_cancelled,
                strength_score=p.strength_score,
            )
            for p in result.pairs
        ],
        net_strength=result.net_strength,
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/bundle",
    response_model=JaiminiBundleResponse,
    summary="Compute every chart-level Jaimini result",
    description=(
        "Chara Karaka, Arudha Padas (A1-A12), Rashi Aspect, Karakamsa/Swamsa "
        "(unless include_karakamsa=false), Chara Dasha, Narayana Dasha, and "
        "every registered Jaimini yoga — computed together in the correct "
        "dependency order via JaiminiOrchestrator."
    ),
)
async def compute_jaimini_bundle(
    body: JaiminiBundleRequest,
    orchestrator: JaiminiOrchestrator = Depends(_get_jaimini_orchestrator),
) -> JaiminiBundleResponse:
    try:
        # Blocking pyswisseph call (via HoroscopeEngine/DivisionalEngine
        # inside the orchestrator) — offload to a worker thread so it does
        # not freeze the event loop. See horoscope.py's generate_d1_chart
        # for the full rationale.
        bundle = await asyncio.to_thread(
            orchestrator.compute_bundle,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
            scheme=body.scheme,
            max_dasha_depth=body.max_dasha_depth,
            include_karakamsa=body.include_karakamsa,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing Jaimini bundle: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Jaimini bundle.",
        )

    return JaiminiBundleResponse(
        chara_karaka=_serialise_karakas(bundle.chara_karaka),
        arudha=_serialise_arudha(bundle.arudha),
        rashi_aspect=_serialise_aspects(bundle.rashi_aspect),
        karakamsa=_serialise_karakamsa(bundle.karakamsa) if bundle.karakamsa else None,
        chara_dasha=_serialise_dasha(bundle.chara_dasha),
        narayana_dasha=_serialise_dasha(bundle.narayana_dasha),
        yogas=[_serialise_evidence(y) for y in bundle.yogas],
    )


@router.post(
    "/argala",
    response_model=JaiminiArgalaResponse,
    summary="Compute Argala/Virodhargala from a reference sign or planet",
    description=(
        "The 4 Argala/Virodhargala pairs (2nd/12th, 4th/10th, 5th/9th, "
        "11th/3rd, counted inclusively from the reference), plus their net "
        "strength. Recomputes the D1 chart, then counts from `reference` "
        "(a rashi name or planet name)."
    ),
)
async def compute_jaimini_argala(
    body: JaiminiArgalaRequest,
    orchestrator: JaiminiOrchestrator = Depends(_get_jaimini_orchestrator),
) -> JaiminiArgalaResponse:
    try:
        d1_chart = await asyncio.to_thread(
            orchestrator.compute_d1_chart,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        argala = orchestrator.compute_argala(d1_chart, body.reference)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing Jaimini argala: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Argala.",
        )

    return _serialise_argala(argala)
