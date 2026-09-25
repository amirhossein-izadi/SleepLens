"""Current-user view."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.v1.serializers.user import UserSerializer


class MeView(APIView):
    """Return the authenticated user's account data."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="accounts_me",
        summary="Get the current user",
        tags=["Accounts"],
        responses={200: UserSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)
