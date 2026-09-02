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
from apps.api.domain.user import User, UserId, UserRole, UserStatus

from apps.api.repositories.ai_settings_repository import AISettingsRepository
from apps.api.repositories.dataset_repository import DatasetRepository
from apps.api.repositories.event_repository import EventRepository
from apps.api.repositories.knowledge_repository import KnowledgeRepository
from apps.api.repositories.user_repository import UserRepository
from apps.api.services.ai_settings_service import AISettingsService
from apps.api.services.auth_service import AuthError, AuthService
from apps.api.services.dataset_service import DatasetService
from apps.api.services.ephemeris_service import EphemerisService
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.entitlement_service import EntitlementService
from apps.api.services.feature_catalog import ACTION_COLUMNS, DECIDED_MATRIX
from apps.api.services.knowledge_engine import KnowledgeEngine

# Features whose Feature x Plan x Action cells are governed by the Phase 2
# entitlement matrix (i.e., the matrix has made at least one decision for
# them). For governed features an absent plan_features row is a product
# decision — "this plan does not include the feature" — and enforcement
# denies rather than falling back to the unresolved-allow shim.
GOVERNED_FEATURES = frozenset(DECIDED_MATRIX.keys())

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
    pool_pre_ping=True,
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
    # Empty REDIS_URL → skip Redis entirely and use in-memory fallback.
    _redis_pool = aioredis.ConnectionPool.from_url(
        _settings.REDIS_URL or "redis://localhost:6379/0",
        decode_responses=True,
        max_connections=20,
        socket_connect_timeout=1,  # fail fast if Redis is unreachable
    )
except Exception:
    _redis_pool = None


class _InMemoryRedis:
    """
    Minimal Redis-compatible in-memory store.

    Used when real Redis is unreachable. Supports get/setex which are the
    only operations the auth service needs for the JWT denylist.
    Entries expire lazily on access (TTL matches real Redis semantics).
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[str | None, float | None]] = {}

    async def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and expires_at <= __import__("time").time():
            self._store.pop(key, None)
            return None
        return value

    async def setex(self, key: str, time_secs: int, value: str) -> bool:
        import time as _time
        self._store[key] = (value, _time.time() + time_secs)
        return True

    async def ping(self) -> bool:
        return True


async def get_redis() -> aioredis.Redis | _InMemoryRedis | None:
    """
    Return a cache client for JWT denylist.

    - Real Redis when reachable.
    - In-memory fallback when Redis is not configured / unreachable.
      Denylist works per-process; restarting the API clears it (acceptable
      for local dev — security is unaffected since denylist is in-memory
      on the real Redis anyway).
    - None only if initialization itself failed (defensive).
    """
    if _redis_pool is None:
        return _InMemoryRedis()
    try:
        client = aioredis.Redis(connection_pool=_redis_pool)
        await client.ping()
        return client
    except Exception:
        return _InMemoryRedis()


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


async def get_ai_settings_repo(
    session: AsyncSession = Depends(get_db_session),
) -> AISettingsRepository:
    return AISettingsRepository(session)


async def get_ai_settings_service(
    repo: AISettingsRepository = Depends(get_ai_settings_repo),
) -> AISettingsService:
    return AISettingsService(repo, _settings)


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
#
# DEV_BYPASS_AUTH=true  → skips all token verification in local development.
# This env var is NEVER set in production; it is checked at runtime so there
# is zero overhead in prod even if the code path exists.

import os as _os
from datetime import datetime as _datetime
from uuid import UUID as _UUID


def _dev_user() -> "User":
    """Return a synthetic admin user for local dev when DEV_BYPASS_AUTH=true."""
    return User(
        id=UserId(value=_UUID("00000000-0000-0000-0000-000000000001")),
        email="dev@astroos.local",
        display_name="Dev User",
        hashed_password="",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        created_at=_datetime(2024, 1, 1),
        updated_at=_datetime(2024, 1, 1),
    )


async def get_current_user_from_bearer(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    # ── Local development auth bypass ────────────────────────────────────────
    if _os.environ.get("DEV_BYPASS_AUTH", "").lower() == "true":
        return _dev_user()

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


# ── Plan-based entitlement enforcement (Phase 3) ─────────────────────────────
#
# require_entitlement(feature_key, action) is the server-side gate that turns
# the Phase 2 entitlement matrix into actual API enforcement:
#
#     Authenticated User → Assigned Plan → Feature → Action → ALLOW / DENY
#
# Distinction from the role guards above (deliberate, do not conflate):
#   ROLE  (require_role / require_admin) = administrative/security authority.
#   PLAN  (require_entitlement)          = product entitlement for customer
#                                          features. An ADMIN role does NOT
#                                          bypass plan entitlements — admins
#                                          resolve to their assigned plan like
#                                          any user (FREE when unassigned),
#                                          because the existing architecture
#                                          defines no admin bypass.
#
# Denial responses use HTTP 403 with a structured `detail` dict so clients can
# distinguish the failure kinds programmatically:
#
#   {"code": "FEATURE_NOT_AVAILABLE", ...}  feature not part of user's plan
#   {"code": "ACTION_NOT_ALLOWED",   ...}  feature on plan, action not granted
#
# (UNAUTHENTICATED stays a plain 401 from get_current_user_from_bearer; role
# failures stay plain-string 403s from require_role — both unchanged.)
#
# Governed-feature strictness: features listed in the Phase 2 DECIDED_MATRIX
# are fully governed by the matrix. For those, an entitlement row ABSENT for
# the caller's plan is a product decision ("this plan doesn't include the
# feature") and denies with FEATURE_NOT_AVAILABLE — the Phase 2
# unresolved-fallback shim must NOT let such callers through (e.g. FREE ×
# research_projects seeds no row precisely because Free has no research
# access). Features outside the matrix remain governed by the compatibility
# fallback, preserving current behaviour until their cells are decided.


def _denial(code: str, message: str, feature_key: str, action: str, plan_code: str) -> HTTPException:
    """Build the canonical 403 response for an entitlement denial."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": code,
            "message": message,
            "feature": feature_key,
            "action": action,
            "plan": plan_code,
        },
    )


