"""LLM configuration resolved from the environment (OpenAI-compatible)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_BASE_URL = "https://api.avalai.ir/v1"
DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class LLMConfig:
    """Provider settings for the OpenAI-compatible chat endpoint."""

    base_url: str
    api_key: str
    model: str
    max_tokens: int
    temperature: float
    timeout_seconds: float

    @property
    def configured(self) -> bool:
        return bool(self.api_key)


def _to_int(value: str, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _to_float(value: str, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


@lru_cache(maxsize=1)
def get_llm_config() -> LLMConfig:
    """Read LLM_* environment variables (cached)."""
    return LLMConfig(
        base_url=os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        api_key=os.getenv("LLM_API_KEY", ""),
        model=os.getenv("LLM_MODEL", DEFAULT_MODEL),
        max_tokens=_to_int(os.getenv("LLM_MAX_TOKENS", ""), 4096),
        temperature=_to_float(os.getenv("LLM_TEMPERATURE", ""), 0.2),
        timeout_seconds=_to_float(os.getenv("LLM_TIMEOUT_SECONDS", ""), 120.0),
    )
