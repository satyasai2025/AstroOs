"""
AstroOS — AI Settings Aggregate (Domain Layer)

Pure Python dataclass. No ORM, no HTTP, no framework dependency.

Deliberately never carries the decrypted API key — only whether one is
set and its last 4 characters — so the router/service layer has no
plaintext secret to accidentally leak into a response. The decrypted key
is fetched separately, only by apps.api.services.ai_provider, and only
for making the outbound AI call itself.
"""

from dataclasses import dataclass
from typing import Optional

from apps.api.domain.user import UserId

PROVIDERS = ("astroos_ai", "openai", "anthropic", "gemini", "openrouter", "ollama")
"""astroos_ai means "use the server's own configured provider" (Settings.OPENAI_*)
— the only provider that needs no user-supplied API key."""


@dataclass
class AISettings:
    user_id: UserId
    provider: str
    has_api_key: bool
    api_key_last4: Optional[str]
    model: Optional[str]
    base_url: Optional[str]
    temperature: float
    max_tokens: int

    def __post_init__(self) -> None:
        if self.provider not in PROVIDERS:
            raise ValueError(f"Unknown AI provider: {self.provider!r}")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        if not (1 <= self.max_tokens <= 32000):
            raise ValueError("max_tokens must be between 1 and 32000")
        if self.base_url is not None and self.provider != "ollama":
            raise ValueError("base_url override is only supported for provider='ollama'")
