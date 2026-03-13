from unittest.mock import patch

from interview_agents.agents.gmail_agent import fast_reject_node


def test_rejects_linkedin_sender() -> None:
    state = {"email_raw": "From: jobs-noreply@linkedin.com\nSubject: New opportunity\n\nHello"}
    result = fast_reject_node(state)
    assert result["fast_rejected"] is True


def test_rejects_daily_job_alert_subject() -> None:
    state = {"email_raw": "From: alerts@example.com\nSubject: Your daily job alert\n\nHello"}
    result = fast_reject_node(state)
    assert result["fast_rejected"] is True


def test_rejects_bulk_precedence_header() -> None:
    state = {"email_raw": "From: info@example.com\nSubject: Weekly update\nPrecedence: bulk\n\nHello"}
    result = fast_reject_node(state)
    assert result["fast_rejected"] is True


def test_passes_legitimate_recruiter_email() -> None:
    state = {
        "email_raw": "From: recruiter@acme.com\nSubject: Interview: Software Engineer\n\nHi, we'd like to schedule an interview."
    }
    result = fast_reject_node(state)
    assert result["fast_rejected"] is False


def test_passes_when_email_raw_empty() -> None:
    result = fast_reject_node({"email_raw": ""})
    assert result["fast_rejected"] is False


def test_passes_when_email_raw_missing() -> None:
    result = fast_reject_node({})
    assert result["fast_rejected"] is False


def test_case_insensitive_domain_check() -> None:
    state = {"email_raw": "From: alerts@LINKEDIN.COM\nSubject: Hi\n\nHello"}
    result = fast_reject_node(state)
    assert result["fast_rejected"] is True


def test_rejects_jobs_matching_subject() -> None:
    state = {"email_raw": "From: noreply@example.com\nSubject: Jobs matching your search\n\nHello"}
    result = fast_reject_node(state)
    assert result["fast_rejected"] is True


def test_rejects_new_jobs_subject() -> None:
    state = {"email_raw": "From: noreply@example.com\nSubject: 5 new jobs in San Francisco\n\nHello"}
    result = fast_reject_node(state)
    assert result["fast_rejected"] is True


def test_rejects_auto_response_suppress_header() -> None:
    state = {"email_raw": "From: bot@example.com\nSubject: Info\nX-Auto-Response-Suppress: All\n\nHello"}
    result = fast_reject_node(state)
    assert result["fast_rejected"] is True


def test_rejects_list_unsubscribe_header() -> None:
    state = {"email_raw": "From: news@example.com\nSubject: News\nList-Unsubscribe: <mailto:unsub@example.com>\n\nHello"}
    result = fast_reject_node(state)
    assert result["fast_rejected"] is True


def test_rejects_subdomain_of_blocked_domain() -> None:
    state = {"email_raw": "From: alerts@mail.indeed.com\nSubject: Hi\n\nHello"}
    result = fast_reject_node(state)
    assert result["fast_rejected"] is True


def test_integration_graph_fast_reject_skips_llm() -> None:
    """Build the real graph and verify fast_reject short-circuits before parse_email."""
    import sys
    from types import ModuleType
    from unittest.mock import MagicMock

    # Ensure twilio can be imported even if not installed.
    twilio_stub = ModuleType("twilio")
    twilio_rest = ModuleType("twilio.rest")
    twilio_rest.Client = MagicMock  # type: ignore[attr-defined]
    sys.modules.setdefault("twilio", twilio_stub)
    sys.modules.setdefault("twilio.rest", twilio_rest)

    from interview_agents.graph import build_email_graph

    app = build_email_graph()
    email_raw = "From: jobs-noreply@linkedin.com\nSubject: Your daily job alert\n\nApply now"

    with patch("interview_agents.agents.gmail_agent.llm") as mock_llm:
        result = app.invoke({"email_raw": email_raw})

    assert result.get("fast_rejected") is True
    assert "parsed_email" not in result
    mock_llm.invoke.assert_not_called()
