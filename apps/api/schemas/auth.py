"""
AstroOS — Auth Schemas (Pydantic v2)

Request and response models for all /auth endpoints.
Validation rules are strict; no silent coercion of bad input.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from apps.api.schemas.ephemeris import EphemerisStatusSchema


# ── Request Schemas ───────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address.")
    display_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Public display name.",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password, 8–128 characters.",
    )

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, and one digit."
            )
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Opaque refresh token string.")


# ── Response Schemas ──────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    role: str
    status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(description="Access token TTL in seconds.")


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenPairResponse


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    """
    Returned by GET /api/healthz.
    Includes a nested ephemeris block that reports whether official
    Swiss Ephemeris .se1 files are loaded or the library is using the
    built-in Moshier polynomial fallback.
    """

    status: str
    version: str
    environment: str
    ephemeris: Optional[EphemerisStatusSchema] = Field(
        default=None,
        description=(
            "Swiss Ephemeris engine status. "
            "official_data=true means high-precision .se1 files are loaded; "
            "false means the built-in Moshier approximation is in use."
        ),
    )

    model_config = {"arbitrary_types_allowed": True}
