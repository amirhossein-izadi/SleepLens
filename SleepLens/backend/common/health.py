"""Health-check endpoint for load balancers and Docker healthchecks."""

from __future__ import annotations

from typing import Any

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


def _check_database() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:  # noqa: BLE001 - health probe must never raise
        return False


def _check_cache() -> bool:
    try:
        cache.set("_health", "ok", 10)
        return cache.get("_health") == "ok"
    except Exception:  # noqa: BLE001
        return False


@require_GET
def health(request: Any) -> JsonResponse:
    checks = {"database": _check_database(), "cache": _check_cache()}
    healthy = all(checks.values())
    return JsonResponse(
        {"status": "healthy" if healthy else "unhealthy", "checks": checks},
        status=200 if healthy else 503,
    )
