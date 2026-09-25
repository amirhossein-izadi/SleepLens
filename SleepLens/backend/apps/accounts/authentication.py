"""JWT authentication that also accepts access tokens from httpOnly cookies.

This keeps the Authorization header working for non-browser clients while
letting the web frontend store tokens in httpOnly, SameSite cookies.
"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"


class CookieJWTAuthentication(JWTAuthentication):
    """Try the Authorization header first, fall back to the access_token cookie."""

    def get_header(self, request: Request) -> bytes | None:
        header = super().get_header(request)
        if header:
            return header
        token = request.COOKIES.get(ACCESS_COOKIE_NAME)
        if token:
            return f"Bearer {token}".encode()
        return None
