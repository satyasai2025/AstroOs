"""
AstroOS — Per-user AI Settings ORM Model

One row per user (enforced by a unique index on user_id), letting each
researcher point pattern-explanation / Ask-tab / AI-search calls at their
own provider and API key instead of the server-wide OPENAI_* config in
apps.api.config.Settings. See apps/api/services/ai_provider.py for how a
missing row (or provider="astroos_ai") falls back to that server-wide config.

api_key_encrypted stores a Fernet token (apps.api.security.encryption), never
plaintext. api_key_last4 duplicates the last 4 characters in plaintext
purely so the UI can render "sk-...ab12" without a decrypt round-trip —
4 characters aren't enough to reconstruct or brute-force the key.
"""

import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


class AISettingsModel(AstroBase):
    __tablename__ = "ai_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="astroos_ai",
        server_default="astroos_ai",
        doc="One of: astroos_ai, openai, anthropic, gemini, openrouter, ollama.",
    )

    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    api_key_last4: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Provider-specific model id. NULL means use that provider's default.",
    )

    base_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Custom API base URL. Only honored for provider='ollama' — see "
        "ai_provider.py's SSRF guard before relaxing that restriction.",
    )

    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.3, server_default="0.3")

    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=1000, server_default="1000")
