from __future__ import annotations

from interview_agents.agents.gmail_agent import _is_sender_blocked, is_interview_email
from interview_agents.config.settings import FilterConfig, ScoringConfig, load_filter_config
from interview_agents.models import EmailInfo


def test_load_filter_config_defaults() -> None:
    cfg = load_filter_config()
    assert "congratulations" in cfg.strong_positive_phrases
    assert "interview" in cfg.interview_context_terms
    assert "zoom.us" in cfg.meeting_hints
    assert "unsubscribe" in cfg.negative_signals
    assert "noreply@linkedin.com" in cfg.blocked_sender_emails
    assert "indeed.com" in cfg.blocked_sender_domains
    assert cfg.scoring.threshold == 4
    assert cfg.scoring.require_strong_confirmation is True


def test_load_filter_config_override(tmp_path) -> None:
    override = tmp_path / "override.yaml"
    override.write_text(
        "negative_signals:\n"
        '  - "spam"\n'
        "scoring:\n"
        "  threshold: 10\n"
    )
    cfg = load_filter_config(override_path=str(override))
    assert cfg.negative_signals == ("spam",)
    assert cfg.scoring.threshold == 10
    # Non-overridden fields keep defaults.
    assert "congratulations" in cfg.strong_positive_phrases


def test_custom_config_changes_behavior(monkeypatch) -> None:
    custom = FilterConfig(
        strong_positive_phrases=("congratulations",),
        interview_context_terms=("interview",),
        meeting_hints=("zoom.us",),
        negative_signals=("unsubscribe",),
        blocked_sender_emails=("blocked@example.com",),
        blocked_sender_domains=("blocked.com",),
        scoring=ScoringConfig(threshold=1, require_strong_confirmation=False),
    )
    monkeypatch.setattr("interview_agents.agents.gmail_agent.filter_config", custom)

    # Low threshold + no strong confirmation required → context term alone is enough.
    parsed = EmailInfo(company="Acme", role="Engineer")
    text = "Let's schedule an interview."
    assert is_interview_email(parsed, text)


def test_custom_blocklist_via_monkeypatch(monkeypatch) -> None:
    custom = FilterConfig(
        strong_positive_phrases=("congratulations",),
        interview_context_terms=("interview",),
        meeting_hints=("zoom.us",),
        negative_signals=(),
        blocked_sender_emails=("evil@spam.com",),
        blocked_sender_domains=("spamcorp.com",),
        scoring=ScoringConfig(),
    )
    monkeypatch.setattr("interview_agents.agents.gmail_agent.filter_config", custom)

    parsed = EmailInfo(
        company="Acme",
        role="Engineer",
        sender_email="evil@spam.com",
        meeting_link="https://zoom.us/j/123",
    )
    text = "Congratulations! We'd like to invite you to interview."
    assert not is_interview_email(parsed, text)

    # Verify domain-level block.
    assert _is_sender_blocked("user@mail.spamcorp.com")
