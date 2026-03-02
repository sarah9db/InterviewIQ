from interview_agents.agents.gmail_agent import is_interview_email
from interview_agents.models import EmailInfo


def test_accepts_strong_invite_phrase() -> None:
    parsed = EmailInfo(company="Acme", role="Data Engineer")
    text = "Congratulations! We'd like to invite you to interview for next steps."
    assert is_interview_email(parsed, text)


def test_accepts_meeting_signal_without_phrase() -> None:
    parsed = EmailInfo(
        company="Acme",
        role="Data Engineer",
        meeting_link="https://meet.google.com/abc-defg-hij",
    )
    text = "Please join the call at the link above."
    assert is_interview_email(parsed, text)


def test_rejects_keyword_only_marketing_noise() -> None:
    parsed = EmailInfo(company="Acme", role="Engineer")
    text = "Interview tips newsletter. Unsubscribe for promotions and discounts."
    assert not is_interview_email(parsed, text)


def test_rejects_when_company_role_missing() -> None:
    parsed = EmailInfo(company=None, role=None)
    text = "We would like to invite you to interview."
    assert not is_interview_email(parsed, text)
