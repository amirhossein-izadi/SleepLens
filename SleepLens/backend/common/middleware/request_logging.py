"""Request logging middleware with correlation IDs (structlog).

Every request gets an ``X-Correlation-ID`` (echoed in the response) and a
structured ``http_request`` log line with method, path, status and duration.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable

import structlog
from django.http import HttpRequest, HttpResponse

logger = structlog.get_logger(__name__)

CORRELATION_HEADER = "X-Correlation-ID"


class RequestLoggingMiddleware:
    """Bind a correlation id and log one structured line per request."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)

        user = getattr(request, "user", None)
        user_id: Any = getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None
        logger.info(
            "http_request",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=str(user_id) if user_id else None,
        )

        response[CORRELATION_HEADER] = correlation_id
        structlog.contextvars.clear_contextvars()
        return response
