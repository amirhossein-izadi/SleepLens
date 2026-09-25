"""Assistant API v1 URL configuration.

Mounted by the root urls as ``api/v1/studies/<uuid:study_id>/chat/`` so the
``study_id`` kwarg flows into these views.
"""

from __future__ import annotations

from django.urls import path

from apps.assistant.api.v1.views.chat import (
    ChatMessageView,
    ChatView,
    SuggestedPromptsView,
)

app_name = "v1"

urlpatterns = [
    path("", ChatView.as_view(), name="chat"),
    path("messages/", ChatMessageView.as_view(), name="chat-messages"),
    path("suggested-prompts/", SuggestedPromptsView.as_view(), name="chat-prompts"),
]
