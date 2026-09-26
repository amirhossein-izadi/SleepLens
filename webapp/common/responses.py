"""
Standard API Response Envelopes.
Adheres to backend_coding_guidelines/08_API_DESIGN.md
"""

from typing import Any, Optional, Dict, List
from rest_framework.response import Response
from rest_framework import status

def api_success(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = status.HTTP_200_OK,
    metadata: Optional[Dict[str, Any]] = None
) -> Response:
    """Builds standard success response: { success: true, data: ..., message: ..., metadata?: ... }"""
    payload: Dict[str, Any] = {
        "success": True,
        "data": data,
        "message": message,
    }
    if metadata is not None:
        payload["metadata"] = metadata
    return Response(payload, status=status_code)

def api_error(
    code: str = "ERROR",
    message: str = "An error occurred",
    details: Optional[List[Dict[str, Any]]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> Response:
    """Builds standard error response: { success: false, data: null, error: { code, message, details } }"""
    return Response(
        {
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
            }
        },
        status=status_code
    )
