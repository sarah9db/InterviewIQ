from interview_agents.agents.gmail_agent import _is_sender_blocked, is_interview_email
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
    text = "Please let us know your availability for a screening call."
    assert not is_interview_email(parsed, text)


def test_rejects_blocklisted_sender_exact_email() -> None:
    parsed = EmailInfo(
        company="Google",
        role="Software Engineer",
        sender_email="noreply@linkedin.com",
        meeting_link="https://meet.google.com/abc",
    )
    text = "Congratulations! We would like to invite you to interview for next steps."
    assert not is_interview_email(parsed, text)


def test_rejects_blocklisted_sender_domain_match() -> None:
    parsed = EmailInfo(
        company="Google",
        role="Software Engineer",
        sender_email="alerts@mail.indeed.com",
        meeting_link="https://meet.google.com/abc",
    )
    text = "Congratulations! We would like to invite you to interview for next steps."
    assert not is_interview_email(parsed, text)


def test_rejects_new_negative_signal_keywords() -> None:
    parsed = EmailInfo(company="Acme", role="Engineer")
    text = "Job alert: recommended jobs and daily digest of job opportunities for you."
    assert not is_interview_email(parsed, text)


def test_accepts_legitimate_sender_with_strong_signal() -> None:
    parsed = EmailInfo(
        company="Acme",
        role="Data Engineer",
        sender_email="recruiter@acme.com",
    )
    text = "Congratulations! We would like to invite you to interview for next steps."
    assert is_interview_email(parsed, text)


def test_is_sender_blocked_exact_match() -> None:
    assert _is_sender_blocked("noreply@linkedin.com")
    assert _is_sender_blocked("NOREPLY@LINKEDIN.COM")


def test_is_sender_blocked_domain_match() -> None:
    assert _is_sender_blocked("alerts@indeed.com")
    assert _is_sender_blocked("alerts@mail.indeed.com")
    assert not _is_sender_blocked("alerts@notindeed.com")


def test_is_sender_blocked_none() -> None:
    assert not _is_sender_blocked(None)
    assert not _is_sender_blocked("")
