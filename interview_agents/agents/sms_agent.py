from __future__ import annotations

from datetime import datetime, timezone

from interview_agents.tools.run_state import RunStateStore
from interview_agents.tools.sheets_client import SheetsClient
from interview_agents.tools.twilio_client import TwilioSMSClient


def build_sms_body(rows: list[dict[str, str]]) -> str:
    lines = ["Today's interview updates:"]
    for i, row in enumerate(rows, start=1):
        role = row.get("role") or "Unknown role"
        company = row.get("company") or "Unknown company"
        dt = row.get("interview_datetime") or "TBD"
        link = row.get("meeting_link") or "N/A"

        lines.append(f"{i}) {role} at {company} - {dt}")
        lines.append(f"Meeting: {link}")
        if row.get("prep_doc"):
            lines.append("Prep: Available in sheet")

    return "\n".join(lines)


def sms_node(_: dict) -> dict:
    sheets = SheetsClient()
    state_store = RunStateStore()
    last_run = state_store.load_last_sms_run()

    if last_run is None:
        recent_rows = sheets.get_recent_rows(hours=24)
    else:
        recent_rows = sheets.get_rows_since(last_run)

    if not recent_rows:
        state_store.save_last_sms_run(datetime.now(timezone.utc))
        return {"sms_sent": False}

    body = build_sms_body(recent_rows)
    twilio = TwilioSMSClient()
    twilio.send(body)
    state_store.save_last_sms_run(datetime.now(timezone.utc))
    return {"sms_sent": True}
