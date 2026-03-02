from __future__ import annotations

from typing import TypedDict

from interview_agents.models import EmailInfo


class GraphState(TypedDict, total=False):
    email_raw: str
    gmail_message_id: str
    parsed_email: EmailInfo
    row_id: str
    prep_doc: str
    sms_sent: bool
