"""
AstroOS — JWT Token Management (RS256)

Uses asymmetric RSA keys so the public key can be distributed to other
services for token verification without sharing the signing secret.

Token structure:
  Access token  — short-lived (default 30 min), carries user claims.
  Refresh token — long-lived (default 7 days), only carries jti + sub.

The *jti* (JWT ID) is a random UUID stored in Redis on revocation,
implementing a denylist that survives process restarts.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from jose import JWTError, jwt

from apps.api.config import get_settings

_settings = get_settings()


def _load_key(path: str, env_var: Optional[str] = None) -> str:
    import os
    if env_var:
        val = os.getenv(env_var)
        if val:
            return val.replace("\\n", "\n")

    key_path = Path(path)
    if not key_path.exists():
        try:
            from apps.api.security.generate_keys import generate_rsa_key_pair
            generate_rsa_key_pair()
        except Exception:
            pass

    if not key_path.exists():
        raise FileNotFoundError(
            f"JWT key not found at '{path}'. "
            "Run `python apps/api/security/generate_keys.py` first."
        )
    return key_path.read_text()


def _private_key() -> str:
    return _load_key(_settings.JWT_PRIVATE_KEY_PATH, "JWT_PRIVATE_KEY")


def _public_key() -> str:
    return _load_key(_settings.JWT_PUBLIC_KEY_PATH, "JWT_PUBLIC_KEY")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    subject: str,
    role: str,
    additional_claims: Optional[dict] = None,
) -> tuple[str, str]:
    """
    Create a signed access token.

    Returns (token_string, jti) where jti uniquely identifies this token.
    """
    now = _utc_now()
    jti = str(uuid4())
    expire = now + timedelta(minutes=_settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict = {
        "sub": subject,
        "jti": jti,
        "iat": now,
        "exp": expire,
        "type": "access",
        "role": role,
    }
    if additional_claims:
        payload.update(additional_claims)

    token = jwt.encode(payload, _private_key(), algorithm=_settings.JWT_ALGORITHM)
    return token, jti


def create_refresh_token(subject: str) -> tuple[str, str]:
    """
    Create a signed refresh token.

    Refresh tokens carry minimal claims — only sub + jti.
    Returns (token_string, jti).
    """
    now = _utc_now()
    jti = str(uuid4())
    expire = now + timedelta(days=_settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": subject,
        "jti": jti,
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }

    token = jwt.encode(payload, _private_key(), algorithm=_settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    """
    Decode and validate a token signature + expiry.
    Raises JWTError on any validation failure.
    Does NOT check the Redis denylist — that is the caller's responsibility.
    """
    return jwt.decode(
        token,
        _public_key(),
        algorithms=[_settings.JWT_ALGORITHM],
        options={"verify_exp": True},
    )


def decode_access_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Token is not an access token.")
    return payload


def decode_refresh_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Token is not a refresh token.")
    return payload
