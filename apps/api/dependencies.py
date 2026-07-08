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
from apps.api.domain.user import User
from apps.api.repositories.user_repository import UserRepository
from apps.api.services.auth_service import AuthError, AuthService
from apps.api.services.ephemeris_service import EphemerisService

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


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    redis: aioredis.Redis | None = Depends(get_redis),
) -> AuthService:
    return AuthService(user_repo=user_repo, redis_client=redis)


# ── Auth Guard ────────────────────────────────────────────────────────────────


async def get_ephemeris_service(request: Request) -> EphemerisService:
    """
    Return the EphemerisService singleton stored in app state during lifespan.
    Injecting via app.state avoids re-initialising the C library per request.
    """
    return request.app.state.ephemeris_service


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