def require_entitlement(feature_key: str, action: str):
    """
    Dependency factory enforcing one Feature x Plan x Action cell of the
    Phase 2 entitlement matrix.

    Usage (route-level, alongside existing role guards):

        @router.post("/projects", dependencies=[
            Depends(require_entitlement("research_projects", "create")),
        ])
        async def create_project(...): ...

    Resolution order per request:
        1. Authentication        — via get_current_user_from_bearer (401).
        2. Plan resolution       — EntitlementService.resolve_user_plan
                                   (explicit assignment, else FREE default).
        3. Entitlement decision  — EntitlementService.get_decision.
        4. Zero-limit guard      — creation also denied when the plan's
                                   numeric limit for the feature is 0
                                   (research_projects on FREE), WITHOUT
                                   consuming any quota (consumption is a
                                   later phase).
        5. ALLOW (returns the User) or 403 FEATURE_NOT_AVAILABLE /
           ACTION_NOT_ALLOWED as described above.

    Raises ValueError at wiring time for an unknown action — misconfigured
    routes fail fast at import instead of at request time.
    """
    if action not in ACTION_COLUMNS:
        raise ValueError(
            f"Unknown entitlement action '{action}'. "
            f"Valid actions: {', '.join(ACTION_COLUMNS)}."
        )

    async def _check_entitlement(
        current_user: User = Depends(get_current_user_from_bearer),
        db: AsyncSession = Depends(get_db_session),
    ) -> User:
        svc = EntitlementService(db)
        plan = await svc.resolve_user_plan(current_user)
        plan_code = plan.plan_code

        decision = await svc.get_decision(current_user, feature_key, action)

        if decision.status == "granted":
            if action == "create" and await svc.creation_blocked_by_zero_limit(
                current_user, feature_key
            ):
                raise _denial(
                    "ACTION_NOT_ALLOWED",
                    f"Your plan ({plan_code}) allows no {feature_key} "
                    f"creations (monthly limit is 0).",
                    feature_key, action, plan_code,
                )
            return current_user

        if decision.status == "denied":
            raise _denial(
                "ACTION_NOT_ALLOWED",
                f"Your plan ({plan_code}) does not allow '{action}' on "
                f"'{feature_key}'.",
                feature_key, action, plan_code,
            )

        # status == "unresolved"
        if feature_key in GOVERNED_FEATURES or not decision.fallback_allowed:
            raise _denial(
                "FEATURE_NOT_AVAILABLE",
                f"'{feature_key}' is not part of your plan ({plan_code}).",
                feature_key, action, plan_code,
            )
        # Undecided feature + compatibility fallback allows it: legacy pass.
        return current_user

    return _check_entitlement
