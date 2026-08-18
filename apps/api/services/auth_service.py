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
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jose import JWTError

from apps.api.config import get_settings
from apps.api.domain.user import User, UserId
from apps.api.repositories.user_repository import UserRepository
from apps.api.security import jwt as jwt_module
from apps.api.security.password import hash_password, verify_password
from apps.api.security.tokens import generate_reset_token, hash_reset_token
from apps.api.services.dtos import AuthResultDTO, AuthTokensDTO, UserDTO
from apps.api.services.email_service import send_password_reset_email

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
    """Raised when a registration failure occurs."""
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
        timezone=user.timezone,
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

    # ── Password reset ───────────────────────────────────────────────────────

    async def request_password_reset(self, email: str) -> None:
        """
        Generate and email a reset link if *email* belongs to an account.

        Always returns normally regardless of whether the account exists —
        the router responds with the same generic message either way, so
        this can't be used to enumerate registered emails.
        """
        user = await self._user_repo.get_by_email(email)
        if not user:
            return

        token = generate_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=_settings.PASSWORD_RESET_TOKEN_TTL_MINUTES
        )
        await self._user_repo.create_reset_token(
            user_id=user.id,
            token_hash=hash_reset_token(token),
            expires_at=expires_at,
        )

        reset_link = f"{_settings.FRONTEND_URL}/reset-password?token={token}"
        await send_password_reset_email(user.email, reset_link)

    async def reset_password(self, token: str, new_password: str) -> None:
        user_id_value = await self._user_repo.consume_reset_token(
            hash_reset_token(token)
        )
        if user_id_value is None:
            raise AuthError("Invalid or expired reset link.", status_code=400)

        user_id = UserId(user_id_value)
        await self._user_repo.update_password(user_id, hash_password(new_password))
        # Force re-login everywhere — a leaked refresh token from before the
        # reset must not still work afterward.
        await self._user_repo.revoke_all_sessions(user_id)

    # ── Current User ──────────────────────────────────────────────────────────

    async def update_profile(
        self,
        user: User,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> User:
        """
        Update the authenticated user's own profile fields.

        Raises AuthError(409) if the requested email is already taken by a
        different account, or AuthError(422) if timezone isn't a real IANA
        zone name (e.g. a typo like "Asia/Kolkota").
        """
        if email is not None and email.strip().lower() != user.email:
            existing = await self._user_repo.get_by_email(email)
            if existing is not None and existing.id != user.id:
                raise AuthError(
                    f"An account with email '{email}' already exists.",
                    status_code=409,
                )

        if timezone is not None:
            try:
                ZoneInfo(timezone)
            except ZoneInfoNotFoundError:
                raise AuthError(
                    f"'{timezone}' is not a recognized timezone.",
                    status_code=422,
                )

        updated = await self._user_repo.update_profile(
            user.id,
            display_name=display_name,
            email=email,
            timezone=timezone,
        )
        if updated is None:
            raise AuthError("User not found.", status_code=404)
        return updated

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Verify the current password and set a new one.

        On success, revokes all existing sessions so the user must sign in
        again with the new password.
        """
        try:
            password_ok = verify_password(current_password, user.hashed_password)
        except Exception:
            # passlib can raise on malformed hashes (e.g. legacy algorithms).
            password_ok = False

        if not password_ok:
            raise AuthError("Current password is incorrect.", status_code=400)

        await self._user_repo.update_password(user.id, hash_password(new_password))
        await self._user_repo.revoke_all_sessions(user.id)

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

    async def delete_account(self, user: User) -> None:
        """
        Soft delete the user and revoke all active sessions.
        """
        await self._user_repo.revoke_all_sessions(user.id)
        deleted = await self._user_repo.soft_delete(user.id)
        if not deleted:
            raise AuthError("User not found or already deleted.", status_code=404)

