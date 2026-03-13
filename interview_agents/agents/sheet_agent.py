from __future__ import annotations

from interview_agents.agents.gmail_agent import is_interview_email
from interview_agents.models import EmailInfo
from interview_agents.tools.filter_logger import log_filter_result
from interview_agents.tools.sheets_client import SheetsClient


def write_sheet_node(state: dict) -> dict:
    parsed: EmailInfo = state["parsed_email"]
    message_id = state.get("gmail_message_id") or parsed.gmail_message_id
    sheets = SheetsClient()
    sheets.ensure_headers()

    result = is_interview_email(parsed, state.get("email_raw", ""))
    log_filter_result(result)

    if not result.accepted:
        return {"row_id": "", "filtered_out": True, "filter_result": result}

    if message_id and sheets.row_exists(message_id):
        return {"row_id": message_id, "duplicate": True, "filter_result": result}

    row_id = sheets.append_email(parsed, message_id=message_id)
    return {"row_id": row_id, "filtered_out": False, "filter_result": result}


def update_sheet_node(state: dict) -> dict:
    row_id = state.get("row_id")
    prep_doc = state.get("prep_doc", "")

    if not row_id or not prep_doc:
        return {}

    sheets = SheetsClient()
    sheets.update_prep_doc(row_id=row_id, prep_doc=prep_doc)
    return {"row_id": row_id}
