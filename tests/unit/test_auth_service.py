"""
AstroOS — Auth Service Unit Tests

All I/O is mocked at the repository and JWT boundaries.
No real DB, no real Redis, no real RSA keys required.

Fix log (post code-review):
  - Removed invalid walrus-in-decorator syntax.
  - Added test for unknown-email login (must return AuthError, not 500).
  - Added test for suspended-user login (must return AuthError 403, not 500).
  - Added test for PermissionError → AuthError mapping at service boundary.
  - Added test for refresh-token replay (second call must fail).
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.services.auth_service import (
    AuthError,
    AuthService,
    RegistrationError,
)
from apps.api.services.dtos import AuthResultDTO, AuthTokensDTO
from tests.conftest import make_user

pytestmark = pytest.mark.asyncio

# ── Shared mock tokens ────────────────────────────────────────────────────────

_MOCK_ACCESS = "mock.access.token"
_MOCK_REFRESH = "mock.refresh.token"
_MOCK_JTI_ACCESS = "jti-access-123"
_MOCK_JTI_REFRESH = "jti-refresh-456"

_MOCK_TOKEN_PAIR = (_MOCK_ACCESS, _MOCK_JTI_ACCESS)
_MOCK_REFRESH_PAIR = (_MOCK_REFRESH, _MOCK_JTI_REFRESH)


# ── Helper factories ──────────────────────────────────────────────────────────


def _make_mock_repo(
    user: User | None = None,
    email_exists: bool = False,
    revoke_returns: bool = True,
):
    repo = AsyncMock()
    repo.email_exists = AsyncMock(return_value=email_exists)
    repo.get_by_email = AsyncMock(return_value=user)
    repo.get_by_id = AsyncMock(return_value=user)
    repo.create = AsyncMock(return_value=user or make_user())
    repo.update_last_login = AsyncMock()
    repo.create_session = AsyncMock()
    repo.revoke_session_by_jti = AsyncMock(return_value=revoke_returns)
    repo.get_session_by_jti = AsyncMock(return_value=None)
    return repo


def _make_mock_redis(jti_revoked: bool = False):
    redis = AsyncMock()
    redis.get = AsyncMock(return_value="1" if jti_revoked else None)
    redis.setex = AsyncMock(return_value=True)
    return redis


def _make_service(repo=None, redis=None):
    return AuthService(
        user_repo=repo or _make_mock_repo(),
        redis_client=redis or _make_mock_redis(),
    )


# ── Registration ──────────────────────────────────────────────────────────────


@patch(
    "apps.api.services.auth_service.jwt_module.create_access_token",
    return_value=_MOCK_TOKEN_PAIR,
)
@patch(
    "apps.api.services.auth_service.jwt_module.create_refresh_token",
    return_value=_MOCK_REFRESH_PAIR,
)
@patch("apps.api.services.auth_service.hash_password", return_value="hashed_pw")
async def test_register_success(mock_hash, mock_refresh, mock_access):
    user = make_user(email="new@example.com")
    repo = _make_mock_repo(user=user, email_exists=False)
    service = _make_service(repo=repo)

    result = await service.register(
        email="new@example.com",
        display_name="New User",
        password="SecurePass1",
    )

    assert isinstance(result, AuthResultDTO)
    assert result.user.email == "new@example.com"
    assert result.tokens.access_token == _MOCK_ACCESS
    assert result.tokens.refresh_token == _MOCK_REFRESH
    repo.create.assert_awaited_once()
    repo.create_session.assert_awaited_once()


@patch(
    "apps.api.services.auth_service.jwt_module.create_access_token",
    return_value=_MOCK_TOKEN_PAIR,
)
@patch(
    "apps.api.services.auth_service.jwt_module.create_refresh_token",
    return_value=_MOCK_REFRESH_PAIR,
)
async def test_register_duplicate_email(mock_refresh, mock_access):
    repo = _make_mock_repo(email_exists=True)
    service = _make_service(repo=repo)

    with pytest.raises(RegistrationError) as exc_info:
        await service.register(
            email="exists@example.com",
            display_name="Someone",
            password="SecurePass1",
        )

    assert "already exists" in str(exc_info.value)
    repo.create.assert_not_awaited()


# ── Login ─────────────────────────────────────────────────────────────────────


@patch(
    "apps.api.services.auth_service.jwt_module.create_access_token",
    return_value=_MOCK_TOKEN_PAIR,
)
@patch(
    "apps.api.services.auth_service.jwt_module.create_refresh_token",
    return_value=_MOCK_REFRESH_PAIR,
)
@patch("apps.api.services.auth_service.verify_password", return_value=True)
async def test_login_success(mock_verify, mock_refresh, mock_access):
    user = make_user(email="user@example.com")
    repo = _make_mock_repo(user=user)
    service = _make_service(repo=repo)

    result = await service.login(email="user@example.com", password="CorrectPass1")

    assert isinstance(result, AuthResultDTO)
    assert result.user.email == "user@example.com"
    repo.update_last_login.assert_awaited_once()
    repo.create_session.assert_awaited_once()


@patch("apps.api.services.auth_service.verify_password", return_value=False)
async def test_login_wrong_password(mock_verify):
    user = make_user(email="user@example.com")
    repo = _make_mock_repo(user=user)
    service = _make_service(repo=repo)

    with pytest.raises(AuthError) as exc_info:
        await service.login(email="user@example.com", password="WrongPass1")

    assert "Invalid" in str(exc_info.value)
    assert exc_info.value.status_code == 401


async def test_login_unknown_email_returns_auth_error_not_500():
    """
    REGRESSION: Previously the dummy hash was invalid bcrypt and would cause
    verify_password to raise, surfacing as a 500. Now we use a precomputed
    valid hash and catch exceptions from verify_password.
    """
    repo = _make_mock_repo(user=None)
    service = _make_service(repo=repo)

    # Must raise AuthError (HTTP 401), never an uncaught exception (500).
    with pytest.raises(AuthError) as exc_info:
        await service.login(email="nobody@example.com", password="AnyPass1")

    assert exc_info.value.status_code == 401
    assert "Invalid" in exc_info.value.message


async def test_login_verify_password_exception_returns_auth_error():
    """
    If verify_password raises (malformed hash), service must still return
    AuthError 401, not propagate the exception as a 500.
    """
    user = make_user(email="user@example.com")
    repo = _make_mock_repo(user=user)
    service = _make_service(repo=repo)

    with patch(
        "apps.api.services.auth_service.verify_password",
        side_effect=ValueError("malformed hash"),
    ):
        with pytest.raises(AuthError) as exc_info:
            await service.login(email="user@example.com", password="AnyPass1")

    assert exc_info.value.status_code == 401


@patch(
    "apps.api.services.auth_service.jwt_module.create_access_token",
    return_value=_MOCK_TOKEN_PAIR,
)
@patch(
    "apps.api.services.auth_service.jwt_module.create_refresh_token",
    return_value=_MOCK_REFRESH_PAIR,
)
@patch("apps.api.services.auth_service.verify_password", return_value=True)
async def test_login_suspended_user_returns_403_not_500(
    mock_verify, mock_refresh, mock_access
):
    """
    REGRESSION: PermissionError from assert_can_authenticate() must be caught
    and converted to AuthError(403) at the service boundary, never leak as 500.
    """
    user = make_user(status=UserStatus.SUSPENDED)
    repo = _make_mock_repo(user=user)
    service = _make_service(repo=repo)

    with pytest.raises(AuthError) as exc_info:
        await service.login(email=user.email, password="AnyPass1")

    assert exc_info.value.status_code == 403


# ── Refresh token ─────────────────────────────────────────────────────────────


@patch(
    "apps.api.services.auth_service.jwt_module.decode_refresh_token",
    return_value={"jti": "jti-old", "sub": str(uuid.uuid4()), "type": "refresh"},
)
@patch(
    "apps.api.services.auth_service.jwt_module.create_access_token",
    return_value=_MOCK_TOKEN_PAIR,
)
@patch(
    "apps.api.services.auth_service.jwt_module.create_refresh_token",
    return_value=_MOCK_REFRESH_PAIR,
)
async def test_refresh_tokens_success(mock_new_refresh, mock_new_access, mock_decode):
    user = make_user()
    repo = _make_mock_repo(user=user, revoke_returns=True)
    service = _make_service(repo=repo)

    result = await service.refresh_tokens("old.refresh.token")

    assert isinstance(result, AuthTokensDTO)
    assert result.access_token == _MOCK_ACCESS
    repo.revoke_session_by_jti.assert_awaited_once_with("jti-old")
    repo.create_session.assert_awaited_once()


@patch(
    "apps.api.services.auth_service.jwt_module.decode_refresh_token",
    return_value={"jti": "jti-used", "sub": str(uuid.uuid4()), "type": "refresh"},
)
async def test_refresh_replay_returns_auth_error(mock_decode):
    """
    REGRESSION: Second use of a refresh token must be rejected.
    revoke_session_by_jti returns False (already revoked) → AuthError.
    """
    user = make_user()
    repo = _make_mock_repo(user=user, revoke_returns=False)  # already revoked
    service = _make_service(repo=repo)

    with pytest.raises(AuthError) as exc_info:
        await service.refresh_tokens("already.used.token")

    assert exc_info.value.status_code == 401
    assert "already been used" in exc_info.value.message


@patch(
    "apps.api.services.auth_service.jwt_module.decode_refresh_token",
    return_value={"jti": "jti-redis-denied", "sub": str(uuid.uuid4()), "type": "refresh"},
)
async def test_refresh_redis_denylist_blocks(mock_decode):
    """Token present in Redis denylist must be rejected immediately."""
    user = make_user()
    repo = _make_mock_repo(user=user)
    redis = _make_mock_redis(jti_revoked=True)  # simulates denylist hit
    service = _make_service(repo=repo, redis=redis)

    with pytest.raises(AuthError) as exc_info:
        await service.refresh_tokens("denylisted.token")

    assert exc_info.value.status_code == 401
    repo.revoke_session_by_jti.assert_not_awaited()


# ── Domain invariants ─────────────────────────────────────────────────────────


def test_user_email_normalisation():
    user = make_user(email="  TEST@EXAMPLE.COM  ")
    assert user.email == "test@example.com"


def test_active_user_is_active():
    user = make_user(status=UserStatus.ACTIVE)
    assert user.is_active is True


def test_suspended_user_is_not_active():
    user = make_user(status=UserStatus.SUSPENDED)
    assert user.is_active is False


def test_suspended_user_assert_can_authenticate_raises():
    user = make_user(status=UserStatus.SUSPENDED)
    with pytest.raises(PermissionError):
        user.assert_can_authenticate()


def test_active_user_assert_can_authenticate_passes():
    user = make_user(status=UserStatus.ACTIVE)
    user.assert_can_authenticate()  # must not raise
