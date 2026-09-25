"""Root URL configuration for SleepLens.

All app URLs are versioned under /api/v1/. The health endpoint lives at
/api/health/ for load-balancer probes (no auth required).
"""

from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from common.health import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # ── v1 API ────────────────────────────────────────────────────────────────
    path("api/v1/accounts/", include("apps.accounts.api.urls")),
    path("api/v1/patients/", include("apps.patients.api.urls")),
    path("api/v1/studies/", include("apps.studies.api.urls")),
    path("api/v1/studies/<uuid:study_id>/chat/", include("apps.assistant.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
