"""
AstroOS i18n — Translation Loader (Phase III.5)

Local-first translation system. No cloud translation API required.
Translations are static JSON files shipped with the app.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_LOCALE_DIR = Path(__file__).resolve().parent

_cache: dict[str, dict[str, str]] = {}

_SUPPORTED_LOCALES = {
    "en": "English",
    "es": "Español",
    "hi": "हिन्दी",
    "fr": "Français",
    "de": "Deutsch",
    "ar": "العربية",
}


def supported_locales() -> dict[str, str]:
    """Return dict of locale_code -> display_name."""
    return dict(_SUPPORTED_LOCALES)


def load_locale(locale: str) -> dict[str, str]:
    """Load translations for a locale (cached after first load)."""
    if locale in _cache:
        return _cache[locale]

    path = _LOCALE_DIR / f"{locale}.json"
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    _cache[locale] = data
    return data


def translate(key: str, locale: str = "en", **kwargs: Any) -> str:
    """Translate a key, falling back to the key itself if not found."""
    translations = load_locale(locale)
    template = translations.get(key, key)
    if kwargs:
        return template.format(**kwargs)
    return template


def reload_all() -> None:
    """Clear the translation cache (e.g., after adding new translations)."""
    _cache.clear()
