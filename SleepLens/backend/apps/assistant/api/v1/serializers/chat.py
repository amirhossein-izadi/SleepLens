"""Chat serializers."""

from __future__ import annotations

from rest_framework import serializers

from apps.assistant.models import ChatMessage, ChatSession


class ChatSessionSerializer(serializers.ModelSerializer):
    """Consultation session metadata."""

    class Meta:
        model = ChatSession
        fields = ["id", "title", "context_injected", "created_at", "updated_at"]
        read_only_fields = fields


class ChatMessageSerializer(serializers.ModelSerializer):
    """One chat turn."""

    class Meta:
        model = ChatMessage
        fields = ["id", "sender", "content", "created_at"]
        read_only_fields = fields


class ChatMessageCreateSerializer(serializers.Serializer):
    """Expert question body."""

    content = serializers.CharField(min_length=1, max_length=4000)
