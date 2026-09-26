"""
API v1 URL Router for SleepLens.
Adheres to backend_coding_guidelines/08_API_DESIGN.md
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.patients.views.patient_views import PatientViewSet
from apps.studies.views.study_views import StudyViewSet
from apps.hypnograms.views.hypnogram_views import HypnogramViewSet
from apps.metrics.views.metric_views import MetricViewSet
from apps.reports.views.report_views import ReportViewSet
from apps.assistant.views.chat_views import ChatViewSet

router = DefaultRouter()
router.register("patients", PatientViewSet, basename="patient")
router.register("studies", StudyViewSet, basename="study")
router.register("studies", HypnogramViewSet, basename="study-hypnogram")
router.register("studies", MetricViewSet, basename="study-metric")
router.register("studies", ReportViewSet, basename="study-report")
router.register("studies", ChatViewSet, basename="study-chat")
router.register("metrics", MetricViewSet, basename="metric")

urlpatterns = [
    path("", include(router.urls)),
]
