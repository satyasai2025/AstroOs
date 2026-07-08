"""
AstroOS API — Application Entry Point

Creates the FastAPI application using the factory pattern.
No global mutable state at module level (except app itself).
Configuration is dependency-injected where needed.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.config import get_settings
from apps.api.routers import auth
from apps.api.routers import horoscope as horoscope_router
from apps.api.schemas.auth import HealthResponse
from apps.api.schemas.ephemeris import EphemerisStatusSchema
from apps.api.services.ephemeris_service import EphemerisService

logger = logging.getLogger(__name__)
_settings = get_settings()


def _make_ephemeris_service() -> EphemerisService:
    return EphemerisService(_settings.EPHEMERIS_PATH)


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

    ephe_svc.close()
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
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handler ──────────────────────────────────────────────

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred."},
        )

    # ── Routers ───────────────────────────────────────────────────────────────

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(horoscope_router.router, prefix="/api/v1")

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
