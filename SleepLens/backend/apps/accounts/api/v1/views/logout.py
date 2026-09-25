"""Logout view — blacklists the refresh token and clears cookies."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.api.v1.utils.auth_cookies import (
    clear_jwt_cookies,
    get_refresh_token,
)


class LogoutView(APIView):
    """Invalidate the refresh token (best effort) and clear cookies."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="accounts_logout",
        summary="Log out and blacklist the refresh token",
        tags=["Accounts"],
    )
    def post(self, request: Request) -> Response:
        refresh = get_refresh_token(request)
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass
        response = Response({"detail": "Logged out."})
        return clear_jwt_cookies(response)
