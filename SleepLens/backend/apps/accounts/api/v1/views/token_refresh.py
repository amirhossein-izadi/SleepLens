"""Token refresh view — body or cookie refresh token, rotated with cookies."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.api.v1.utils.auth_cookies import get_refresh_token, set_jwt_cookies


class TokenRefreshRequestSerializer(serializers.Serializer):
    """Request body for the refresh endpoint."""

    refresh = serializers.CharField(required=False, allow_blank=True)


class TokenRefreshView(APIView):
    """Exchange a refresh token for a new access token."""

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="accounts_token_refresh",
        summary="Refresh the access token",
        tags=["Accounts"],
        request=TokenRefreshRequestSerializer,
    )
    def post(self, request: Request) -> Response:
        refresh_str = get_refresh_token(request)
        if not refresh_str:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "No refresh token provided.",
                        "details": [],
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(refresh_str)
            access = str(refresh.access_token)
        except Exception:  # noqa: BLE001 - invalid/expired/blacklisted token
            return Response(
                {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired refresh token.",
                        "details": [],
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = {"access": access, "refresh": refresh_str}
        response = Response(tokens)
        return set_jwt_cookies(response, access, refresh_str)
