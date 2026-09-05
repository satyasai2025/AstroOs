"""
AstroOS — AI Provider Resolver

Single place that turns "the current user's AI settings, or lack thereof"
into a concrete (provider, api_key, model, base_url, temperature,
max_tokens) tuple, and knows how to make the actual chat-completion call
for each of the 6 supported providers. Every AI-backed feature
(pattern_explainer, pattern_query_assistant, ai_search_assistant) goes
through resolve_provider() + call_chat_completion() rather than reading
Settings.OPENAI_* or building its own httpx call directly — that's what
makes per-user BYOK settings take effect everywhere instead of only
wherever someone remembered to check for them.

build_resolved_provider() is also used directly by ai_settings_service's
test_connection, which needs to validate candidate form values that
haven't been saved yet — not necessarily what's already in the DB.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx

from apps.api.config import Settings
from apps.api.domain.user import UserId
from apps.api.repositories.ai_settings_repository import AISettingsRepository

_PROVIDER_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",
}

_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-5",
    "gemini": "gemini-3.6-flash",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "google/gemma-4-26b-a4b-it:free",
    "ollama": "llama3.1",
}

_ANTHROPIC_VERSION = "2023-06-01"
_REQUEST_TIMEOUT_SECONDS = 30.0


class AIProviderError(RuntimeError):
    """Raised when no usable provider/key is configured, or the call fails."""


@dataclass
class ResolvedAIProvider:
    provider: str
    api_key: Optional[str]
    model: str
    base_url: str
    temperature: float
    max_tokens: int


def _guard_base_url(base_url: str) -> None:
    """
    Minimal SSRF hardening for user-supplied Ollama base URLs — the one
    place this server makes an outbound request to an address a user
    chose rather than one hardcoded above. Blocks the well-known cloud
    metadata endpoints (169.254.169.254 etc, all link-local); does NOT
    block private/loopback ranges in general, since "point this at my own
    LAN/localhost Ollama instance" is the entire point of the feature.
    """
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https"):
        raise AIProviderError("base_url must use http or https.")
    host = parsed.hostname
    if not host:
        raise AIProviderError("base_url is missing a host.")
    try:
        resolved_ips = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror as exc:
        raise AIProviderError(f"Could not resolve base_url host: {host}") from exc
    for ip_str in resolved_ips:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_link_local:
            raise AIProviderError("base_url may not point at a link-local address.")


def build_resolved_provider(
    *,
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    base_url: Optional[str],
    temperature: float,
    max_tokens: int,
    global_settings: Settings,
) -> ResolvedAIProvider:
    """Fill in provider defaults and validate, without touching the DB."""
    if provider == "astroos_ai":
        resolved_key = (
            global_settings.GEMINI_API_KEY
            or global_settings.GROQ_API_KEY
            or global_settings.OPENROUTER_API_KEY
            or global_settings.OPENAI_API_KEY
        )
        resolved_base = global_settings.OPENAI_BASE_URL
        resolved_model = global_settings.OPENAI_MODEL

        # Priority / Auto-detection:
        if global_settings.DEFAULT_AI_PROVIDER == "groq" and global_settings.GROQ_API_KEY:
            resolved_key = global_settings.GROQ_API_KEY
            resolved_base = "https://api.groq.com/openai/v1"
            resolved_model = "llama-3.3-70b-versatile"
        elif global_settings.DEFAULT_AI_PROVIDER == "openrouter" and global_settings.OPENROUTER_API_KEY:
            resolved_key = global_settings.OPENROUTER_API_KEY
            resolved_base = "https://openrouter.ai/api/v1"
            resolved_model = "google/gemma-4-26b-a4b-it:free"
        elif global_settings.GEMINI_API_KEY:
            resolved_key = global_settings.GEMINI_API_KEY
            resolved_base = "https://generativelanguage.googleapis.com/v1beta/openai"
            resolved_model = "gemini-3.6-flash"
        elif global_settings.GROQ_API_KEY:
            resolved_key = global_settings.GROQ_API_KEY
            resolved_base = "https://api.groq.com/openai/v1"
            resolved_model = "llama-3.3-70b-versatile"
        elif global_settings.OPENROUTER_API_KEY:
            resolved_key = global_settings.OPENROUTER_API_KEY
            resolved_base = "https://openrouter.ai/api/v1"
            resolved_model = "google/gemma-4-26b-a4b-it:free"
        elif resolved_key:
            clean_key = resolved_key.strip()
            if clean_key.startswith("gsk_"):
                resolved_base = "https://api.groq.com/openai/v1"
                resolved_model = "llama-3.3-70b-versatile"
            elif clean_key.startswith("AIza") or clean_key.startswith("AQ."):
                resolved_base = "https://generativelanguage.googleapis.com/v1beta/openai"
                resolved_model = "gemini-3.6-flash"
            elif clean_key.startswith("sk-or-"):
                resolved_base = "https://openrouter.ai/api/v1"
                resolved_model = "google/gemma-4-26b-a4b-it:free"

        return ResolvedAIProvider(
            provider="astroos_ai",
            api_key=resolved_key,
            model=resolved_model,
            base_url=resolved_base,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    resolved_base_url = base_url or _PROVIDER_BASE_URLS[provider]
    if provider == "ollama" and base_url:
        _guard_base_url(resolved_base_url)
    resolved_model = model or _DEFAULT_MODELS[provider]

    return ResolvedAIProvider(
        provider=provider,
        api_key=api_key,
        model=resolved_model,
        base_url=resolved_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def resolve_provider(
    user_id: Optional[UserId],
    repo: AISettingsRepository,
    global_settings: Settings,
) -> ResolvedAIProvider:
    """
    Resolve the effective AI provider config for a request.

    Falls back to the server-wide Settings.OPENAI_* config when the user
    has no ai_settings row, or explicitly selected provider="astroos_ai".
    """
    settings_row = await repo.get_by_user_id(user_id) if user_id is not None else None

    if settings_row is None:
        return build_resolved_provider(
            provider="astroos_ai", api_key=None, model=None, base_url=None,
            temperature=0.3, max_tokens=1000, global_settings=global_settings,
        )

    api_key = None
    if settings_row.provider != "astroos_ai":
        api_key = await repo.get_decrypted_api_key(user_id)

    return build_resolved_provider(
        provider=settings_row.provider,
        api_key=api_key,
        model=settings_row.model,
        base_url=settings_row.base_url,
        temperature=settings_row.temperature,
        max_tokens=settings_row.max_tokens,
        global_settings=global_settings,
    )


async def call_chat_completion(
    client: httpx.AsyncClient,
    resolved: ResolvedAIProvider,
    system_prompt: str,
    user_prompt: str,
    *,
    json_mode: bool = False,
) -> str:
    """
    Make one chat-completion call, returning the assistant's text.
    Raises AIProviderError on any failure (missing key, HTTP error,
    unexpected response shape) — callers decide how to surface that.

    json_mode requests strict JSON output via response_format on
    OpenAI-compatible providers. Anthropic's Messages API has no
    equivalent parameter — callers relying on json_mode already instruct
    "respond only with JSON" in the prompt itself as the primary
    mechanism, so this is a belt-and-suspenders addition, not silently
    ignored-but-required.
    """
    if not resolved.api_key:
        raise AIProviderError(f"No API key configured for provider '{resolved.provider}'.")

    try:
        if resolved.provider == "anthropic":
            response = await client.post(
                f"{resolved.base_url.rstrip('/')}/messages",
                headers={
                    "x-api-key": resolved.api_key,
                    "anthropic-version": _ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": resolved.model,
                    "max_tokens": resolved.max_tokens,
                    "temperature": resolved.temperature,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            body = response.json()
            return body["content"][0]["text"].strip()

        payload = {
            "model": resolved.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": resolved.temperature,
            "max_tokens": resolved.max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {
            "Authorization": f"Bearer {resolved.api_key}",
            "Content-Type": "application/json",
        }
        if "openrouter.ai" in (resolved.base_url or ""):
            headers["HTTP-Referer"] = "https://astroos.dev"
            headers["X-Title"] = "AstroOS"

        response = await client.post(
            f"{resolved.base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"].get("content") or ""
        return content.strip()

    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:300]
        raise AIProviderError(
            f"{resolved.provider} request failed ({exc.response.status_code}): {detail}"
        ) from exc
    except httpx.HTTPError as exc:
        raise AIProviderError(f"{resolved.provider} request failed: {exc}") from exc
    except (KeyError, IndexError, TypeError) as exc:
        raise AIProviderError(f"Unexpected {resolved.provider} response shape: {body!r}") from exc
