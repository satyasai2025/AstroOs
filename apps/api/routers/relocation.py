"""
AstroOS — Relocation Analysis Router

Adapter-only HTTP surface for the relocation engine + the four relocation
technique fixtures. Computes facts for a birth->target pair server-side,
executes the four techniques, and maps results to HTTP. No astrology and no
rule logic live here (same discipline as routers/technique.py).
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter

from apps.api.domain.facts import Fact
from apps.api.schemas.relocation import (
    RelocationAnalyzeRequest,
    RelocationAnalyzeResponse,
    RelocationAngleSchema,
    RelocationTechniqueSchema,
    RelocationTriggerSchema,
)
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.relocation_engine import RelocationEngine
from apps.api.services.technique_engine import TechniqueEngine
from apps.api.services.technique_resolver import TechniqueResolver
# Importing this registers the bundled relocation technique fixtures.
from apps.api.services.techniques import (  # noqa: F401
    harmonic_interpretation,
    midpoints_to_angles,
    paran_crossings,
    sun_angular,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/relocation", tags=["relocation"])

_RELOCATION_TECHNIQUE_IDS = (
    "paran_crossings",
    "sun_angular",
    "midpoints_to_angles",
    "harmonic_interpretation",
)


def _to_angle_schema(registry: FactRegistry, name: str) -> RelocationAngleSchema:
    base = f"relocation.{name}"
    return RelocationAngleSchema(
        degree=registry.get_value(f"{base}.degree", 0.0),
        sign=registry.get_value(f"{base}.sign", ""),
        label=registry.get_value(f"{base}.label", 0.0),
        harmonic_family=registry.get_value(f"{base}.harmonic_family", ""),
    )


def _to_trigger_schema(trigger) -> RelocationTriggerSchema:
    return RelocationTriggerSchema(
        rule_id=trigger.rule_id,
        rule_name=trigger.rule_name,
        role=trigger.role.value,
        status=trigger.status.value,
        provenance=trigger.provenance.value,
        matched_conditions=list(trigger.matched_conditions),
        failed_conditions=list(trigger.failed_conditions),
        missing_facts=list(trigger.missing_facts),
        explanation=trigger.explanation,
    )


@router.post("/analyze", response_model=RelocationAnalyzeResponse)
def analyze_relocation(body: RelocationAnalyzeRequest) -> RelocationAnalyzeResponse:
    engine = RelocationEngine(ayanamsa=body.ayanamsa, house_system=body.house_system)
    facts = engine.compute_facts(
        body.birth_utc,
        body.birth_lat,
        body.birth_lon,
        body.target_lat,
        body.target_lon,
    )

    registry = FactRegistry()
    for fact in facts:
        registry.add_fact(fact)

    resolver = TechniqueResolver()
    tech_engine = TechniqueEngine()
    techniques: list[RelocationTechniqueSchema] = []
    for tech_id in _RELOCATION_TECHNIQUE_IDS:
        tech = resolver.resolve_by_id(tech_id, 1)
        if tech is None:
            continue
        result = tech_engine.execute(tech, registry)
        techniques.append(
            RelocationTechniqueSchema(
                technique_id=result.technique_id,
                technique_name=tech.name,
                confidence=result.confidence,
                confidence_basis=result.confidence_basis,
                is_matched=any(
                    t.status.value == "triggered" for t in result.triggers
                ),
                triggers=[_to_trigger_schema(t) for t in result.triggers],
            )
        )

    return RelocationAnalyzeResponse(
        birth={"lat": body.birth_lat, "lon": body.birth_lon},
        target={"lat": body.target_lat, "lon": body.target_lon},
        angles={
            "ascendant": _to_angle_schema(registry, "ascendant"),
            "midheaven": _to_angle_schema(registry, "midheaven"),
        },
        techniques=techniques,
        facts={
            "relocation.midpoints.asc.count": registry.get_value(
                "relocation.midpoints.asc.count", 0
            ),
            "relocation.midpoints.mc.count": registry.get_value(
                "relocation.midpoints.mc.count", 0
            ),
            "relocation.midpoints.asc.double": registry.get_value(
                "relocation.midpoints.asc.double", False
            ),
            "relocation.midpoints.mc.double": registry.get_value(
                "relocation.midpoints.mc.double", False
            ),
            "relocation.paran.count": registry.get_value("relocation.paran.count", 0),
            "relocation.lines.paran.count": registry.get_value(
                "relocation.lines.paran.count", 0
            ),
        },
    )
