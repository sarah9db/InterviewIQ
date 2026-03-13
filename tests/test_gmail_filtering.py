from interview_agents.agents.gmail_agent import _is_sender_blocked, is_interview_email
from interview_agents.models import EmailInfo


def test_accepts_strong_invite_phrase() -> None:
    parsed = EmailInfo(company="Acme", role="Data Engineer")
    text = "Congratulations! We'd like to invite you to interview for next steps."
    result = is_interview_email(parsed, text)
    assert result.accepted
    assert result.score >= 4
    assert result.strong_phrase_points > 0
    assert len(result.matched_strong_phrases) > 0


def test_accepts_meeting_signal_without_phrase() -> None:
    parsed = EmailInfo(
        company="Acme",
        role="Data Engineer",
        meeting_link="https://meet.google.com/abc-defg-hij",
    )
    text = "Please join the call at the link above."
    result = is_interview_email(parsed, text)
    assert result.accepted
    assert result.meeting_signal_points > 0


def test_rejects_keyword_only_marketing_noise() -> None:
    parsed = EmailInfo(company="Acme", role="Engineer")
    text = "Interview tips newsletter. Unsubscribe for promotions and discounts."
    result = is_interview_email(parsed, text)
    assert not result.accepted
    assert result.negative_signal_points > 0
    assert len(result.matched_negative_signals) > 0


def test_rejects_when_company_role_missing() -> None:
    parsed = EmailInfo(company=None, role=None)
    text = "Please let us know your availability for a screening call."
    result = is_interview_email(parsed, text)
    assert not result.accepted
    assert result.company_role_points == 0


def test_rejects_blocklisted_sender_exact_email() -> None:
    parsed = EmailInfo(
        company="Google",
        role="Software Engineer",
        sender_email="noreply@linkedin.com",
        meeting_link="https://meet.google.com/abc",
    )
    text = "Congratulations! We would like to invite you to interview for next steps."
    result = is_interview_email(parsed, text)
    assert not result.accepted
    assert result.rejection_reason == "blocked sender"
    assert result.blocked_sender_points > 0


def test_rejects_blocklisted_sender_domain_match() -> None:
    parsed = EmailInfo(
        company="Google",
        role="Software Engineer",
        sender_email="alerts@mail.indeed.com",
        meeting_link="https://meet.google.com/abc",
    )
    text = "Congratulations! We would like to invite you to interview for next steps."
    result = is_interview_email(parsed, text)
    assert not result.accepted
    assert result.rejection_reason == "blocked sender"


def test_rejects_new_negative_signal_keywords() -> None:
    parsed = EmailInfo(company="Acme", role="Engineer")
    text = "Job alert: recommended jobs and daily digest of job opportunities for you."
    result = is_interview_email(parsed, text)
    assert not result.accepted
    assert len(result.matched_negative_signals) > 0


def test_accepts_legitimate_sender_with_strong_signal() -> None:
    parsed = EmailInfo(
        company="Acme",
        role="Data Engineer",
        sender_email="recruiter@acme.com",
    )
    text = "Congratulations! We would like to invite you to interview for next steps."
    result = is_interview_email(parsed, text)
    assert result.accepted
    assert result.rejection_reason is None


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


def test_filter_result_has_timestamp() -> None:
    parsed = EmailInfo(company="Acme", role="Engineer")
    text = "Congratulations! We'd like to invite you to interview."
    result = is_interview_email(parsed, text)
    assert result.timestamp != ""


def test_filter_result_score_breakdown() -> None:
    parsed = EmailInfo(
        company="Acme",
        role="Engineer",
        meeting_link="https://zoom.us/j/123",
    )
    text = "Congratulations! We'd like to invite you to interview for the role."
    result = is_interview_email(parsed, text)
    assert result.company_role_points == 2
    assert result.strong_phrase_points == 3
    assert result.meeting_signal_points == 2
    expected_score = (
        result.company_role_points
        + result.strong_phrase_points
        + result.context_term_points
        + result.meeting_signal_points
        - result.negative_signal_points
        - result.blocked_sender_points
    )
    assert result.score == expected_score
