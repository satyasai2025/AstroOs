"""
AstroOS — AI Settings Service

Business rules for per-user AI provider settings. No HTTP concepts leak
into this layer; no ORM models leak into this layer — only domain
objects. test_connection makes a genuine outbound call so a bad key
fails fast with a clear message instead of only surfacing on first real
use.
"""

from dataclasses import dataclass
from typing import Optional

import httpx

from apps.api.config import Settings
from apps.api.domain.ai_settings import PROVIDERS, AISettings
from apps.api.domain.user import UserId
from apps.api.repositories.ai_settings_repository import AISettingsRepository
from apps.api.services.ai_provider import AIProviderError, build_resolved_provider, call_chat_completion

_TEST_SYSTEM_PROMPT = "Reply with exactly one word: OK."
_TEST_USER_PROMPT = "Connection test."


class AISettingsError(Exception):
    """Raised for expected AI-settings failures. Carries an HTTP status code."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class TestConnectionResult:
    success: bool
    message: str


class AISettingsService:
    def __init__(self, repo: AISettingsRepository, global_settings: Settings) -> None:
        self._repo = repo
        self._settings = global_settings

    async def get_settings(self, user_id: UserId) -> AISettings:
        existing = await self._repo.get_by_user_id(user_id)
        if existing is not None:
            return existing
        # No row yet — report the implicit default rather than 404ing,
        # since "no settings saved" and "using AstroOS AI" are the same
        # thing from the user's point of view.
        return AISettings(
            user_id=user_id,
            provider="astroos_ai",
            has_api_key=False,
            api_key_last4=None,
            model=None,
            base_url=None,
            temperature=0.3,
            max_tokens=1000,
        )

    async def update_settings(
        self,
        user_id: UserId,
        *,
        provider: str,
        api_key: Optional[str],
        clear_api_key: bool,
        model: Optional[str],
        base_url: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> AISettings:
        if provider not in PROVIDERS:
            raise AISettingsError(f"Unknown provider: {provider!r}", status_code=422)
        if base_url and provider != "ollama":
            raise AISettingsError(
                "A custom base_url is only supported for provider='ollama'.", status_code=422
            )
        if not (0.0 <= temperature <= 2.0):
            raise AISettingsError("temperature must be between 0.0 and 2.0", status_code=422)
        if not (1 <= max_tokens <= 32000):
            raise AISettingsError("max_tokens must be between 1 and 32000", status_code=422)

        try:
            return await self._repo.upsert(
                user_id,
                provider=provider,
                api_key=api_key,
                clear_api_key=clear_api_key,
                model=model,
                base_url=base_url,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except AIProviderError as exc:
            raise AISettingsError(str(exc), status_code=422) from exc

    async def test_connection(
        self,
        user_id: UserId,
        http_client: httpx.AsyncClient,
        *,
        provider: str,
        api_key: Optional[str],
        model: Optional[str],
        base_url: Optional[str],
    ) -> TestConnectionResult:
        """
        Test candidate form values, not necessarily what's saved — lets
        the user click Test Connection right after typing a new key,
        before hitting Save. api_key=None means "use the already-stored
        key for this user" (masked in the UI, never re-sent in full).
        """
        if provider not in PROVIDERS:
            raise AISettingsError(f"Unknown provider: {provider!r}", status_code=422)

        effective_key = api_key
        if not effective_key and provider != "astroos_ai":
            effective_key = await self._repo.get_decrypted_api_key(user_id)

        try:
            resolved = build_resolved_provider(
                provider=provider,
                api_key=effective_key,
                model=model,
                base_url=base_url,
                temperature=0.0,
                max_tokens=8,
                global_settings=self._settings,
            )
            reply = await call_chat_completion(
                http_client, resolved, _TEST_SYSTEM_PROMPT, _TEST_USER_PROMPT
            )
            return TestConnectionResult(success=True, message=f"Connected. Model replied: {reply!r}")
        except AIProviderError as exc:
            return TestConnectionResult(success=False, message=str(exc))
