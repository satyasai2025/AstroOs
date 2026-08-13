"""
AstroOS — Jaimini Module Orchestrator (Layer 6: Calculation Engine)

Composes every Jaimini engine (Chara Karaka, Arudha, Rashi Aspect,
Karakamsa, Chara/Narayana Dasha via jaimini_dasha_adapter, and the
Jaimini Yoga Engine) into a single "compute everything for this chart"
entry point — so a caller (eventually apps/api/routers/jaimini.py) makes
one call instead of manually sequencing 7 engines in the right
dependency order.

Deliberately NOT built on apps/api/services/orchestration/'s Stage/
Pipeline framework (the one WorkflowOrchestrator uses). That framework
earns its keep tracing async, I/O-bound, partially-failable stages (DB
persistence, repository calls, external verification). Every engine
composed here is a synchronous, pure, in-memory computation over an
already-fetched D1/D9 chart pair — there is no I/O to trace and no
per-stage partial-failure semantics worth isolating. This class is a
plain composition/facade, matching every other *_engine.py's style in
this codebase, not a new orchestration pattern.

Argala is intentionally excluded from compute_bundle's result: unlike
the other 6 engines, it requires a per-call reference point (a sign or
planet) rather than being computable once per chart, so it's exposed as
a separate method (compute_argala) instead of forced into the single
bundled result.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import (
    ArgalaResult,
    ArudhaResult,
    CharaKarakaResult,
    CharaKarakaScheme,
    JaiminiDashaResult,
    KarakamsaResult,
    RashiAspectResult,
)
from apps.api.domain.prediction_evidence import PredictionEvidence
from apps.api.services.argala_engine import ArgalaEngine
from apps.api.services.arudha_engine import ArudhaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.jaimini_dasha_adapter import JaiminiDashaAdapter
from apps.api.services.jaimini_engine import CharaKarakaEngine
from apps.api.services.jaimini_yoga_context import JaiminiYogaContext
from apps.api.services.jaimini_yoga_engine import JaiminiYogaEngine
from apps.api.services.karakamsa_engine import KarakamsaEngine
from apps.api.services.rashi_aspect_engine import RashiAspectEngine


@dataclass(frozen=True)
class JaiminiBundle:
    """Every chart-level (not per-reference-point) Jaimini result for
    one birth chart, computed together in the correct dependency order."""

    d1_chart: D1Chart
    chara_karaka: CharaKarakaResult
    arudha: ArudhaResult
    rashi_aspect: RashiAspectResult
    karakamsa: Optional[KarakamsaResult]
    chara_dasha: JaiminiDashaResult
    narayana_dasha: JaiminiDashaResult
    yogas: tuple[PredictionEvidence, ...]


class JaiminiOrchestrator:
    """
    Composition root for the Jaimini module.

    Holds constructor-injected engine instances (same shape as
    HoroscopeEngine/DivisionalEngine holding self._wrapper) but performs
    no per-call state mutation — calling compute_bundle twice never
    changes this instance. Contains no calculation logic of its own:
    every number in JaiminiBundle comes from one of the composed
    engines, never computed here directly.
    """

    def __init__(self, ephemeris_wrapper: EphemerisWrapper) -> None:
        self._horoscope_engine = HoroscopeEngine(ephemeris_wrapper)
        self._divisional_engine = DivisionalEngine(ephemeris_wrapper)
        self._dasha_adapter = JaiminiDashaAdapter(DashaEngine(ephemeris_wrapper))
        self._chara_karaka_engine = CharaKarakaEngine()
        self._arudha_engine = ArudhaEngine()
        self._rashi_aspect_engine = RashiAspectEngine()
        self._karakamsa_engine = KarakamsaEngine(self._chara_karaka_engine)
        self._argala_engine = ArgalaEngine()
        self._yoga_engine = JaiminiYogaEngine()

    def compute_bundle(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        scheme: CharaKarakaScheme = "sapta_karaka",
        max_dasha_depth: int = 3,
        include_karakamsa: bool = True,
    ) -> JaiminiBundle:
        """
        Compute every chart-level Jaimini result for one birth moment, in
        the correct dependency order:

            D1 -> (Chara Karaka, Arudha, Rashi Aspect)
               -> [D9 -> Karakamsa]  (only if include_karakamsa)
               -> Chara/Narayana Dasha
               -> Jaimini Yogas (consumes all of the above via
                  JaiminiYogaContext)
        """
        d1_chart = self._horoscope_engine.generate_d1(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )
        chara_karaka = self._chara_karaka_engine.compute(d1_chart, scheme=scheme)
        arudha = self._arudha_engine.compute(d1_chart)
        rashi_aspect = self._rashi_aspect_engine.compute(d1_chart)

        karakamsa: Optional[KarakamsaResult] = None
        if include_karakamsa:
            d9_chart = self._divisional_engine.compute(
                birth_datetime_utc=birth_datetime_utc,
                latitude=latitude,
                longitude=longitude,
                varga="D9",
                ayanamsa=ayanamsa,
                house_system=house_system,
            )
            karakamsa = self._karakamsa_engine.compute(d1_chart, d9_chart, scheme=scheme)

        chara_dasha = self._dasha_adapter.compute_chara(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
            max_depth=max_dasha_depth,
        )
        narayana_dasha = self._dasha_adapter.compute_narayana(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
            max_depth=max_dasha_depth,
        )

        yoga_ctx = JaiminiYogaContext(
            d1_chart=d1_chart,
            chara_karaka=chara_karaka,
            arudha=arudha,
            rashi_aspect=rashi_aspect,
            karakamsa=karakamsa,
        )
        yogas = tuple(self._yoga_engine.evaluate_all(yoga_ctx))

        return JaiminiBundle(
            d1_chart=d1_chart,
            chara_karaka=chara_karaka,
            arudha=arudha,
            rashi_aspect=rashi_aspect,
            karakamsa=karakamsa,
            chara_dasha=chara_dasha,
            narayana_dasha=narayana_dasha,
            yogas=yogas,
        )

    def compute_argala(self, d1_chart: D1Chart, reference: str) -> ArgalaResult:
        """
        Argala needs a per-call reference point (a sign or planet name),
        so it is not part of the single bundled result — call this
        separately once you have a D1Chart (e.g. JaiminiBundle.d1_chart
        from compute_bundle, to avoid recomputing the chart).
        """
        return self._argala_engine.compute(d1_chart, reference)
