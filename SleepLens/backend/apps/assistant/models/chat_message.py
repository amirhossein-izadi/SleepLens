"""ChatMessage — one turn in a consultation thread."""

from __future__ import annotations

from django.db import models

from common.models import BaseModel


class ChatSender(models.TextChoices):
    """Who produced a message."""

    SYSTEM = "system", "System"
    USER = "user", "User (expert)"
    ASSISTANT = "assistant", "Assistant"


class ChatMessage(BaseModel):
    """A persisted turn (system context, expert question, or assistant reply)."""

    session = models.ForeignKey(
        "assistant.ChatSession",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.CharField(max_length=10, choices=ChatSender.choices)
    content = models.TextField()

    class Meta:
        db_table = "chat_messages"
        verbose_name = "Chat message"
        verbose_name_plural = "Chat messages"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["session", "created_at"])]

    def __str__(self) -> str:
        return f"{self.sender}@{self.session_id}"
