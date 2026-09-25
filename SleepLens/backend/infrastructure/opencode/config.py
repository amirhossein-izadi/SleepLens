"""Configuration for the local opencode agent server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_BASE_URL = "http://127.0.0.1:4096"


@dataclass(frozen=True)
class OpenCodeConfig:
    """Where the opencode server runs and how patient we are with it."""

    base_url: str
    timeout_seconds: float
    connect_timeout_seconds: float
    api_key: str = ""
    model: str = ""

    @property
    def health_url(self) -> str:
        return f"{self.base_url}/session"

    def model_payload(self) -> dict[str, str] | None:
        """`providerID/modelID` -> {"providerID": ..., "modelID": ...}."""
        if not self.model or "/" not in self.model:
            return None
        provider_id, model_id = self.model.split("/", 1)
        if not provider_id or not model_id:
            return None
        return {"providerID": provider_id, "modelID": model_id}


def _to_float(value: str, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


@lru_cache(maxsize=1)
def get_opencode_config() -> OpenCodeConfig:
    """Read OPENCODE_* environment variables (cached)."""
    return OpenCodeConfig(
        base_url=os.getenv("OPENCODE_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        timeout_seconds=_to_float(os.getenv("OPENCODE_TIMEOUT_SECONDS", ""), 180.0),
        connect_timeout_seconds=_to_float(os.getenv("OPENCODE_CONNECT_TIMEOUT", ""), 3.0),
        api_key=os.getenv("OPENCODE_API_KEY", ""),
        model=os.getenv("OPENCODE_MODEL", ""),
    )
