"""
AstroOS — Auth Service

All authentication business logic lives here.
No HTTP concepts (Request/Response) leak into this layer.
No Pydantic schemas leak into this layer — only domain objects and DTOs.
No ORM models leak into this layer.

Fix log (post code-review):
  - Dummy hash replaced with a precomputed valid sentinel (prevents 500 on unknown email).
  - verify_password wrapped in try/except (passlib can raise on malformed hashes).
  - PermissionError from domain mapped to AuthError(403) at service boundary.
  - Refresh revocation now checks the atomic return value (replay-race guard).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError

from apps.api.config import get_settings
from apps.api.domain.user import User, UserId
from apps.api.repositories.user_repository import UserRepository
from apps.api.security import jwt as jwt_module
from apps.api.security.password import hash_password, verify_password
from apps.api.services.dtos import AuthResultDTO, AuthTokensDTO, UserDTO

_settings = get_settings()

# Precomputed at import time — a valid bcrypt hash of a sentinel string that
# will never match any real user input. Used to keep login timing constant when
# the requested email does not exist in the database.
# Sentinel is kept under 72 bytes (bcrypt's hard limit).
_DUMMY_HASH: str = hash_password("_astros_sentinel_")


class AuthError(Exception):
    """
    Raised for expected auth failures.
    Carries an HTTP status code so routers can map it without business logic.
    """

    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RegistrationError(AuthError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


def _assert_can_auth(user: User) -> None:
    """
    Assert the user is allowed to receive tokens.
    Maps domain PermissionError → AuthError so routers never see a 500.
    """
    try:
        user.assert_can_authenticate()
    except PermissionError as exc:
        raise AuthError(str(exc), status_code=403) from exc


def _build_token_pair(user: User) -> tuple[AuthTokensDTO, str]:
    """
    Create access + refresh tokens for *user*.
    Returns (AuthTokensDTO, refresh_jti).
    """
    access_token, _ = jwt_module.create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )
    refresh_token, refresh_jti = jwt_module.create_refresh_token(
        subject=str(user.id),
    )
    return (
        AuthTokensDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        refresh_jti,
    )


def _user_dto(user: User) -> UserDTO:
    return UserDTO(
        id=user.id.value,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        status=user.status.value,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


class AuthService:
    """
    Stateless authentication service.

    Depends on UserRepository for DB access and an optional Redis client
    for the JWT denylist. Both are injected; neither is imported globally.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        redis_client=None,  # redis.asyncio.Redis | None
    ) -> None:
        self._user_repo = user_repo
        self._redis = redis_client

    # ── Registration ──────────────────────────────────────────────────────────

    async def register(
        self,
        email: str,
        display_name: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuthResultDTO:
        if await self._user_repo.email_exists(email):
            raise RegistrationError(
                f"An account with email '{email}' already exists."
            )

        hashed = hash_password(password)
        user = await self._user_repo.create(
            email=email,
            display_name=display_name,
            hashed_password=hashed,
        )

        tokens, refresh_jti = _build_token_pair(user)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=_settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self._user_repo.create_session(
            user_id=user.id,
            refresh_token_jti=refresh_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return AuthResultDTO(user=_user_dto(user), tokens=tokens)

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuthResultDTO:
        user = await self._user_repo.get_by_email(email)

        # Always run bcrypt even when the email does not exist.
        # This keeps timing constant and prevents user-enumeration via timing.
        actual_hash = user.hashed_password if user else _DUMMY_HASH
        try:
            password_ok = verify_password(password, actual_hash)
        except Exception:
            # passlib can raise on malformed hashes (e.g. legacy algorithms).
            # Treat as incorrect password, never expose internals.
            password_ok = False

        if not user or not password_ok:
            raise AuthError("Invalid email or password.")

        _assert_can_auth(user)

        now = datetime.now(timezone.utc)
        await self._user_repo.update_last_login(user.id, now)

        tokens, refresh_jti = _build_token_pair(user)
        expires_at = now + timedelta(days=_settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._user_repo.create_session(
            user_id=user.id,
            refresh_token_jti=refresh_jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return AuthResultDTO(user=_user_dto(user), tokens=tokens)

    # ── Refresh ───────────────────────────────────────────────────────────────

    async def refresh_tokens(self, refresh_token: str) -> AuthTokensDTO:
        try:
            payload = jwt_module.decode_refresh_token(refresh_token)
        except JWTError as exc:
            raise AuthError(f"Invalid refresh token: {exc}") from exc

        jti: str = payload["jti"]
        subject: str = payload["sub"]

        # Check Redis denylist first (fast path)
        if self._redis and await self._redis.get(f"denylist:{jti}"):
            raise AuthError("Refresh token has been revoked.")

        # Atomic single-use consumption: conditional UPDATE WHERE revoked_at IS NULL.
        # Returns True only if this specific call performed the revocation.
        # Concurrent callers with the same token will get False → replay rejected.
        revoked = await self._user_repo.revoke_session_by_jti(jti)
        if not revoked:
            # Either already revoked or never existed — both are invalid.
            raise AuthError("Refresh token is invalid or has already been used.")

        # Denylist the old JTI in Redis so in-flight access tokens derived from
        # it can be cut off if needed (belt-and-suspenders with the DB revocation).
        if self._redis:
            ttl = _settings.REDIS_TOKEN_DENYLIST_TTL
            await self._redis.setex(f"denylist:{jti}", ttl, "1")

        from uuid import UUID as _UUID
        user = await self._user_repo.get_by_id(UserId(_UUID(subject)))
        if not user:
            raise AuthError("User not found.")
        _assert_can_auth(user)

        tokens, new_jti = _build_token_pair(user)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=_settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self._user_repo.create_session(
            user_id=user.id,
            refresh_token_jti=new_jti,
            expires_at=expires_at,
        )
        return tokens

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(self, access_token: str) -> None:
        try:
            payload = jwt_module.decode_access_token(access_token)
        except JWTError:
            return  # silently ignore invalid tokens on logout

        jti: str = payload.get("jti", "")
        if jti and self._redis:
            ttl = _settings.REDIS_TOKEN_DENYLIST_TTL
            await self._redis.setex(f"denylist:{jti}", ttl, "1")

    # ── Current User ──────────────────────────────────────────────────────────

    async def get_current_user(self, access_token: str) -> User:
        try:
            payload = jwt_module.decode_access_token(access_token)
        except JWTError as exc:
            raise AuthError(f"Invalid token: {exc}") from exc

        jti: str = payload.get("jti", "")
        if self._redis and await self._redis.get(f"denylist:{jti}"):
            raise AuthError("Token has been revoked.")

        user_id_str: str = payload["sub"]
        try:
            from uuid import UUID as _UUID
            user_id = UserId(_UUID(user_id_str))
        except (ValueError, AttributeError) as exc:
            raise AuthError("Malformed token subject.") from exc

        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise AuthError("User not found.")

        return user
