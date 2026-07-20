"""
AstroOS — Dependency Injection

FastAPI's DI system wires database sessions, Redis connections, and
service instances to route handlers. Nothing is instantiated globally
at module import time (except the engine, which is cheap).

Dependency graph:
  get_db_session → get_user_repo → get_auth_service → routes
  get_redis      ↗
"""

from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fastapi import Request as _Request

from apps.api.config import Settings, get_settings
from apps.api.domain.user import User, UserRole
from apps.api.repositories.dataset_repository import DatasetRepository
from apps.api.repositories.event_repository import EventRepository
from apps.api.repositories.knowledge_repository import KnowledgeRepository
from apps.api.repositories.user_repository import UserRepository
from apps.api.services.auth_service import AuthError, AuthService
from apps.api.services.dataset_service import DatasetService
from apps.api.services.ephemeris_service import EphemerisService
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.knowledge_engine import KnowledgeEngine

_settings: Settings = get_settings()

# ── Database ──────────────────────────────────────────────────────────────────

from urllib.parse import urlencode, urlparse, parse_qs, urlunparse


def _build_async_engine_args(raw_url: str) -> tuple[str, dict]:
    """
    Convert a sync PostgreSQL URL to asyncpg format.

    asyncpg does not accept URL query parameters for SSL/sslmode — it uses
    driver-level connect_args instead. This function:
      1. Rewrites the scheme to postgresql+asyncpg.
      2. Extracts 'sslmode' from the query string and maps it to ssl= bool.
      3. Returns (clean_url, connect_args) ready for create_async_engine().
    """
    parsed = urlparse(raw_url)

    # Rewrite scheme
    scheme = parsed.scheme
    if scheme in ("postgresql", "postgres"):
        scheme = "postgresql+asyncpg"
    elif scheme == "postgresql+psycopg2":
        scheme = "postgresql+asyncpg"

    # Parse and mutate query string
    qs = parse_qs(parsed.query, keep_blank_values=True)
    sslmode = qs.pop("sslmode", [None])[0]  # remove sslmode from URL

    # Rebuild clean URL without sslmode
    new_query = urlencode({k: v[0] for k, v in qs.items()})
    clean = urlunparse((scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    # Map sslmode → asyncpg ssl flag
    connect_args: dict = {}
    if sslmode in (None, "disable", "allow", "prefer"):
        connect_args["ssl"] = False
    else:
        # "require", "verify-ca", "verify-full" → use system SSL context
        import ssl as _ssl
        connect_args["ssl"] = _ssl.create_default_context()

    return clean, connect_args


_async_url, _connect_args = _build_async_engine_args(_settings.DATABASE_URL)

_engine = create_async_engine(
    _async_url,
    echo=_settings.DB_ECHO_SQL,
    pool_size=_settings.DB_POOL_SIZE,
    max_overflow=_settings.DB_MAX_OVERFLOW,
    pool_timeout=_settings.DB_POOL_TIMEOUT,
    pool_recycle=_settings.DB_POOL_RECYCLE,
    connect_args=_connect_args,
)

_async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional DB session; commit on success, rollback on error."""
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Redis ─────────────────────────────────────────────────────────────────────

_redis_pool: aioredis.ConnectionPool | None = None

try:
    _redis_pool = aioredis.ConnectionPool.from_url(
        _settings.REDIS_URL,
        decode_responses=True,
        max_connections=20,
        socket_connect_timeout=1,  # fail fast if Redis is unreachable
    )
except Exception:
    _redis_pool = None


async def get_redis() -> aioredis.Redis | None:
    """
    Return a Redis client, or None if Redis is not configured / unreachable.

    The service layer handles None gracefully: JWT denylist is skipped but
    all other auth flows remain fully functional.
    """
    if _redis_pool is None:
        return None
    try:
        client = aioredis.Redis(connection_pool=_redis_pool)
        await client.ping()  # fast connectivity check
        return client
    except Exception:
        return None


# ── Repository & Service factories ───────────────────────────────────────────


async def get_user_repo(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session)


async def get_event_repo(
    session: AsyncSession = Depends(get_db_session),
) -> EventRepository:
    return EventRepository(session)


async def get_dataset_repo(
    session: AsyncSession = Depends(get_db_session),
) -> DatasetRepository:
    return DatasetRepository(session)


async def get_dataset_service(
    repo: DatasetRepository = Depends(get_dataset_repo),
) -> DatasetService:
    return DatasetService(repo)


async def get_knowledge_repo(
    session: AsyncSession = Depends(get_db_session),
) -> KnowledgeRepository:
    return KnowledgeRepository(session)


async def get_knowledge_engine(
    repo: KnowledgeRepository = Depends(get_knowledge_repo),
) -> KnowledgeEngine:
    return KnowledgeEngine(repo)


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    redis: aioredis.Redis | None = Depends(get_redis),
) -> AuthService:
    return AuthService(user_repo=user_repo, redis_client=redis)


# ── Knowledge Graph singleton (Phase D) ────────────────────────────────────

_graph_engine = None


def get_knowledge_graph_engine():
    """
    Return the process-wide KnowledgeGraphEngine singleton.

    Built lazily on first call; subsequent calls return the cached instance.
    The underlying OntologyRegistry is built from in-memory constants
    (packages/shared/constants.py + yoga definitions) — no DB or external
    service required.
    """
    global _graph_engine
    if _graph_engine is None:
        from apps.api.services.knowledge_graph_engine import KnowledgeGraphEngine
        from apps.api.services.ontology_registry import build_default_ontology

        _graph_engine = KnowledgeGraphEngine(build_default_ontology())
    return _graph_engine


# ── Auth Guard ────────────────────────────────────────────────────────────────


async def get_ephemeris_service(request: Request) -> EphemerisService:
    """
    Return the EphemerisService singleton stored in app state during lifespan.
    Injecting via app.state avoids re-initialising the C library per request.
    """
    return request.app.state.ephemeris_service


async def get_ephemeris_wrapper(request: Request) -> EphemerisWrapper:
    """
    Return the single process-wide EphemerisWrapper instance created during
    lifespan startup (see apps.api.main._make_ephemeris_wrapper).

    Routers (horoscope, divisional, dasha) MUST depend on this instead of
    constructing their own EphemerisWrapper. pyswisseph holds process-global
    state, and EphemerisWrapper.calculate() is internally lock-protected on
    the assumption that exactly one instance exists per process — creating
    a second instance does not provide request isolation, it just adds a
    second, uncoordinated lock guarding the same global C-library state.
    """
    return request.app.state.ephemeris_wrapper


async def get_worker_pool_manager(request: Request):
    """
    Return the process-wide WorkerPoolManager created during lifespan startup
    (see apps.api.main._make_worker_pool_manager). Owns the cpu/io/ai pools
    used by the batch job API (Phase II.4) — one instance per process, same
    rationale as the EphemerisWrapper/GeocodingService singletons above.
    """
    return request.app.state.worker_pool_manager


async def get_geocoding_service(request: Request):
    """
    Return the process-wide GeocodingService instance created during
    lifespan startup (see apps.api.main._make_geocoding_service).

    Constructed once because TimezoneFinder() loads a sizeable bundled
    spatial index at construction time — same "expensive to build,
    stateless per-call after that" shape as EphemerisWrapper — and to
    reuse one httpx.AsyncClient connection pool across requests instead
    of opening a fresh connection to Nominatim per search.
    """
    return request.app.state.geocoding_service


# ── Auth Guard ────────────────────────────────────────────────────────────────


async def get_current_user_from_bearer(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or malformed.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_header.removeprefix("Bearer ").strip()
    try:
        return await auth_service.get_current_user(token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── Role-based access control (v2 Phase A) ────────────────────────────────────
#
# require_role(*roles) is applied at the router level via
# app.include_router(..., dependencies=[Depends(require_authenticated)])
# in main.py — one policy declaration per router, rather than annotating
# every individual endpoint function. Endpoints needing a finer-grained
# split within one router (e.g. knowledge.py's public reads vs
# researcher-only writes) add the dependency directly on those specific
# functions instead.


def require_role(*allowed_roles: UserRole):
    """
    Returns a dependency that accepts only the given roles. Reuses
    get_current_user_from_bearer for the actual token verification —
    this only adds the role check on top, so a bad/missing token still
    surfaces as 401 (via that dependency), and a valid token with the
    wrong role surfaces as 403 here.
    """

    async def _check_role(
        current_user: User = Depends(get_current_user_from_bearer),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This action requires one of: "
                    f"{', '.join(r.value for r in allowed_roles)}."
                ),
            )
        return current_user

    return _check_role


async def require_authenticated(
    current_user: User = Depends(get_current_user_from_bearer),
) -> User:
    """Any authenticated user, regardless of role — the minimum bar for
    every non-public endpoint."""
    return current_user


require_researcher = require_role(UserRole.RESEARCHER, UserRole.ADMIN)
require_admin = require_role(UserRole.ADMIN)
