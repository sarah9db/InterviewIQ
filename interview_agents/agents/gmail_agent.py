from __future__ import annotations

import re

from interview_agents.config.settings import filter_config
from interview_agents.models import EmailInfo
from interview_agents.tools.llm_utils import extract_json_object, make_llm


llm = make_llm()


def _is_sender_blocked(sender_email: str | None) -> bool:
    if not sender_email:
        return False
    email_lower = sender_email.strip().lower()
    blocked_emails = {e.lower() for e in filter_config.blocked_sender_emails}
    if email_lower in blocked_emails:
        return True
    domain = email_lower.rsplit("@", 1)[-1] if "@" in email_lower else ""
    blocked_domains = {d.lower() for d in filter_config.blocked_sender_domains}
    return any(domain == d or domain.endswith("." + d) for d in blocked_domains)


def parse_email_node(state: dict) -> dict:
    email_text = state.get("email_raw", "")
    message_id = state.get("gmail_message_id")

    prompt = f"""
You parse job interview emails.

Return STRICT JSON only with these keys:
sender_name, sender_email, company, role,
meeting_link, interview_datetime, subject, snippet.

Rules:
- If the email is not clearly interview-related, set company and role to null.
- Do not infer company/role from guesses. Use only explicit evidence from the email text.
- interview_datetime should be ISO-8601 when possible.
- snippet should be 1-2 concise sentences.
- You MUST set company and role to null for any of these categories:
  * Automated job alerts (e.g. "jobs you might like", "new jobs for you", "recommended jobs")
  * Newsletters or daily/weekly digests
  * Mass mailings, marketing emails, or promotional content
  * Job board notifications from sites like LinkedIn, Indeed, Glassdoor, ZipRecruiter, Dice, or Monster
  * Non-personal communications (bulk "noreply@" senders, unsubscribe links present)

Examples of emails where company and role MUST be null:
- "Your daily job alert: 15 new Data Engineer jobs in San Francisco. View all jobs. Unsubscribe."
- "Hi, here are your top picks this week: Software Engineer at Acme, Backend Dev at WidgetCo..."
- "New jobs for you: 3 roles match your profile. Apply now on Indeed."
- "This week in tech hiring — our newsletter with tips and featured roles."

Email:
{email_text}
""".strip()

    response = llm.invoke(prompt)
    try:
        payload = extract_json_object(response)
        parsed = EmailInfo(**payload)
    except Exception:
        # Fail closed: treat unparsable output as non-interview so pipeline continues.
        parsed = EmailInfo(company=None, role=None, snippet="LLM parse failed for this email.")
    if message_id:
        parsed.gmail_message_id = message_id
    return {"parsed_email": parsed}


def _contains_any(text: str, phrases: list[str] | tuple[str, ...]) -> bool:
    return any(p in text for p in phrases)


def is_interview_email(parsed: EmailInfo, email_text: str = "") -> bool:
    text = re.sub(r"\s+", " ", (email_text or "").lower()).strip()
    sc = filter_config.scoring

    has_company_role = bool(parsed.company and parsed.role)
    has_strong_phrase = _contains_any(text, filter_config.strong_positive_phrases)
    has_context_term = _contains_any(text, filter_config.interview_context_terms)
    has_meeting_signal = bool(parsed.meeting_link or parsed.interview_datetime) or _contains_any(
        text, filter_config.meeting_hints
    )
    has_negative_signal = _contains_any(text, filter_config.negative_signals)
    is_blocked_sender = _is_sender_blocked(parsed.sender_email)

    score = 0
    if has_company_role:
        score += sc.company_role_weight
    if has_strong_phrase:
        score += sc.strong_phrase_weight
    if has_context_term:
        score += sc.context_term_weight
    if has_meeting_signal:
        score += sc.meeting_signal_weight
    if has_negative_signal:
        score -= sc.negative_signal_penalty
    if is_blocked_sender:
        score -= sc.blocked_sender_penalty

    # Require at least one strong confirmation path to avoid keyword-only noise.
    strong_confirmation = has_strong_phrase or has_meeting_signal
    if sc.require_strong_confirmation:
        return bool(score >= sc.threshold and strong_confirmation)
    return bool(score >= sc.threshold)
