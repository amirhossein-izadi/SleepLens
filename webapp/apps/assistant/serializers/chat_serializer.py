"""
Chat serializers for SleepLens Assistant.
Adheres to backend_coding_guidelines/03_DJANGO_PATTERNS.md
"""

from rest_framework import serializers
from apps.assistant.models.chat_session import ChatSession
from apps.assistant.models.chat_message import ChatMessage, ChatSender

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_display = serializers.CharField(source="get_sender_display", read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "session_id",
            "sender",
            "sender_display",
            "content",
            "prompt_tokens",
            "completion_tokens",
            "created_at",
        ]
        read_only_fields = fields

class ChatMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(required=True, min_length=1, max_length=4000)

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "study_id",
            "physician_id",
            "opencode_session_id",
            "title",
            "created_at",
            "updated_at",
            "messages",
        ]
        read_only_fields = fields
