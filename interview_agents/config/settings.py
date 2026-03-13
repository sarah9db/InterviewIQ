from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
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
class ScoringConfig:
    company_role_weight: int = 2
    strong_phrase_weight: int = 3
    context_term_weight: int = 1
    meeting_signal_weight: int = 2
    negative_signal_penalty: int = 2
    blocked_sender_penalty: int = 5
    threshold: int = 4
    require_strong_confirmation: bool = True


@dataclass(frozen=True)
class FilterConfig:
    strong_positive_phrases: tuple[str, ...] = ()
    interview_context_terms: tuple[str, ...] = ()
    meeting_hints: tuple[str, ...] = ()
    negative_signals: tuple[str, ...] = ()
    blocked_sender_emails: tuple[str, ...] = ()
    blocked_sender_domains: tuple[str, ...] = ()
    scoring: ScoringConfig = field(default_factory=ScoringConfig)


def _deep_merge(base: dict, override: dict) -> dict:
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_filter_config(override_path: str = "") -> FilterConfig:
    default_yaml = Path(__file__).resolve().parent / "filter_config.yaml"
    with open(default_yaml) as f:
        data = yaml.safe_load(f)

    override_file = override_path or _env("FILTER_CONFIG_FILE")
    if override_file:
        override_path_obj = Path(override_file)
        if not override_path_obj.is_absolute():
            override_path_obj = PROJECT_ROOT / override_path_obj
        if override_path_obj.exists():
            with open(override_path_obj) as f:
                override_data = yaml.safe_load(f) or {}
            data = _deep_merge(data, override_data)

    scoring_data = data.pop("scoring", {})
    scoring = ScoringConfig(**scoring_data)

    return FilterConfig(
        strong_positive_phrases=tuple(data.get("strong_positive_phrases", ())),
        interview_context_terms=tuple(data.get("interview_context_terms", ())),
        meeting_hints=tuple(data.get("meeting_hints", ())),
        negative_signals=tuple(data.get("negative_signals", ())),
        blocked_sender_emails=tuple(data.get("blocked_sender_emails", ())),
        blocked_sender_domains=tuple(data.get("blocked_sender_domains", ())),
        scoring=scoring,
    )


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
filter_config = load_filter_config()
