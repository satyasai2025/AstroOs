"""
AstroOS — Admin Auth Router

Public admin authentication endpoints (login, me, logout).
Separate from the admin management routes which require admin auth.

This router is included WITHOUT the require_admin dependency so
that the login endpoint is accessible to unauthenticated users.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

logger = logging.getLogger("astroos.admin_auth")

router = APIRouter(prefix="/admin/auth", tags=["Admin Authentication"])


# ── Dependency for protected admin routes ──────────────────────────
# This replaces the existing `require_admin` which only accepts RS256 tokens.
# Admin tokens are HS256-signed, so we verify them with our custom logic.

async def require_admin_token(request: Request):
    """Dependency that validates admin HS256 tokens for protected admin routes."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing admin token")
    token = auth_header.split(" ", 1)[1]
    try:
        payload = verify_admin_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return payload

# ── Configuration ─────────────────────────────────────────────────

ADMIN_JWT_SECRET = os.getenv(
    "ADMIN_JWT_SECRET",
    os.getenv("ADMIN_SECRET_KEY", "astroos-admin-secret-change-in-production"),
)
ADMIN_JWT_ALGORITHM = "HS256"
ADMIN_TOKEN_EXPIRY_HOURS = 8


# ── Rate Limiter ──────────────────────────────────────────────────

_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 900


def _check_rate_limit(identifier: str) -> bool:
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    if identifier not in _rate_limit_store:
        _rate_limit_store[identifier] = []
    _rate_limit_store[identifier] = [t for t in _rate_limit_store[identifier] if t > cutoff]
    if len(_rate_limit_store[identifier]) >= RATE_LIMIT_MAX_ATTEMPTS:
        return False
    _rate_limit_store[identifier].append(now)
    return True


def _reset_rate_limit(identifier: str) -> None:
    _rate_limit_store.pop(identifier, None)


