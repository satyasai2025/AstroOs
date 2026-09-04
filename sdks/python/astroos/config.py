"""SDK configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class SdkConfig:
    """Configuration for the AstroOS client.

    Defaults to localhost:8000 — the local-first development target.
    Override ``base_url`` for production (e.g. ``https://api.astroos.dev/api/v1/``).

    Note the trailing slash: Python's ``urllib.parse.urljoin`` requires it on
    the base URL for correct relative-path resolution.
    """

    base_url: str = "http://localhost:8000/api/v1/"
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    retry_backoff: float = 1.5

    @classmethod
    def from_env(cls) -> "SdkConfig":
        """Load configuration from environment variables."""
        return cls(
            base_url=os.environ.get(
                "ASTROOS_BASE_URL", "http://localhost:8000/api/v1/"
            ),
            api_key=os.environ.get("ASTROOS_API_KEY"),
            access_token=os.environ.get("ASTROOS_ACCESS_TOKEN"),
            timeout=int(os.environ.get("ASTROOS_TIMEOUT", "30")),
        )

    @classmethod
    def from_file(cls, path: str) -> "SdkConfig":
        """Load configuration from a JSON file."""
        import json
        with open(path) as f:
            data = json.load(f)
        return cls(**{k: data[k] for k in [
            "base_url", "api_key", "access_token", "timeout",
        ] if k in data})
