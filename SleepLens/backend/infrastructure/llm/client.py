"""Minimal OpenAI-compatible chat client (AvalAI / OpenAI / OpenRouter / ...).

Kept dependency-light: httpx only, synchronous (Celery workers and request
handlers both use it). Mirrors the provider pattern used in ApplyStation's
``infrastructure/llm`` without pulling in LangChain.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from .config import LLMConfig, get_llm_config

logger = structlog.get_logger(__name__)


class LLMError(RuntimeError):
    """Raised when the LLM call cannot be completed."""


def chat(
    messages: list[dict[str, str]],
    *,
    config: LLMConfig | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Send a chat completion request and return the assistant text.

    ``messages`` follows the OpenAI schema, e.g.
    ``[{"role": "system", "content": ...}, {"role": "user", "content": ...}]``.
    """
    cfg = config or get_llm_config()
    if not cfg.configured:
        raise LLMError("LLM_API_KEY is not configured.")

    payload: dict[str, Any] = {
        "model": model or cfg.model,
        "messages": messages,
        "temperature": cfg.temperature if temperature is None else temperature,
        "max_tokens": cfg.max_tokens if max_tokens is None else max_tokens,
    }
    url = f"{cfg.base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=cfg.timeout_seconds) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:400] if exc.response is not None else str(exc)
        logger.error("llm_http_error", status=exc.response.status_code if exc.response else None, detail=detail)
        raise LLMError(f"LLM provider error: {detail}") from exc
    except httpx.HTTPError as exc:
        logger.error("llm_transport_error", error=str(exc))
        raise LLMError(f"LLM request failed: {exc}") from exc

    try:
        return str(data["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        logger.error("llm_malformed_response", keys=list(data.keys()))
        raise LLMError("LLM response did not contain a message.") from exc
