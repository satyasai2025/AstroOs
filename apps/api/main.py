"""
AstroOS API — Application Entry Point

Creates the FastAPI application using the factory pattern.
No global mutable state at module level (except app itself).
Configuration is dependency-injected where needed.
"""

import logging
import re
import ssl
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
import truststore
from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from timezonefinder import TimezoneFinder

from apps.api.config import get_settings
from apps.api.dependencies import (
    require_admin,
    require_authenticated,
    require_researcher,
)
from apps.api.routers import admin as admin_router
from apps.api.routers import admin_auth as admin_auth_router
from apps.api.routers import ai as ai_router
from apps.api.routers import ai_phase_e as ai_phase_e_router
from apps.api.routers import ai_settings as ai_settings_router
from apps.api.routers import ashtakavarga as ashtakavarga_router
from apps.api.routers import auth
from apps.api.routers import batch as batch_router
from apps.api.routers import benchmark as benchmark_router
from apps.api.routers import calendar as calendar_router
from apps.api.routers import continuous_monitoring as continuous_monitoring_router
from apps.api.routers import dasha as dasha_router
from apps.api.routers import dataset_import as dataset_import_router
from apps.api.routers import datasets as datasets_router
from apps.api.routers import divisional as divisional_router
from apps.api.routers import digital_twin as digital_twin_router
from apps.api.routers import events as events_router
from apps.api.routers import event_analysis as event_analysis_router
from apps.api.routers import export as export_router
from apps.api.routers import geocoding as geocoding_router
from apps.api.routers import governance as governance_router
from apps.api.routers import guru_research as guru_research_router
from apps.api.routers import horoscope as horoscope_router
from apps.api.routers import intelligence as intelligence_router
from apps.api.routers import jaimini as jaimini_router
from apps.api.routers import jobs as jobs_router
from apps.api.routers import knowledge as knowledge_router
from apps.api.routers import knowledge_graph as knowledge_graph_router
from apps.api.routers import kp as kp_router
from apps.api.routers import muhurta as muhurta_router
from apps.api.routers import prashna as prashna_router
from apps.api.routers import report as report_router
from apps.api.routers import report_full as report_full_router
from apps.api.routers import research as research_router
from apps.api.routers import search as search_router
from apps.api.routers import research_tools as research_tools_router
from apps.api.routers import avastha as avastha_router
from apps.api.routers import vimsopaka as vimsopaka_router
from apps.api.routers import collab as collab_router
from apps.api.routers import sbc as sbc_router
from apps.api.routers import shadbala as shadbala_router
from apps.api.routers import statistics as statistics_router
from apps.api.routers import tarabala as tarabala_router
from apps.api.routers import technique as technique_router
from apps.api.routers import custom_techniques as custom_techniques_router
from apps.api.routers import benchmark as benchmark_router
from apps.api.routers import prediction_orchestration as prediction_orchestration_router
from apps.api.routers import research_calibration as research_calibration_router
from apps.api.routers import research_reproducibility as research_reproducibility_router
from apps.api.routers import decision_synthesis as decision_synthesis_router
from apps.api.routers import research_knowledge_graph as research_knowledge_graph_router
from apps.api.routers import decision_action as decision_action_router
from apps.api.routers import portfolio_planner as portfolio_planner_router
from apps.api.routers import longitudinal_tracking as longitudinal_tracking_router
from apps.api.routers import adaptive_research as adaptive_research_router
from apps.api.routers import benchmark_expansion as benchmark_expansion_router
from apps.api.routers import research_publication as research_publication_router
from apps.api.routers import research_forensics as research_forensics_router
from apps.api.routers import research_evidence_registry as research_evidence_registry_router
from apps.api.routers import research_validity as research_validity_router
from apps.api.routers import research_replication as research_replication_router
from apps.api.routers import research_generalization as research_generalization_router
from apps.api.routers import research_knowledge_state as research_knowledge_state_router
from apps.api.routers import timeline as timeline_router
from apps.api.routers import transit as transit_router
# Imported for its side effect: registers the /patterns route onto
# transit_router.router (see routers/transit_patterns.py's docstring).
from apps.api.routers import transit_patterns as transit_patterns_router  # noqa: F401
from apps.api.routers import varshaphal as varshaphal_router
from apps.api.routers import visualization as visualization_router
from apps.api.routers import workflow as workflow_router
from apps.api.routers import ws as ws_router
from apps.api.routers import yoga as yoga_router
from apps.api.schemas.auth import HealthResponse
from apps.api.schemas.ephemeris import EphemerisStatusSchema
from apps.api.services.ephemeris_service import EphemerisService
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.geocoding_service import GeocodingService
from apps.api.services.research_middleware import research_mode_logging_middleware

