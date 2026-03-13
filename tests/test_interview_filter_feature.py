from __future__ import annotations

from interview_agents.agents.gmail_agent import is_interview_email
from interview_agents.agents.sheet_agent import write_sheet_node
from interview_agents.models import EmailInfo


class FakeSheetsClient:
    def __init__(self, exists: bool = False) -> None:
        self.exists = exists
        self.ensure_headers_called = False
        self.append_called = False

    def ensure_headers(self) -> None:
        self.ensure_headers_called = True

    def row_exists(self, row_id: str) -> bool:
        return self.exists

    def append_email(self, email: EmailInfo, message_id: str | None = None) -> str:
        self.append_called = True
        return message_id or "fake-row-id"


def test_strict_filter_rejects_weak_keyword_noise() -> None:
    parsed = EmailInfo(company="Acme", role="Engineer")
    email_text = "Thanks for reading our newsletter and product updates."
    assert not is_interview_email(parsed, email_text).accepted


def test_write_sheet_appends_for_strong_interview_signal(monkeypatch) -> None:
    fake = FakeSheetsClient(exists=False)
    monkeypatch.setattr("interview_agents.agents.sheet_agent.SheetsClient", lambda: fake)
    monkeypatch.setattr("interview_agents.agents.sheet_agent.log_filter_result", lambda r: None)
    monkeypatch.setattr("interview_agents.agents.sheet_agent.settings", type("S", (), {"filter_log_sheet_enabled": False})())

    state = {
        "gmail_message_id": "msg-1",
        "email_raw": "We'd like to invite you to a technical interview next steps.",
        "parsed_email": EmailInfo(
            company="Acme",
            role="Backend Engineer",
            interview_datetime="2026-03-01T18:00:00+00:00",
        ),
    }

    result = write_sheet_node(state)

    assert fake.ensure_headers_called
    assert fake.append_called
    assert result["row_id"] == "msg-1"
    assert not result["filtered_out"]


def test_write_sheet_marks_duplicate(monkeypatch) -> None:
    fake = FakeSheetsClient(exists=True)
    monkeypatch.setattr("interview_agents.agents.sheet_agent.SheetsClient", lambda: fake)
    monkeypatch.setattr("interview_agents.agents.sheet_agent.log_filter_result", lambda r: None)
    monkeypatch.setattr("interview_agents.agents.sheet_agent.settings", type("S", (), {"filter_log_sheet_enabled": False})())

    state = {
        "gmail_message_id": "msg-dup",
        "email_raw": "We would like to invite you for an interview.",
        "parsed_email": EmailInfo(
            company="Acme",
            role="Backend Engineer",
            meeting_link="https://meet.google.com/abc-defg-hij",
        ),
    }

    result = write_sheet_node(state)

    assert fake.ensure_headers_called
    assert not fake.append_called
    assert result["row_id"] == "msg-dup"
    assert result["duplicate"]


def test_write_sheet_filters_out_non_interview(monkeypatch) -> None:
    fake = FakeSheetsClient(exists=False)
    monkeypatch.setattr("interview_agents.agents.sheet_agent.SheetsClient", lambda: fake)
    monkeypatch.setattr("interview_agents.agents.sheet_agent.log_filter_result", lambda r: None)
    monkeypatch.setattr("interview_agents.agents.sheet_agent.settings", type("S", (), {"filter_log_sheet_enabled": False})())

    state = {
        "gmail_message_id": "msg-nope",
        "email_raw": "Monthly marketing newsletter. Unsubscribe here.",
        "parsed_email": EmailInfo(company="Acme", role="Engineer"),
    }

    result = write_sheet_node(state)

    assert fake.ensure_headers_called
    assert not fake.append_called
    assert result["row_id"] == ""
    assert result["filtered_out"]
