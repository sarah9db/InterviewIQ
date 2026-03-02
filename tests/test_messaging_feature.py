from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from interview_agents.agents.sms_agent import sms_node
from interview_agents.tools.twilio_client import TwilioSMSClient


class FakeTwilioMessages:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def create(self, to: str, from_: str, body: str):
        self.calls.append({"to": to, "from_": from_, "body": body})
        return SimpleNamespace(sid="SM123")


class FakeTwilioClient:
    def __init__(self, *_args, **_kwargs) -> None:
        self.messages = FakeTwilioMessages()


def test_twilio_client_prefers_whatsapp_when_configured(monkeypatch) -> None:
    fake_settings = SimpleNamespace(
        twilio_account_sid="ACxxx",
        twilio_auth_token="token",
        twilio_whatsapp_from="+14155238886",
        twilio_whatsapp_to="+15557654321",
        twilio_from_number="+15550001111",
        twilio_to_number="+15550002222",
    )
    monkeypatch.setattr("interview_agents.tools.twilio_client.settings", fake_settings)
    monkeypatch.setattr("interview_agents.tools.twilio_client.Client", FakeTwilioClient)

    client = TwilioSMSClient()
    sid = client.send("hello")

    assert sid == "SM123"
    assert client.client.messages.calls[0]["to"] == "whatsapp:+15557654321"
    assert client.client.messages.calls[0]["from_"] == "whatsapp:+14155238886"


def test_twilio_client_falls_back_to_sms(monkeypatch) -> None:
    fake_settings = SimpleNamespace(
        twilio_account_sid="ACxxx",
        twilio_auth_token="token",
        twilio_whatsapp_from="",
        twilio_whatsapp_to="",
        twilio_from_number="+15550001111",
        twilio_to_number="+15550002222",
    )
    monkeypatch.setattr("interview_agents.tools.twilio_client.settings", fake_settings)
    monkeypatch.setattr("interview_agents.tools.twilio_client.Client", FakeTwilioClient)

    client = TwilioSMSClient()
    client.send("hello")

    assert client.client.messages.calls[0]["to"] == "+15550002222"
    assert client.client.messages.calls[0]["from_"] == "+15550001111"


def test_sms_node_sends_when_recent_rows_exist(monkeypatch) -> None:
    sent_bodies: list[str] = []
    save_calls = 0

    class FakeSheetsClient:
        def get_recent_rows(self, hours: int = 24):
            assert hours == 24
            return [
                {
                    "role": "ML Engineer",
                    "company": "Acme",
                    "interview_datetime": "2026-03-01T18:00:00+00:00",
                    "meeting_link": "https://meet.google.com/abc",
                    "prep_doc": "# Prep",
                }
            ]

        def get_rows_since(self, since: datetime):
            return []

    class FakeRunStateStore:
        def load_last_sms_run(self):
            return None

        def save_last_sms_run(self, _dt=None):
            nonlocal save_calls
            save_calls += 1

    class FakeTwilioSMSClient:
        def send(self, body: str) -> str:
            sent_bodies.append(body)
            return "SM123"

    monkeypatch.setattr("interview_agents.agents.sms_agent.SheetsClient", FakeSheetsClient)
    monkeypatch.setattr("interview_agents.agents.sms_agent.RunStateStore", FakeRunStateStore)
    monkeypatch.setattr("interview_agents.agents.sms_agent.TwilioSMSClient", FakeTwilioSMSClient)

    result = sms_node({})

    assert result == {"sms_sent": True}
    assert len(sent_bodies) == 1
    assert "Today's interview updates:" in sent_bodies[0]
    assert save_calls == 1


def test_sms_node_does_not_send_when_no_rows(monkeypatch) -> None:
    send_calls = 0
    save_calls = 0

    class FakeSheetsClient:
        def get_recent_rows(self, hours: int = 24):
            return []

        def get_rows_since(self, since: datetime):
            return []

    class FakeRunStateStore:
        def load_last_sms_run(self):
            return datetime.now(timezone.utc)

        def save_last_sms_run(self, _dt=None):
            nonlocal save_calls
            save_calls += 1

    class FakeTwilioSMSClient:
        def send(self, body: str) -> str:
            nonlocal send_calls
            send_calls += 1
            return "SM123"

    monkeypatch.setattr("interview_agents.agents.sms_agent.SheetsClient", FakeSheetsClient)
    monkeypatch.setattr("interview_agents.agents.sms_agent.RunStateStore", FakeRunStateStore)
    monkeypatch.setattr("interview_agents.agents.sms_agent.TwilioSMSClient", FakeTwilioSMSClient)

    result = sms_node({})

    assert result == {"sms_sent": False}
    assert send_calls == 0
    assert save_calls == 1
