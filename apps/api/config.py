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
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
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
