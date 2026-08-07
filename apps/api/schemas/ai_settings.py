"""
AstroOS — AI Settings Schemas

Request/response models for GET/PUT /api/v1/ai/settings and
POST /api/v1/ai/settings/test.
"""

from typing import Optional

from pydantic import BaseModel, Field

from apps.api.domain.ai_settings import PROVIDERS


class AISettingsResponse(BaseModel):
    provider: str = Field(description="One of: " + ", ".join(PROVIDERS))
    has_api_key: bool = Field(description="Whether an API key is stored for this provider.")
    api_key_last4: Optional[str] = Field(
        default=None, description="Last 4 characters of the stored key, for display only."
    )
    model: Optional[str] = Field(default=None, description="NULL means the provider's default model.")
    base_url: Optional[str] = Field(default=None, description="Only meaningful for provider='ollama'.")
    temperature: float
    max_tokens: int


class UpdateAISettingsRequest(BaseModel):
    provider: str = Field(description="One of: " + ", ".join(PROVIDERS))
    api_key: Optional[str] = Field(
        default=None,
        max_length=500,
        description=(
            "Omit to leave the currently stored key untouched. "
            "Pass an empty string to remove the stored key. "
            "Not required for provider='astroos_ai'."
        ),
    )
    model: Optional[str] = Field(default=None, max_length=100)
    base_url: Optional[str] = Field(
        default=None, max_length=500, description="Only allowed for provider='ollama'."
    )
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=32000)


class TestAISettingsRequest(BaseModel):
    provider: str = Field(description="One of: " + ", ".join(PROVIDERS))
    api_key: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Omit to test the already-stored key for this provider.",
    )
    model: Optional[str] = Field(default=None, max_length=100)
    base_url: Optional[str] = Field(default=None, max_length=500)


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
