from __future__ import annotations

import argparse
from pathlib import Path

from google.oauth2.credentials import Credentials

from interview_agents.config.settings import settings
from interview_agents.graph import build_email_graph, build_sms_graph
from interview_agents.tools.gmail_client import GmailClient
from interview_agents.tools.sheets_client import SCOPES as REQUIRED_GOOGLE_SCOPES


def run_poll_gmail(max_results: int, query: str | None = None) -> None:
    gmail = GmailClient()
    app = build_email_graph()

    q = query or settings.gmail_query
    messages = gmail.list_messages(query=q, max_results=max_results)
    appended = 0
    filtered = 0
    duplicates = 0
    failed = 0
    fast_rejected = 0

    for item in messages:
        message_id = item["id"]
        try:
            msg = gmail.get_message(message_id)
            raw_text = gmail.get_message_text(msg)
            result = app.invoke({"email_raw": raw_text, "gmail_message_id": message_id})
            if result.get("fast_rejected"):
                fast_rejected += 1
                print(f"Fast-rejected message {message_id}")
            elif result.get("duplicate"):
                duplicates += 1
                print(f"Duplicate message {message_id} (already in sheet)")
            elif result.get("filtered_out") or not result.get("row_id", ""):
                filtered += 1
                print(f"Filtered out message {message_id}")
            else:
                appended += 1
                print(f"Appended message {message_id} -> row {result.get('row_id', '')}")
        except Exception as exc:
            failed += 1
            print(f"Skipped message {message_id}: {exc}")

    print(
        f"Summary: fetched={len(messages)} appended={appended} "
        f"filtered={filtered} fast_rejected={fast_rejected} "
        f"duplicates={duplicates} failed={failed}"
    )


def run_process_single_email(path: Path) -> None:
    app = build_email_graph()
    text = path.read_text(encoding="utf-8")
    app.invoke({"email_raw": text, "gmail_message_id": f"local-{path.stem}"})
    print(f"Processed local email file: {path}")


def run_daily_sms() -> None:
    app = build_sms_graph()
    result = app.invoke({})
    print(f"Daily SMS result: {result}")


def run_doctor() -> None:
    print("=== Interview Agents Doctor ===")
    print(f"GMAIL_CREDENTIALS_FILE: {settings.gmail_credentials_file}")
    print(f"GMAIL_TOKEN_FILE: {settings.gmail_token_file}")
    print(f"GOOGLE_SHEET_ID set: {bool(settings.google_sheet_id)}")
    if settings.google_sheet_id:
        print(f"GOOGLE_SHEET_ID prefix: {settings.google_sheet_id[:8]}...")
    print(f"GOOGLE_SHEET_NAME: {settings.google_sheet_name}")

    cred_path = Path(settings.gmail_credentials_file)
    token_path = Path(settings.gmail_token_file)
    print(f"credentials.json exists: {cred_path.exists()}")
    print(f"token.json exists: {token_path.exists()}")

    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), REQUIRED_GOOGLE_SCOPES)
            token_scopes = set(creds.scopes or [])
            needed = set(REQUIRED_GOOGLE_SCOPES)
            print(f"token has gmail scope: {'https://www.googleapis.com/auth/gmail.readonly' in token_scopes}")
            print(f"token has sheets scope: {'https://www.googleapis.com/auth/spreadsheets' in token_scopes}")
            print(f"token covers all required scopes: {needed.issubset(token_scopes)}")
        except Exception as exc:
            print(f"token parse error: {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interview multi-agent system")
    subparsers = parser.add_subparsers(dest="command", required=True)

    poll = subparsers.add_parser("poll-gmail", help="Poll Gmail and process interview emails")
    poll.add_argument("--max-results", type=int, default=20)
    poll.add_argument("--query", type=str, default=None)

    one = subparsers.add_parser("process-email-file", help="Process a local raw email text file")
    one.add_argument("path", type=Path)

    subparsers.add_parser("send-daily-sms", help="Send daily interview SMS summary")
    subparsers.add_parser("doctor", help="Show config/auth diagnostics")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "poll-gmail":
        run_poll_gmail(max_results=args.max_results, query=args.query)
    elif args.command == "process-email-file":
        run_process_single_email(path=args.path)
    elif args.command == "send-daily-sms":
        run_daily_sms()
    elif args.command == "doctor":
        run_doctor()


if __name__ == "__main__":
    main()
