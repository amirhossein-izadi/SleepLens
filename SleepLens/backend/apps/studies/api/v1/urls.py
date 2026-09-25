"""Studies API v1 URL configuration."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.studies.api.v1.views.study import StudyViewSet

app_name = "v1"

router = DefaultRouter()
router.register(r"", StudyViewSet, basename="studies")

urlpatterns = [
    path("", include(router.urls)),
]