logger = logging.getLogger(__name__)
_settings = get_settings()


def _make_ephemeris_service() -> EphemerisService:
    return EphemerisService(_settings.EPHEMERIS_PATH)


def _make_ephemeris_wrapper() -> EphemerisWrapper:
    """
    Build the single, process-wide EphemerisWrapper instance.

    This MUST be created exactly once and shared via app.state — see the
    thread-safety note on EphemerisWrapper itself. Routers must never
    construct their own EphemerisWrapper; they depend on
    `apps.api.dependencies.get_ephemeris_wrapper` instead.
    """
    return EphemerisWrapper(
        ephemeris_path=_settings.EPHEMERIS_PATH,
        ayanamsa="lahiri",
        node_type=_settings.NODE_TYPE,
    )


def _make_worker_pool_manager():
    """
    Build the single, process-wide WorkerPoolManager instance (Phase II.4).

    Same rationale as _make_ephemeris_wrapper: pool executors and their
    dispatcher/autoscaler threads must exist exactly once per process, not
    be recreated per request.
    """
    from apps.api.services.worker_pool import WorkerPoolManager

    return WorkerPoolManager(
        cpu_range=(_settings.WORKER_CPU_MIN, _settings.WORKER_CPU_MAX),
        io_range=(_settings.WORKER_IO_MIN, _settings.WORKER_IO_MAX),
        ai_range=(_settings.WORKER_AI_MIN, _settings.WORKER_AI_MAX),
        autoscale_interval=_settings.WORKER_AUTOSCALE_INTERVAL_SECONDS,
        job_ttl_seconds=_settings.WORKER_JOB_TTL_SECONDS,
    )


