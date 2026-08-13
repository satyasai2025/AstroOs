"""
AstroOS API — Application Configuration

All runtime configuration is loaded from environment variables.
No value is hardcoded here; every default is a safe development default only.
Production environments must supply all required fields via env or .env file.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings driven by environment variables.
    Pydantic-settings performs type coercion and validation at startup,
    so misconfigured deployments fail fast rather than silently.
    """

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "AstroOS API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # ── Database (PostgreSQL) ─────────────────────────────────────────────────
    DATABASE_URL: str  # required — no default
    DB_ECHO_SQL: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TOKEN_DENYLIST_TTL: int = 60 * 60 * 24 * 7  # 7 days in seconds

    # ── JWT / Auth ────────────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY_PATH: str = "apps/api/security/keys/private.pem"
    JWT_PUBLIC_KEY_PATH: str = "apps/api/security/keys/public.pem"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Security ──────────────────────────────────────────────────────────────
    BCRYPT_ROUNDS: int = 12

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
    ]
    ALLOWED_HOSTS: List[str] = ["*"]

    # ── Swiss Ephemeris ───────────────────────────────────────────────────────
    EPHEMERIS_PATH: str = "data/ephemeris"
    """
    Directory containing official Swiss Ephemeris .se1 binary data files.
    If the directory is empty or missing the required files, pyswisseph falls
    back to the built-in Moshier approximation automatically.
    The health check reports which mode is active.
    """

    EPHEMERIS_CACHE_TTL: int = 3600  # 1 hour; results are deterministic per input

    # ── Geocoding (birth place search) ────────────────────────────────────────
    GEOCODING_PROVIDER_URL: str = "https://nominatim.openstreetmap.org/search"
    """
    OpenStreetMap Nominatim's public instance — free, no API key required.
    Nominatim's usage policy (https://operations.osmfoundation.org/policies/nominatim/)
    requires a descriptive User-Agent (below) and caps heavy/production use at
    ~1 request/second; the frontend debounces search input to stay well under
    that. Swap this for a self-hosted Nominatim instance or a paid provider
    (Google/Mapbox) before any real production traffic.
    """
    GEOCODING_USER_AGENT: str = "AstroOS/1.0 (development)"

    # ── LLM (pattern explanations + natural-language pattern Q&A) ────────────
    OPENAI_API_KEY: str | None = None
    """Set this in .env to enable AI-generated pattern explanations
    (POST /research/cases/patterns/{pattern_id}/explain) and the
    natural-language Ask tab (POST /research/cases/patterns/ask). Left
    unset, those endpoints return a clear error rather than silently
    degrading.

    Despite the name, this is not OpenAI-only: any provider exposing an
    OpenAI-compatible /chat/completions endpoint works by pointing
    OPENAI_BASE_URL at it. For Google Gemini, use its OpenAI compatibility
    layer — see OPENAI_BASE_URL below."""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    """Base URL of an OpenAI-compatible API. ``/chat/completions`` is
    appended to it.

    OpenAI (default):
        OPENAI_BASE_URL=https://api.openai.com/v1
        OPENAI_MODEL=gpt-4o-mini
    Google Gemini (OpenAI compatibility layer):
        OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
        OPENAI_MODEL=gemini-2.0-flash
    """
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── AI Engine Backend (Phase IV, IV.3 — opt-in local LLM narration) ───────
    AI_BACKEND: str = "template"
    """
    "template" (default): the existing deterministic, template-based
    narration in apps/api/services/ai_engine.py — no network access at
    all, same output every time for the same input.

    "local_llm": opt-in enrichment of that same template output via a
    locally-hosted, OpenAI-compatible model server that YOU run
    yourself (e.g. Ollama, LM Studio) — never a cloud/external API call,
    unlike OPENAI_API_KEY above (which is a separate, already-existing
    feature for research pattern explanations). The model is instructed
    to rewrite using only the template's own facts, not invent new
    astrological claims. If the local server is unreachable or times
    out, AIEngine silently falls back to the plain template output —
    the deterministic-fallback guarantee never breaks.
    """
    LOCAL_LLM_BASE_URL: str = "http://localhost:11434/v1"
    """OpenAI-compatible base URL of the local model server. Ollama's
    built-in OpenAI-compatible endpoint is http://localhost:11434/v1."""
    LOCAL_LLM_MODEL: str = "llama3.1"
    LOCAL_LLM_TIMEOUT_SECONDS: float = 15.0

    # ── Secrets at rest (per-user AI settings API keys) ───────────────────────
    ENCRYPTION_KEY: str
    """
    A urlsafe-base64-encoded 32-byte key (Fernet format) used to encrypt
    user-supplied AI provider API keys before they're stored in the
    ai_settings table. Required — no default, since a missing/placeholder
    value would silently make stored keys unrecoverable or, worse, guessable.
    Generate one with:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    Rotating this key invalidates every previously stored API key — users
    would need to re-enter them.
    """

    # ── Worker Pools (Phase II.4 — local-first) ─────────────────────────────────
    WORKER_CPU_MIN: int = 1
    WORKER_CPU_MAX: int = 4
    WORKER_IO_MIN: int = 2
    WORKER_IO_MAX: int = 16
    WORKER_AI_MIN: int = 1
    WORKER_AI_MAX: int = 4
    WORKER_AUTOSCALE_INTERVAL_SECONDS: float = 5.0
    """
    How often the local autoscaler re-evaluates each pool's queue depth and
    grows/shrinks it within [MIN, MAX]. In-process only — no HPA/K8s.
    """
    WORKER_MAX_RETRIES: int = 3
    WORKER_RETRY_BASE_DELAY_SECONDS: float = 1.0
    """Exponential backoff base: delay = BASE * 2^(attempt-1)."""
    WORKER_JOB_TTL_SECONDS: int = 24 * 60 * 60
    """How long completed/failed job records are kept in memory before eviction."""
    BATCH_OUTPUT_DIR: str = "data/batch_output"
    """Local directory where batch job result archives (zips) are written."""

    # ── Email / SMTP (password reset) ───────────────────────────────────────
    SMTP_HOST: str | None = None
    """Left unset (safe local-development default), password-reset emails
    are logged instead of sent — see apps/api/services/email_service.py."""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "noreply@astroos.local"
    SMTP_USE_TLS: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    """Origin used to build links (e.g. the password-reset link) sent in emails."""
    PASSWORD_RESET_TOKEN_TTL_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Return the singleton Settings instance.
    Cached so the .env file is parsed exactly once per process.
    """
    return Settings()
