"""Authentication views: register and login."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.api.v1.serializers.login import LoginSerializer
from apps.accounts.api.v1.serializers.register import RegisterSerializer
from apps.accounts.api.v1.serializers.user import UserSerializer
from apps.accounts.api.v1.utils.auth_cookies import set_jwt_cookies


class RegisterThrottle(AnonRateThrottle):
    rate = "3/hour"


class LoginThrottle(AnonRateThrottle):
    rate = "10/minute"


def _token_payload(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(APIView):
    """Create an account and return tokens."""

    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    @extend_schema(
        operation_id="accounts_register",
        summary="Register a new user",
        tags=["Accounts"],
        request=RegisterSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        tokens = _token_payload(user)
        response = Response(
            {"user": UserSerializer(user).data, "tokens": tokens},
            status=status.HTTP_201_CREATED,
        )
        return set_jwt_cookies(response, tokens["access"], tokens["refresh"])


class LoginView(APIView):
    """Authenticate and return tokens."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(
        operation_id="accounts_login",
        summary="Log in with email and password",
        tags=["Accounts"],
        request=LoginSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        tokens = _token_payload(user)
        response = Response({"user": UserSerializer(user).data, "tokens": tokens})
        return set_jwt_cookies(response, tokens["access"], tokens["refresh"])
