"""Client for the local opencode agent server (sessions + messages).

The opencode server (``opencode serve --port 4096``) exposes a small REST API:
  GET  /session                 -> list sessions (used as a health probe)
  POST /session {"title": ...}  -> {"id": "<session-id>", ...}
  POST /session/{id}/message    -> append a message, returns the assistant message
  GET  /session/{id}/message    -> full message history (used for recovery)

This adapter is Django-free and proxy-agnostic (``trust_env=False`` so machine
HTTP proxies do not intercept localhost traffic).
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from .config import OpenCodeConfig, get_opencode_config

logger = structlog.get_logger(__name__)


class OpenCodeError(RuntimeError):
    """Raised when the opencode server cannot fulfil a request."""


class OpenCodeClient:
    """Thin, explicit wrapper around the opencode session API."""

    def __init__(self, config: OpenCodeConfig | None = None) -> None:
        self.config = config or get_opencode_config()

    def _headers(self) -> dict[str, str]:
        """Optional bearer auth (some opencode servers require it)."""
        if self.config.api_key:
            return {"Authorization": f"Bearer {self.config.api_key}"}
        return {}

    # ── health ───────────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """True when the opencode server answers on /session."""
        try:
            with httpx.Client(
                timeout=self.config.connect_timeout_seconds, trust_env=False
            ) as client:
                response = client.get(self.config.health_url, headers=self._headers())
                return response.status_code < 500
        except httpx.HTTPError:
            return False

    # ── sessions ─────────────────────────────────────────────────────────────

    def create_session(self, title: str) -> str:
        payload = {"title": title}
        data = self._request("POST", "/session", json=payload)
        session_id = (data or {}).get("id") if isinstance(data, dict) else None
        if not session_id:
            raise OpenCodeError("opencode did not return a session id.")
        logger.info("opencode_session_created", session_id=session_id)
        return str(session_id)

    def delete_session(self, session_id: str) -> None:
        """Best-effort session cleanup."""
        try:
            self._request("DELETE", f"/session/{session_id}")
        except OpenCodeError as exc:
            logger.warning("opencode_session_delete_failed", session_id=session_id, error=str(exc))

    # ── messages ─────────────────────────────────────────────────────────────

    def send_message(self, session_id: str, text: str) -> str:
        """Append a user message and return the assistant's reply text.

        When ``OPENCODE_MODEL`` is configured (``providerID/modelID``) it is sent
        with every message, so the server's default model does not apply.
        """
        payload: dict[str, Any] = {"parts": [{"type": "text", "text": text}]}
        model = self.config.model_payload()
        if model:
            payload["model"] = model
        try:
            data = self._request("POST", f"/session/{session_id}/message", json=payload)
            extracted = _extract_text(data)
            if extracted:
                return extracted
        except OpenCodeError as exc:
            logger.info("opencode_send_recovering", session_id=session_id, error=str(exc))

        history = self._request("GET", f"/session/{session_id}/message")
        for message in reversed(history or []):
            if isinstance(message, dict) and (message.get("info", {}) or {}).get("role") == "assistant":
                info = message.get("info", {}) or {}
                error = info.get("error")
                if error:
                    detail = (error.get("data", {}) or {}).get("message") if isinstance(error, dict) else None
                    raise OpenCodeError(
                        f"opencode model error ({info.get('providerID')}/{info.get('modelID')}): "
                        f"{detail or error}"
                    )
                extracted = _extract_text(message)
                if extracted:
                    return extracted
        raise OpenCodeError("opencode returned no assistant reply for this session.")

    # ── internals ────────────────────────────────────────────────────────────

    def _request(self, method: str, path: str, json: dict | None = None) -> Any:
        url = f"{self.config.base_url}{path}"
        try:
            with httpx.Client(timeout=self.config.timeout_seconds, trust_env=False) as client:
                response = client.request(method, url, json=json, headers=self._headers())
                response.raise_for_status()
                if not response.content:
                    return None
                return response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:300] if exc.response is not None else str(exc)
            raise OpenCodeError(f"opencode HTTP {exc.response.status_code}: {detail}") from exc
        except httpx.HTTPError as exc:
            raise OpenCodeError(f"opencode unreachable at {self.config.base_url}: {exc}") from exc


def _extract_text(data: Any) -> str | None:
    """Extract assistant text from an opencode message dict or a message list."""
    if isinstance(data, list):
        for item in reversed(data):
            text = _extract_text(item)
            if text:
                return text
        return None
    if isinstance(data, dict):
        for part in data.get("parts", []) or []:
            if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                return str(part["text"]).strip()
        for key in ("content", "message", "text"):
            if isinstance(data.get(key), str) and data[key].strip():
                return data[key].strip()
    return None
