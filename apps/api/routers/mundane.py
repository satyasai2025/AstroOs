"""
AstroOS — Mundane Astrology (Medini Jyotisha / Samhita) Router
Endpoints for Chaitra Shukla Pratipada, Planetary Cabinet, Eclipses, Kurma Chakra, and National Forecasts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.mundane import (
    CabinetMinisterSchema,
    IngressChartRequest,
    IngressChartResponse,
    IngressMomentSchema,
    KurmaChakraResponse,
    KurmaSectorStatusSchema,
    MundaneBhavaEvaluationSchema,
    MundaneEclipseSchema,
    NationalForecastResponse,
    PlanetaryCabinetResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.kurma_chakra_engine import KurmaChakraEngine
from apps.api.services.mundane_analysis_engine import MundaneAnalysisEngine
from apps.api.services.mundane_eclipse_engine import MundaneEclipseEngine
from apps.api.services.mundane_ingress_engine import MundaneIngressEngine
from apps.api.services.planetary_cabinet_engine import PlanetaryCabinetEngine

router = APIRouter(prefix="/research/mundane", tags=["Research: Mundane Astrology & Geopolitics"])


@router.post("/chaitra-pratipada", response_model=IngressChartResponse, status_code=status.HTTP_200_OK)
def get_chaitra_pratipada_chart(
    req: IngressChartRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> IngressChartResponse:
    """Computes Chaitra Shukla Pratipada Annual Ingress Horoscope for national capital."""
    engine = MundaneIngressEngine(wrapper)
    moment = engine.find_chaitra_shukla_pratipada(req.year, req.ayanamsa)
    chart_res = engine.generate_ingress_chart(
        moment=moment,
        country_name=req.country_name,
        capital_city=req.capital_city,
        latitude=req.latitude,
        longitude=req.longitude,
        ayanamsa=req.ayanamsa,
    )

    return IngressChartResponse(
        ingress_moment=IngressMomentSchema(
            ingress_type=moment.ingress_type.value,
            timestamp_utc=moment.timestamp_utc,
            sun_longitude=moment.sun_longitude,
            moon_longitude=moment.moon_longitude,
            weekday=moment.weekday,
            weekday_lord=moment.weekday_lord,
        ),
        country_name=chart_res.country_name,
        capital_city=chart_res.capital_city,
        ascendant_rashi=chart_res.ascendant_rashi,
        ascendant_lord=chart_res.ascendant_lord,
        tenth_house_rashi=chart_res.tenth_house_rashi,
        tenth_house_lord=chart_res.tenth_house_lord,
    )


@router.get("/planetary-cabinet/{year}", response_model=PlanetaryCabinetResponse, status_code=status.HTTP_200_OK)
def get_planetary_cabinet(
    year: int,
    ayanamsa: str = Query(default="lahiri"),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> PlanetaryCabinetResponse:
    """Calculates the 9-Minister Planetary Cabinet (Nava Nayakas) for the astrological year."""
    ingress_engine = MundaneIngressEngine(wrapper)
    cab_engine = PlanetaryCabinetEngine(ingress_engine)
    cabinet = cab_engine.calculate_cabinet(year, ayanamsa)

    min_schemas = [
        CabinetMinisterSchema(
            portfolio=m.portfolio,
            planet=m.planet,
            basis_ingress=m.basis_ingress,
            is_benefic=m.is_benefic,
            impact_summary=m.impact_summary,
        )
        for m in cabinet.ministers
    ]

    return PlanetaryCabinetResponse(
        year=cabinet.year,
        ministers=min_schemas,
        overall_balance_score=cabinet.overall_balance_score,
        governance_climate=cabinet.governance_climate,
        classical_summary=cabinet.classical_summary,
    )


@router.get("/eclipses/{year}", response_model=list[MundaneEclipseSchema], status_code=status.HTTP_200_OK)
def get_mundane_eclipses(
    year: int,
    ayanamsa: str = Query(default="lahiri"),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> list[MundaneEclipseSchema]:
    """Scans and calculates solar & lunar eclipses and duration of impact."""
    ecl_engine = MundaneEclipseEngine(wrapper)
    eclipses = ecl_engine.find_eclipses_for_year(year, ayanamsa)

    return [
        MundaneEclipseSchema(
            eclipse_type=e.eclipse_type.value,
            peak_utc=e.peak_utc,
            eclipsed_rashi=e.eclipsed_rashi,
            eclipsed_nakshatra=e.eclipsed_nakshatra,
            node_involved=e.node_involved,
            duration_hours=e.duration_hours,
            impact_duration_months=e.impact_duration_months,
            afflicted_directions=[d.value for d in e.afflicted_directions],
            impact_summary=e.impact_summary,
        )
        for e in eclipses
    ]


@router.get("/kurma-chakra", response_model=KurmaChakraResponse, status_code=status.HTTP_200_OK)
def get_kurma_chakra_state(
    dt_iso: Optional[str] = Query(default=None, description="ISO datetime string, defaults to UTC now"),
    ayanamsa: str = Query(default="lahiri"),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> KurmaChakraResponse:
    """Evaluates 9-directional Kurma Chakra geopolitical vulnerability."""
    dt = datetime.fromisoformat(dt_iso.replace("Z", "+00:00")) if dt_iso else datetime.now(timezone.utc)
    kurma_engine = KurmaChakraEngine(wrapper)
    state = kurma_engine.evaluate_state(dt, ayanamsa)

    sectors = [
        KurmaSectorStatusSchema(
            direction=s.direction.value,
            nakshatras=list(s.nakshatras),
            traditional_regions=list(s.traditional_regions),
            transiting_malefics=list(s.transiting_malefics),
            transiting_benefics=list(s.transiting_benefics),
            is_afflicted=s.is_afflicted,
            severity=s.severity,
            risk_summary=s.risk_summary,
        )
        for s in state.sectors
    ]

    return KurmaChakraResponse(
        evaluated_at=state.evaluated_at,
        sectors=sectors,
        highest_risk_directions=[d.value for d in state.highest_risk_directions],
        summary=state.summary,
    )


@router.post("/national-forecast", response_model=NationalForecastResponse, status_code=status.HTTP_200_OK)
def get_national_forecast(
    req: IngressChartRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> NationalForecastResponse:
    """Generates complete comprehensive national forecast integrating Ingress, Cabinet, Eclipses, and Kurma Chakra."""
    analysis_engine = MundaneAnalysisEngine(wrapper)
    forecast = analysis_engine.generate_forecast(
        country_name=req.country_name,
        capital_city=req.capital_city,
        latitude=req.latitude,
        longitude=req.longitude,
        year=req.year,
        ayanamsa=req.ayanamsa,
    )

    cab_schemas = [
        CabinetMinisterSchema(
            portfolio=m.portfolio,
            planet=m.planet,
            basis_ingress=m.basis_ingress,
            is_benefic=m.is_benefic,
            impact_summary=m.impact_summary,
        )
        for m in forecast.planetary_cabinet.ministers
    ]

    cab_resp = PlanetaryCabinetResponse(
        year=forecast.planetary_cabinet.year,
        ministers=cab_schemas,
        overall_balance_score=forecast.planetary_cabinet.overall_balance_score,
        governance_climate=forecast.planetary_cabinet.governance_climate,
        classical_summary=forecast.planetary_cabinet.classical_summary,
    )

    ecl_resp = [
        MundaneEclipseSchema(
            eclipse_type=e.eclipse_type.value,
            peak_utc=e.peak_utc,
            eclipsed_rashi=e.eclipsed_rashi,
            eclipsed_nakshatra=e.eclipsed_nakshatra,
            node_involved=e.node_involved,
            duration_hours=e.duration_hours,
            impact_duration_months=e.impact_duration_months,
            afflicted_directions=[d.value for d in e.afflicted_directions],
            impact_summary=e.impact_summary,
        )
        for e in forecast.active_eclipses
    ]

    kurma_resp = KurmaChakraResponse(
        evaluated_at=forecast.kurma_state.evaluated_at,
        sectors=[
            KurmaSectorStatusSchema(
                direction=s.direction.value,
                nakshatras=list(s.nakshatras),
                traditional_regions=list(s.traditional_regions),
                transiting_malefics=list(s.transiting_malefics),
                transiting_benefics=list(s.transiting_benefics),
                is_afflicted=s.is_afflicted,
                severity=s.severity,
                risk_summary=s.risk_summary,
            )
            for s in forecast.kurma_state.sectors
        ],
        highest_risk_directions=[d.value for d in forecast.kurma_state.highest_risk_directions],
        summary=forecast.kurma_state.summary,
    )

    bhava_schemas = [
        MundaneBhavaEvaluationSchema(
            house_number=b.house_number,
            signification=b.signification,
            rashi=b.rashi,
            lord=b.lord,
            occupants=list(b.occupants),
            strength_score=b.strength_score,
            outlook=b.outlook,
        )
        for b in forecast.bhava_evaluations
    ]

    return NationalForecastResponse(
        country_name=forecast.country_name,
        capital_city=forecast.capital_city,
        year=forecast.year,
        planetary_cabinet=cab_resp,
        active_eclipses=ecl_resp,
        kurma_state=kurma_resp,
        bhava_evaluations=bhava_schemas,
        economic_index=forecast.economic_index,
        defense_security_index=forecast.defense_security_index,
        political_stability_index=forecast.political_stability_index,
        public_health_index=forecast.public_health_index,
        executive_summary=forecast.executive_summary,
    )
