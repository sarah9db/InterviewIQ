from __future__ import annotations

import re

from interview_agents.config.settings import settings
from interview_agents.models import EmailInfo
from interview_agents.tools.llm_utils import extract_json_object, make_llm


llm = make_llm()


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


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(p in text for p in phrases)


def is_interview_email(parsed: EmailInfo, email_text: str = "") -> bool:
    text = re.sub(r"\s+", " ", (email_text or "").lower()).strip()

    has_company_role = bool(parsed.company and parsed.role)
    has_strong_phrase = _contains_any(text, settings.strong_positive_phrases)
    has_context_term = _contains_any(text, settings.interview_context_terms)
    has_meeting_signal = bool(parsed.meeting_link or parsed.interview_datetime) or _contains_any(
        text, settings.meeting_hints
    )
    has_negative_signal = _contains_any(text, settings.negative_signals)

    score = 0
    if has_company_role:
        score += 2
    if has_strong_phrase:
        score += 3
    if has_context_term:
        score += 1
    if has_meeting_signal:
        score += 2
    if has_negative_signal:
        score -= 2

    # Require company+role and at least one strong signal to avoid noise.
    strong_confirmation = has_strong_phrase or has_meeting_signal
    return bool(score >= 4 and strong_confirmation and has_company_role)
