"""API renderer enforcing the standard SleepLens response envelope.

Success responses are ``{"success": true, "data": ...}``; list endpoints add
``metadata`` (from ``common.pagination.StandardPagination``). Errors are
produced by ``common.exceptions.custom_exception_handler`` and already carry
the envelope, so this renderer passes them through untouched.
"""

from __future__ import annotations

from typing import Any

from rest_framework.renderers import JSONRenderer


class ApiRenderer(JSONRenderer):
    """Wrap bare payloads in the standard envelope."""

    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict | None = None,
    ) -> bytes:
        payload = self._envelope(data, renderer_context)
        return super().render(payload, accepted_media_type, renderer_context)

    @staticmethod
    def _envelope(data: Any, renderer_context: dict | None) -> Any:
        if renderer_context is None:
            return data
        response = renderer_context.get("response")
        already_enveloped = isinstance(data, dict) and "success" in data

        if already_enveloped:
            return data
        if data is None:
            return {"success": response is not None and response.status_code < 400, "data": None}
        if response is not None and response.status_code >= 400:
            return {
                "success": False,
                "data": None,
                "error": {"code": "ERROR", "message": str(data), "details": []},
            }
        return {"success": True, "data": data}
