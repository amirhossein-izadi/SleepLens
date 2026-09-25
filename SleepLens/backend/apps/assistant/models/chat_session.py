"""ChatSession — one consultation thread per study, backed by opencode."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from common.models import BaseModel


class ChatSession(BaseModel):
    """A single assistant consultation bound to one study."""

    study = models.OneToOneField(
        "studies.Study",
        on_delete=models.CASCADE,
        related_name="chat_session",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    opencode_session_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    context_injected = models.BooleanField(default=False)

    class Meta:
        db_table = "chat_sessions"
        verbose_name = "Chat session"
        verbose_name_plural = "Chat sessions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"chat[{self.study_id}]"
