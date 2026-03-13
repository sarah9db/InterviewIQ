"""Tests that parse_email_node handles spam-like emails correctly via mocked LLM."""

from __future__ import annotations

import json

from interview_agents.agents.gmail_agent import parse_email_node


class FakeLLM:
    """Minimal stand-in that returns a pre-set JSON string."""

    def __init__(self, response: str) -> None:
        self._response = response

    def invoke(self, prompt: str) -> str:
        return self._response


def _make_null_response(**overrides: object) -> str:
    """Return a JSON string mimicking an LLM that correctly nulls company/role."""
    base: dict = {
        "sender_name": None,
        "sender_email": overrides.get("sender_email"),
        "company": None,
        "role": None,
        "meeting_link": None,
        "interview_datetime": None,
        "subject": overrides.get("subject", "Job alert"),
        "snippet": overrides.get("snippet", "Automated job alert email."),
    }
    return json.dumps(base)


# -- Prompt content tests -----------------------------------------------------


def test_prompt_contains_spam_category_instructions(monkeypatch: object) -> None:
    """The expanded prompt must include the new spam-category rules."""
    captured: list[str] = []

    class CaptureLLM:
        def invoke(self, prompt: str) -> str:
            captured.append(prompt)
            return _make_null_response()

    monkeypatch.setattr("interview_agents.agents.gmail_agent.llm", CaptureLLM())

    parse_email_node({"email_raw": "some email text"})

    prompt = captured[0]
    assert "Automated job alerts" in prompt
    assert "Newsletters or daily/weekly digests" in prompt
    assert "Job board notifications" in prompt
    assert "Non-personal communications" in prompt
    assert "You MUST set company and role to null" in prompt


def test_prompt_contains_spam_examples(monkeypatch: object) -> None:
    """The prompt must include few-shot negative examples."""
    captured: list[str] = []

    class CaptureLLM:
        def invoke(self, prompt: str) -> str:
            captured.append(prompt)
            return _make_null_response()

    monkeypatch.setattr("interview_agents.agents.gmail_agent.llm", CaptureLLM())

    parse_email_node({"email_raw": "some email text"})

    prompt = captured[0]
    assert "Your daily job alert" in prompt
    assert "Apply now on Indeed" in prompt
    assert "newsletter with tips and featured roles" in prompt


# -- Parsing behavior tests ---------------------------------------------------


def test_parse_email_node_returns_null_company_role_for_spam(monkeypatch: object) -> None:
    """When LLM correctly returns null company/role, parsed result reflects that."""
    fake_llm = FakeLLM(_make_null_response(
        sender_email="noreply@linkedin.com",
        subject="Jobs you might like",
        snippet="15 new Data Engineer jobs in San Francisco.",
    ))
    monkeypatch.setattr("interview_agents.agents.gmail_agent.llm", fake_llm)

    result = parse_email_node({
        "email_raw": "Your daily job alert: 15 new Data Engineer jobs. Unsubscribe.",
    })

    parsed = result["parsed_email"]
    assert parsed.company is None
    assert parsed.role is None
    assert parsed.snippet is not None


def test_parse_email_node_preserves_message_id(monkeypatch: object) -> None:
    """gmail_message_id from state is attached to the parsed result."""
    fake_llm = FakeLLM(_make_null_response())
    monkeypatch.setattr("interview_agents.agents.gmail_agent.llm", fake_llm)

    result = parse_email_node({
        "email_raw": "some spam",
        "gmail_message_id": "msg-spam-1",
    })

    assert result["parsed_email"].gmail_message_id == "msg-spam-1"


def test_parse_email_node_handles_malformed_llm_output(monkeypatch: object) -> None:
    """Malformed LLM output should fail closed with null company/role."""
    fake_llm = FakeLLM("This is not valid JSON at all!!!")
    monkeypatch.setattr("interview_agents.agents.gmail_agent.llm", fake_llm)

    result = parse_email_node({"email_raw": "anything"})

    parsed = result["parsed_email"]
    assert parsed.company is None
    assert parsed.role is None
