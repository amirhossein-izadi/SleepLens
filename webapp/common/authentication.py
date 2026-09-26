"""
Custom DRF Authentication classes for SleepLens API.
Provides CSRF-exempt session authentication for REST API endpoints consumed by SPAs.
Adheres to backend_coding_guidelines/08_API_DESIGN.md
"""

from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication without CSRF enforcement for REST API endpoints.
    Allows authenticated admin sessions from the browser to seamlessly query API endpoints.
    """
    def enforce_csrf(self, request):
        return  # Bypass CSRF validation for API requests