# ── JWT Utilities ─────────────────────────────────────────────────

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _sign(payload: str) -> str:
    return _base64url_encode(
        hmac.new(
            ADMIN_JWT_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    )


def create_admin_token(user_id: str, email: str, role: str = "super_admin") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "admin": True,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ADMIN_TOKEN_EXPIRY_HOURS)).timestamp()),
        "jti": secrets.token_hex(16),
    }
    header = {"alg": ADMIN_JWT_ALGORITHM, "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _sign(f"{header_b64}.{payload_b64}")
    return f"{header_b64}.{payload_b64}.{signature}"


def create_admin_refresh_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "admin": True,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
        "jti": secrets.token_hex(16),
    }
    header = {"alg": ADMIN_JWT_ALGORITHM, "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _sign(f"{header_b64}.{payload_b64}")
    return f"{header_b64}.{payload_b64}.{signature}"


def verify_admin_token(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        header_b64, payload_b64, signature_b64 = parts
        expected = _sign(f"{header_b64}.{payload_b64}")
        if not hmac.compare_digest(signature_b64, expected):
            raise ValueError("Invalid signature")
        payload = json.loads(_base64url_decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            raise ValueError("Token expired")
        if not payload.get("admin"):
            raise ValueError("Not an admin token")
        return payload
    except Exception as e:
        raise ValueError(f"Invalid admin token: {e}")


# ── Password Hashing (bcrypt) ────────────────────────────────────

try:
    import bcrypt

    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

    def _verify_password(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
except ImportError:
    import hashlib as _hl

    def _hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        h = _hl.sha256((salt + password).encode()).hexdigest()
        return f"{salt}${h}"

    def _verify_password(password: str, password_hash: str) -> bool:
        parts = password_hash.split("$")
        if len(parts) != 2:
            return False
        salt, h = parts
        return _hl.sha256((salt + password).encode()).hexdigest() == h


# ── In-memory demo data ──────────────────────────────────────────

_admin_users: dict[str, dict] = {}
_audit_logs: list[dict] = []


def _init_demo():
    """Seed demo admin account."""
    uid = "admin-001"
    _admin_users[uid] = {
        "id": uid,
        "email": "admin@astroos.dev",
        "display_name": "System Administrator",
        "password_hash": _hash_password("admin123"),
        "role": "super_admin",
        "mfa_enabled": False,
        "status": "active",
        "last_login_at": None,
        "failed_login_attempts": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _audit_logs.append({
        "id": "log-init",
        "admin_id": uid,
        "admin_email": "admin@astroos.dev",
        "action": "system.initialize",
        "resource_type": "system",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


_init_demo()


def _log_audit(admin_id: str, admin_email: str, action: str,
               resource_type: str = "auth", resource_id: str = None,
               details: dict = None, ip_address: str = "unknown"):
    entry = {
        "id": f"log-{secrets.token_hex(8)}",
        "admin_id": admin_id,
        "admin_email": admin_email,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "ip_address": ip_address,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _audit_logs.insert(0, entry)
    if len(_audit_logs) > 1000:
        _audit_logs.pop()
    return entry


# ── Request/Response Schemas ──────────────────────────────────────

class AdminLoginRequest(BaseModel):
    email: str
    password: str
    mfa_code: Optional[str] = None


class AdminLoginResponse(BaseModel):
    user: dict
    tokens: dict


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


# ── Routes ────────────────────────────────────────────────────────

@router.post("/login")
async def admin_login(req: AdminLoginRequest, request: Request):
    """Admin login — returns separate admin JWT tokens."""
    ip = _get_client_ip(request)

    if not _check_rate_limit(f"admin_login:{req.email}"):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    # Find admin user
    admin = None
    for u in _admin_users.values():
        if u["email"] == req.email.lower().strip():
            admin = u
            break

    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if admin["status"] == "suspended":
        raise HTTPException(status_code=403, detail="Account suspended")

    if not _verify_password(req.password, admin["password_hash"]):
        admin["failed_login_attempts"] = admin.get("failed_login_attempts", 0) + 1
        if admin["failed_login_attempts"] >= 5:
            admin["status"] = "locked"
        _log_audit(admin["id"], admin["email"], "auth.login.failed",
                   details={"reason": "invalid_password"}, ip_address=ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Success
    _reset_rate_limit(f"admin_login:{req.email}")
    admin["last_login_at"] = datetime.now(timezone.utc).isoformat()
    admin["failed_login_attempts"] = 0

    access_token = create_admin_token(admin["id"], admin["email"], admin["role"])
    refresh_token = create_admin_refresh_token(admin["id"])

    _log_audit(admin["id"], admin["email"], "auth.login.success", ip_address=ip)

    user_data = {k: v for k, v in admin.items() if k != "password_hash"}
    return AdminLoginResponse(
        user=user_data,
        tokens={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": ADMIN_TOKEN_EXPIRY_HOURS * 3600,
        },
    )


@router.get("/me")
async def admin_me(request: Request):
    """Return current admin user info from token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing admin token")
    token = auth_header.split(" ", 1)[1]
    try:
        payload = verify_admin_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    admin = _admin_users.get(payload["sub"])
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")

    return {k: v for k, v in admin.items() if k != "password_hash"}


@router.post("/logout")
async def admin_logout(request: Request):
    """Admin logout (client clears tokens)."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            payload = verify_admin_token(auth_header.split(" ", 1)[1])
            _log_audit(payload.get("sub", ""), payload.get("email", ""), "auth.logout")
        except ValueError:
            pass
    return {"message": "Logged out successfully"}


# ── Dashboard (aggregated) ───────────────────────────────────────

@router.get("/dashboard")
async def admin_dashboard(request: Request):
    """Aggregated admin dashboard data."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing admin token")
    try:
        payload = verify_admin_token(auth_header.split(" ", 1)[1])
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return {
        "admin": {"id": payload["sub"], "email": payload["email"], "role": payload["role"]},
        "stats": {
            "total_admin_users": len(_admin_users),
            "active_admin_users": sum(1 for u in _admin_users.values() if u["status"] == "active"),
            "total_audit_logs": len(_audit_logs),
        },
        "system": {"status": "healthy", "version": "2.3.0"},
    }
