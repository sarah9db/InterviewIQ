from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    if value is None:
        return ""
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        cleaned = cleaned[1:-1].strip()
    return cleaned


@dataclass(frozen=True)
class Settings:
    ollama_model: str = _env("OLLAMA_MODEL", "llama3")

    # Gmail API
    gmail_credentials_file: str = _env("GMAIL_CREDENTIALS_FILE", "credentials.json")
    gmail_token_file: str = _env("GMAIL_TOKEN_FILE", "token.json")
    gmail_query: str = _env(
        "GMAIL_QUERY",
        'label:inbox newer_than:1d ("interview" OR "screening" OR "assessment" OR "take home" OR "onsite")',
    )

    # Google Sheets
    google_sheet_id: str = _env("GOOGLE_SHEET_ID", "")
    google_sheet_name: str = _env("GOOGLE_SHEET_NAME", "InterviewSheet")

    # Search
    tavily_api_key: str = _env("TAVILY_API_KEY", "")

    # Twilio
    twilio_account_sid: str = _env("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = _env("TWILIO_AUTH_TOKEN", "")
    twilio_from_number: str = _env("TWILIO_FROM_NUMBER", "")
    twilio_to_number: str = _env("TWILIO_TO_NUMBER", "")
    twilio_whatsapp_from: str = _env("TWILIO_WHATSAPP_FROM", "")
    twilio_whatsapp_to: str = _env("TWILIO_WHATSAPP_TO", "")

    # Runtime state
    sms_last_run_file: str = _env("SMS_LAST_RUN_FILE", ".state/last_sms_run.txt")


settings = Settings()