def _make_geocoding_service(http_client: httpx.AsyncClient) -> GeocodingService:
    """
    Build the single, process-wide GeocodingService instance — see the
    same rationale as _make_ephemeris_wrapper: TimezoneFinder()'s
    bundled spatial index is expensive to construct, and the
    httpx.AsyncClient's connection pool should be shared, not
    reopened per request.
    """
    return GeocodingService(
        provider_url=_settings.GEOCODING_PROVIDER_URL,
        user_agent=_settings.GEOCODING_USER_AGENT,
        http_client=http_client,
        timezone_finder=TimezoneFinder(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle hooks."""
    logger.info(
        "AstroOS API starting",
        extra={"environment": _settings.ENVIRONMENT, "version": _settings.APP_VERSION},
    )

    # Initialise Swiss Ephemeris once and store in app state so the DI layer
    # can retrieve it without re-creating it on every request.
    ephe_svc: EphemerisService = _make_ephemeris_service()
    ephe_svc.initialize()
    app.state.ephemeris_service = ephe_svc

    # Single shared EphemerisWrapper for the whole process — see the
    # thread-safety note on EphemerisWrapper for why this must not be
    # re-created per request.
    app.state.ephemeris_wrapper = _make_ephemeris_wrapper()

    # Single shared httpx client + GeocodingService for the whole process.
    #
    # verify=truststore.SSLContext(...) makes outbound HTTPS calls trust
    # the OS-native certificate store instead of the certifi bundle
    # Python normally uses. This matters concretely on this machine:
    # local antivirus software (Avast) performs HTTPS-scanning by MITM-ing
    # TLS connections with its own injected root CA, which Windows (and
    # therefore browsers) already trusts but certifi's bundled public-CA
    # list does not — every outbound call otherwise fails with
    # CERTIFICATE_VERIFY_FAILED. truststore is the standard, secure fix
    # (verification still happens, just against the OS trust store) —
    # not a `verify=False` workaround.
    ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    http_client = httpx.AsyncClient(verify=ssl_context)
    app.state.http_client = http_client
    app.state.geocoding_service = _make_geocoding_service(http_client)

    # Single shared WorkerPoolManager (cpu/io/ai pools) for batch jobs —
    # Phase II.4, local-first (no Celery/Redis broker/K8s required).
    app.state.worker_pool_manager = _make_worker_pool_manager()

    startup_status = ephe_svc.get_status()
    logger.info(
        "Swiss Ephemeris ready",
        extra={
            "mode": startup_status.mode,
            "official_data": startup_status.official_data,
            "files": startup_status.se1_files,
            "path": startup_status.path,
        },
    )

    yield

    app.state.worker_pool_manager.shutdown()
    ephe_svc.close()
    await http_client.aclose()
    logger.info("AstroOS API shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=_settings.APP_NAME,
        version=_settings.APP_VERSION,
        docs_url="/api/docs" if _settings.DEBUG else None,
        redoc_url="/api/redoc" if _settings.DEBUG else None,
        openapi_url="/api/openapi.json" if _settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.ALLOWED_ORIGINS,
        allow_origin_regex=r"http://localhost:\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting (Phase 10 cleanup, 2026-07-23): setup_rate_limiting()
    # and the `limiter` instance already existed in
    # apps/api/middleware/rate_limit.py but were never wired in anywhere
    # — the retroactive security review flagged POST /workflow/analyze
    # (the CPU-expensive full pipeline: D1 + 22 vargas + dasha + yogas +
    # shadbala + ashtakavarga + transits + rules, all per request) as
    # reachable with zero throttling by any authenticated user. This
    # activates the global per-remote-address default (100/hour,
    # 10/minute — see rate_limit.py); /workflow/analyze additionally
    # carries its own stricter decorator-based limit (see
    # routers/workflow.py) since it's the one endpoint expensive enough
    # to matter most.
    from slowapi.errors import RateLimitExceeded
    from slowapi import _rate_limit_exceeded_handler
    from apps.api.middleware.rate_limit import setup_rate_limiting

    setup_rate_limiting(app)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Research mode logging middleware (logs queries when research mode is on)
    app.middleware("http")(research_mode_logging_middleware)

    # Observability (Phase II.2): correlation IDs, request metrics, tracing.
    # Registered last so it wraps all other middleware (outermost).
    from apps.api.observability import (
        observability_middleware,
        setup_structured_logging,
    )

    setup_structured_logging()
    app.middleware("http")(observability_middleware)

    # ── Global exception handler ──────────────────────────────────────────────

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred."},
        )
        # A handler registered for the base `Exception` class runs inside
        # Starlette's ServerErrorMiddleware, which sits OUTSIDE CORSMiddleware
        # — so this response never passes back through CORS's header
        # injection. Without this, every unhandled 500 looks like a network
        # failure to the browser (CORS-blocked) instead of a real error.
        origin = request.headers.get("origin")
        if origin and (origin in _settings.ALLOWED_ORIGINS or re.fullmatch(r"http://localhost:\d+", origin)):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        return response

    # ── Routers ───────────────────────────────────────────────────────────────

    # Auth itself stays ungated (register/login/refresh are necessarily
    # public; /me and /logout already extract+verify their own token).
    app.include_router(auth.router, prefix="/api/v1")

    # Authenticated (any role) — core chart-computation and user-facing
    # product surface. Gated here, once, at the router level rather than
    # annotating every individual endpoint function.
    _authenticated = [Depends(require_authenticated)]
    app.include_router(
        search_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        horoscope_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        jaimini_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        divisional_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        dasha_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        events_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        event_analysis_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        ashtakavarga_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        shadbala_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        avastha_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        vimsopaka_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        yoga_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    # transit_patterns_router registers its /patterns route onto
    # transit_router's own router object (see routers/transit_patterns.py) —
    # importing it above is what wires the route in; only one include_router
    # call is needed for both files' routes.
    app.include_router(
        transit_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        sbc_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        tarabala_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        technique_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        custom_techniques_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        prediction_orchestration_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        timeline_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        visualization_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        report_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        report_full_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        export_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(ai_router.router, prefix="/api/v1", dependencies=_authenticated)
    app.include_router(
        ai_phase_e_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        ai_settings_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        workflow_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        kp_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        benchmark_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        governance_router.router, dependencies=_authenticated
    )
    app.include_router(
        continuous_monitoring_router.router, dependencies=_authenticated
    )
    app.include_router(
        intelligence_router.router, dependencies=_authenticated
    )
    app.include_router(
        geocoding_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        muhurta_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        prashna_router.router, prefix="/api/v1"
    )
    app.include_router(
        calendar_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        varshaphal_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(batch_router.router, dependencies=_authenticated)
    app.include_router(jobs_router.router, dependencies=_authenticated)

    # Knowledge: mixed — public reads (search/list/get), researcher-gated
    # writes (create/update/delete). Gated per-endpoint inside
    # routers/knowledge.py instead of here; no router-level dependency.
    app.include_router(knowledge_router.router, prefix="/api/v1")

    # Knowledge Graph: public reads over the ontology (entities, relationships).
    # The ontology is built from in-memory constants at first call; no DB needed.
    app.include_router(knowledge_graph_router.router, prefix="/api/v1")

    # Researcher or Admin — Research Data Office / Statistics surface.
    _researcher = [Depends(require_researcher)]
    app.include_router(
        research_router.router, prefix="/api/v1", dependencies=_researcher
    )
    app.include_router(
        research_calibration_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(research_reproducibility_router.router)
    app.include_router(decision_synthesis_router.router)
    app.include_router(research_knowledge_graph_router.router)
    app.include_router(decision_action_router.router)
    app.include_router(portfolio_planner_router.router)
    app.include_router(longitudinal_tracking_router.router)
    app.include_router(adaptive_research_router.router)
    app.include_router(benchmark_expansion_router.router)
    app.include_router(research_publication_router.router)
    app.include_router(research_forensics_router.router)
    app.include_router(research_evidence_registry_router.router)
    app.include_router(research_validity_router.router)
    app.include_router(research_replication_router.router)
    app.include_router(research_generalization_router.router)
    app.include_router(research_knowledge_state_router.router)
    app.include_router(
        benchmark_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        digital_twin_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        research_tools_router.router, prefix="/api/v1", dependencies=_researcher
    )
    app.include_router(
        guru_research_router.router, prefix="/api/v1", dependencies=_authenticated
    )
    app.include_router(
        statistics_router.router, prefix="/api/v1", dependencies=_researcher
    )

    # Admin Auth (public — login, me, logout)
    app.include_router(
        admin_auth_router.router, prefix="/api/v1"
    )

    # Admin only (management routes) — uses HS256 admin token verification.
    from apps.api.routers.admin_auth import require_admin_token
    app.include_router(
        admin_router.router, prefix="/api/v1", dependencies=[Depends(require_admin_token)]
    )

    # Dataset import — gated with require_researcher (was previously
    # ungated, flagged in ASTROOS_V2_STATUS.md's Phase A objective 4 notes).
    # Import/validate are research-level operations; status/report/schema/
    # template reads are also researcher-gated since they expose dataset
    # metadata and structure.
    app.include_router(
        dataset_import_router.router, dependencies=_researcher
    )
    app.include_router(datasets_router.router)

    # ── Collaboration (RTCollab WebSocket + mDNS session discovery) ───────────
    # Off by default (ENABLE_RTCOLLAB=false) per ASTROOS_PHASE_IV_V2_4_ROADMAP.md
    # §IV.2's success criterion — the router isn't even mounted unless opted in.
    if _settings.ENABLE_RTCOLLAB:
        app.include_router(ws_router.router, prefix="/ws")
        app.include_router(
            collab_router.router, prefix="/api/v1", dependencies=_authenticated
        )

    # ── Monitoring ────────────────────────────────────────────────────────────

    from apps.api.monitoring import setup_monitoring_routes

    setup_monitoring_routes(app)

    # ── Health ────────────────────────────────────────────────────────────────

    @app.get("/api/healthz", response_model=HealthResponse, tags=["System"])
    async def health(request: Request) -> HealthResponse:
        ephe_svc: EphemerisService = request.app.state.ephemeris_service
        ephe_status = ephe_svc.get_status()

        return HealthResponse(
            status="ok",
            version=_settings.APP_VERSION,
            environment=_settings.ENVIRONMENT,
            ephemeris=EphemerisStatusSchema(
                mode=ephe_status.mode,
                official_data=ephe_status.official_data,
                path=ephe_status.path,
                se1_files=ephe_status.se1_files,
                test_longitude=ephe_status.test_longitude,
                error=ephe_status.error,
            ),
        )

    return app


app = create_app()
