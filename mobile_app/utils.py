"""Helpers for offline caching and notifications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CACHE_FILE = Path(__file__).parent / "offline_cache.json"


def save_cache(payload: Any) -> None:
    CACHE_FILE.write_text(json.dumps(payload))


def load_cache() -> Any:
    if not CACHE_FILE.exists():
        return None
    return json.loads(CACHE_FILE.read_text())


__all__ = ["save_cache", "load_cache"]
