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
from apps.api.services.disposable_email import is_disposable_email


# ── Shared validators ────────────────────────────────────────────────────────


def _validate_password_strength(v: str) -> str:
    has_upper = any(c.isupper() for c in v)
    has_lower = any(c.islower() for c in v)
    has_digit = any(c.isdigit() for c in v)
    if not (has_upper and has_lower and has_digit):
        raise ValueError(
            "Password must contain at least one uppercase letter, "
            "one lowercase letter, and one digit."
        )
    return v


# ── Request Schemas ───────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """Request payload for register operations."""
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

    @field_validator("email")
    @classmethod
    def reject_disposable_email(cls, v: str) -> str:
        if is_disposable_email(v):
            raise ValueError(
                "Disposable/temporary email addresses are not allowed. "
                "Please use a permanent email address."
            )
        return v

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, v: str) -> str:
        # Capitalize each word in display_name (name/last name)
        return " ".join(word.capitalize() for word in v.strip().split())

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class LoginRequest(BaseModel):
    """Request payload for login operations."""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class RefreshTokenRequest(BaseModel):
    """Request payload for refresh token operations."""
    refresh_token: str = Field(..., description="Opaque refresh token string.")


class ForgotPasswordRequest(BaseModel):
    """Request payload for initiating a password reset."""
    email: EmailStr = Field(..., description="Email address of the account.")


class ResetPasswordRequest(BaseModel):
    """Request payload for completing a password reset."""
    token: str = Field(..., description="Opaque password-reset token from the email link.")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password, 8–128 characters.",
    )

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class UpdateProfileRequest(BaseModel):
    """Request payload for updating a user's own profile (PATCH /auth/me)."""
    display_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="New public display name.",
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="New account email address.",
    )
    timezone: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="IANA timezone name (e.g. 'Asia/Kolkata'). Validated against the tzdata database.",
    )

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Capitalize each word in display_name (name/last name)
        return " ".join(word.capitalize() for word in v.strip().split())

    @field_validator("email")
    @classmethod
    def reject_disposable_email(cls, v: Optional[EmailStr]) -> Optional[EmailStr]:
        if v is None:
            return v
        if is_disposable_email(v):
            raise ValueError(
                "Disposable/temporary email addresses are not allowed. "
                "Please use a permanent email address."
            )
        return v

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UpdateProfileRequest":
        if self.display_name is None and self.email is None and self.timezone is None:
            raise ValueError("Provide at least one of display_name, email, or timezone.")
        return self


class ChangePasswordRequest(BaseModel):
    """Request payload for changing the authenticated user's password."""
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password, 8–128 characters.",
    )

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


# ── Response Schemas ──────────────────────────────────────────────────────────


class UserResponse(BaseModel):
    """Response payload describing user data."""
    id: UUID
    email: str
    display_name: str
    role: str
    status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None
    timezone: str = "UTC"

    model_config = {"from_attributes": True}


class TokenPairResponse(BaseModel):
    """Response payload describing token pair data."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(description="Access token TTL in seconds.")


class AuthResponse(BaseModel):
    """Response payload describing auth data."""
    user: UserResponse
    tokens: TokenPairResponse


class MessageResponse(BaseModel):
    """Response payload describing message data."""
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
