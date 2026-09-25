"""Patients API v1 URL configuration."""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.patients.api.v1.views.patient import PatientViewSet

app_name = "v1"

router = DefaultRouter()
router.register(r"", PatientViewSet, basename="patients")

urlpatterns = [
    path("", include(router.urls)),
]
