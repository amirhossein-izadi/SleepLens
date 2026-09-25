"""Custom DRF exception handler producing the standard error envelope."""

from __future__ import annotations

from typing import Any

import structlog
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = structlog.get_logger(__name__)

_CODE_BY_STATUS: dict[int, str] = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    406: "NOT_ACCEPTABLE",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "BUSINESS_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
}


def _details_from(data: Any) -> tuple[str, list[dict[str, str]]]:
    """Return (message, details) for a DRF error payload."""
    if isinstance(data, dict):
        if "detail" in data and len(data) == 1:
            return str(data["detail"]), []
        details = [
            {
                "field": str(field),
                "message": " ".join(str(item) for item in value)
                if isinstance(value, list)
                else str(value),
            }
            for field, value in data.items()
        ]
        return "Validation failed", details
    if isinstance(data, list):
        return "; ".join(str(item) for item in data), []
    return str(data), []


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """Wrap DRF errors in ``{"success": false, "error": {...}}``."""
    response = drf_exception_handler(exc, context)

    if response is None:
        view = context.get("view")
        logger.exception(
            "unhandled_error",
            view=view.__class__.__name__ if view is not None else None,
            error=str(exc),
        )
        return Response(
            {
                "success": False,
                "data": None,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "details": [],
                },
            },
            status=500,
        )

    message, details = _details_from(response.data)
    response.data = {
        "success": False,
        "data": None,
        "error": {
            "code": _CODE_BY_STATUS.get(response.status_code, "ERROR"),
            "message": message,
            "details": details,
        },
    }
    return response
