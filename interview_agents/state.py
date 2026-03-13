from __future__ import annotations

from typing import TypedDict

from interview_agents.models import EmailInfo, FilterResult


class GraphState(TypedDict, total=False):
    email_raw: str
    gmail_message_id: str
    parsed_email: EmailInfo
    filter_result: FilterResult
    row_id: str
    prep_doc: str
    sms_sent: bool
    fast_rejected: bool
