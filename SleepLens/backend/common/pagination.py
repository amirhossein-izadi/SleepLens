"""Standard pagination for list endpoints (``?page=&limit=``)."""

from __future__ import annotations

from math import ceil
from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """Page-number pagination that emits the standard ``metadata`` block."""

    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100

    def get_paginated_response(self, data: list[Any]) -> Response:
        page_size = self.get_page_size(self.request) or self.page_size
        total = self.page.paginator.count
        return Response(
            {
                "success": True,
                "data": data,
                "metadata": {
                    "total": total,
                    "page": self.page.number,
                    "limit": page_size,
                    "pages": ceil(total / page_size) if page_size else 1,
                },
            }
        )
