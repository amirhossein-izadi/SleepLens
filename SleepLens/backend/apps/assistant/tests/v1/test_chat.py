"""API tests for the opencode-backed consultation chat."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.assistant.models import ChatMessage, ChatSession
from apps.studies.models import NightFeatures, Study

pytestmark = pytest.mark.django_db


class FakeOpenCodeClient:
    """Stand-in for the opencode server (no network)."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    def is_available(self) -> bool:
        return True

    def create_session(self, title: str) -> str:
        return "oc-session-1"

    def send_message(self, session_id: str, text: str) -> str:
        return "Mocked assistant reply."

    def delete_session(self, session_id: str) -> None:
        return None


class UnavailableOpenCodeClient(FakeOpenCodeClient):
    def is_available(self) -> bool:
        return False


@pytest.fixture(autouse=True)
def fake_opencode(monkeypatch):
    monkeypatch.setattr(
        "apps.assistant.services.chat_service.OpenCodeClient", FakeOpenCodeClient
    )


@pytest.fixture
def study_with_data(user):
    study = Study.objects.create(
        user=user,
        file="studies/chat.edf",
        original_filename="chat.edf",
        file_size=10,
        summary={"needs_review_pct": 15.96, "staging_system": "ensemble"},
    )
    NightFeatures.objects.create(
        study=study,
        values={"se_pct": 72.0, "n3_pct_tst": 8.0, "sfi": 20.0, "sdi_rb": 0.4},
        not_assessable=[{"key": "apnea_index", "reason": "no airflow channel"}],
    )
    return study


class TestChatSession:
    def test_post_creates_session_with_honest_context(self, authenticated_client, study_with_data):
        url = reverse("studies_api:v1:studies-chat", args=[study_with_data.id])
        response = authenticated_client.post(url, {}, format="json")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["available"] is True
        assert data["session"]["context_injected"] is True
        system_messages = [m for m in data["messages"] if m["sender"] == "system"]
        assert system_messages
        context = system_messages[0]["content"]
        assert "Case data" in context
        assert "not_assessable" in context
        assert "never invent" in context

    def test_second_post_reuses_the_session(self, authenticated_client, study_with_data):
        url = reverse("studies_api:v1:studies-chat", args=[study_with_data.id])
        first = authenticated_client.post(url, {}, format="json").json()["data"]["session"]["id"]
        second = authenticated_client.post(url, {}, format="json").json()["data"]["session"]["id"]
        assert first == second
        assert ChatSession.objects.filter(study=study_with_data).count() == 1

    def test_get_returns_history(self, authenticated_client, study_with_data):
        url = reverse("studies_api:v1:studies-chat", args=[study_with_data.id])
        authenticated_client.post(url, {}, format="json")
        data = authenticated_client.get(url).json()["data"]
        assert [m["sender"] for m in data["messages"]] == ["system"]

    def test_send_message_roundtrip(self, authenticated_client, study_with_data):
        url = reverse("studies_api:v1:studies-chat-messages", args=[study_with_data.id])
        response = authenticated_client.post(
            url, {"content": "Why is N3 low?"}, format="json"
        )
        assert response.status_code == 201
        message = response.json()["data"]
        assert message["sender"] == "assistant"
        assert message["content"] == "Mocked assistant reply."
        senders = list(
            ChatMessage.objects.filter(session__study=study_with_data).values_list("sender", flat=True)
        )
        assert senders == ["system", "user", "assistant"]

    def test_unavailable_returns_503(self, authenticated_client, study_with_data, monkeypatch):
        monkeypatch.setattr(
            "apps.assistant.services.chat_service.OpenCodeClient", UnavailableOpenCodeClient
        )
        url = reverse("studies_api:v1:studies-chat", args=[study_with_data.id])
        response = authenticated_client.post(url, {}, format="json")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "OPENCODE_UNAVAILABLE"
        assert not ChatSession.objects.exists()

    def test_suggested_prompts_from_data(self, authenticated_client, study_with_data):
        url = reverse("studies_api:v1:studies-chat-suggestions", args=[study_with_data.id])
        prompts = authenticated_client.get(url).json()["data"]["prompts"]
        joined = " ".join(prompts).lower()
        assert "efficiency" in joined
        assert "deep (n3)" in joined
        assert "fragmentation" in joined
        assert len(prompts) <= 4

    def test_delete_resets_session(self, authenticated_client, study_with_data):
        url = reverse("studies_api:v1:studies-chat", args=[study_with_data.id])
        authenticated_client.post(url, {}, format="json")
        response = authenticated_client.delete(url)
        assert response.status_code == 200
        assert response.json()["data"]["available"] is False
        assert not ChatSession.objects.exists()

    def test_foreign_study_is_404(self, authenticated_client):
        from apps.accounts.services.auth_service import UserService

        stranger = UserService.create_user(
            email="chatstranger@example.com", password="strangerpass1", full_name="S"
        )
        foreign = Study.objects.create(
            user=stranger, file="studies/f.edf", original_filename="f.edf", file_size=1
        )
        url = reverse("studies_api:v1:studies-chat", args=[foreign.id])
        assert authenticated_client.post(url, {}, format="json").status_code == 404
