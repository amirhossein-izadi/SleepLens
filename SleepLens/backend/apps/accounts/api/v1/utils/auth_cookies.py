"""Helpers for setting and clearing JWT httpOnly cookies.

Cookies are the primary token transport for the web frontend. They are marked
httpOnly so JavaScript cannot steal them via XSS, and SameSite=Lax to allow
normal top-level navigation while mitigating CSRF.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"


def _cookie_flags() -> dict[str, Any]:
    return {
        "httponly": True,
        "samesite": "Lax",
        "secure": getattr(settings, "SESSION_COOKIE_SECURE", False),
        "domain": getattr(settings, "SESSION_COOKIE_DOMAIN", None),
    }


def set_jwt_cookies(response: Response, access: str, refresh: str) -> Response:
    """Attach access and refresh tokens as httpOnly cookies."""
    flags = _cookie_flags()
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        access,
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        path="/",
        **flags,
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        path="/",
        **flags,
    )
    return response


def clear_jwt_cookies(response: Response) -> Response:
    """Remove JWT cookies from the response.

    ``delete_cookie`` only accepts path/domain/samesite (httponly and secure
    are not part of its signature), so the flags are filtered here.
    """
    flags = _cookie_flags()
    delete_flags = {key: value for key, value in flags.items() if key in {"domain", "samesite"}}
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/", **delete_flags)
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/", **delete_flags)
    return response


def get_refresh_token(request: Request) -> str | None:
    """Refresh token from the request body or the refresh cookie."""
    return request.data.get("refresh") or request.COOKIES.get(REFRESH_COOKIE_NAME)
