"""LLM adapters for any OpenAI-compatible provider (AvalAI by default)."""

from __future__ import annotations

from .client import LLMError, chat
from .config import LLMConfig, get_llm_config

__all__ = ["LLMConfig", "LLMError", "chat", "get_llm_config"]
