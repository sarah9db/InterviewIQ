from __future__ import annotations

import base64
import re
from email.utils import parseaddr
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from interview_agents.config.settings import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]


class GmailClient:
    def __init__(self) -> None:
        self._service = None

    def _get_credentials(self) -> Credentials:
        creds = None
        if settings.gmail_token_file:
            try:
                creds = Credentials.from_authorized_user_file(settings.gmail_token_file, SCOPES)
            except FileNotFoundError:
                creds = None

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        if not creds or not creds.valid or not creds.has_scopes(SCOPES):
            flow = InstalledAppFlow.from_client_secrets_file(settings.gmail_credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(settings.gmail_token_file, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        return creds

    @property
    def service(self):
        if self._service is None:
            creds = self._get_credentials()
            self._service = build("gmail", "v1", credentials=creds)
        return self._service

    def list_messages(self, query: str, max_results: int = 20) -> list[dict[str, str]]:
        result = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        return result.get("messages", [])

    def get_message(self, message_id: str) -> dict[str, Any]:
        return (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

    def get_message_text(self, message: dict[str, Any]) -> str:
        payload = message.get("payload", {})
        headers = payload.get("headers", [])

        subject = self._header_value(headers, "Subject")
        sender = self._header_value(headers, "From")
        snippet = message.get("snippet", "")
        body = self._extract_body(payload)

        text = [
            f"Message-ID: {message.get('id', '')}",
            f"From: {sender}",
            f"Subject: {subject}",
            f"Snippet: {snippet}",
            "",
            body,
        ]
        return "\n".join(text).strip()

    def extract_sender(self, message: dict[str, Any]) -> tuple[str | None, str | None]:
        headers = message.get("payload", {}).get("headers", [])
        raw = self._header_value(headers, "From")
        name, email = parseaddr(raw)
        return (name or None, email or None)

    def extract_subject(self, message: dict[str, Any]) -> str | None:
        headers = message.get("payload", {}).get("headers", [])
        return self._header_value(headers, "Subject") or None

    @staticmethod
    def _header_value(headers: list[dict[str, str]], name: str) -> str:
        for h in headers:
            if h.get("name", "").lower() == name.lower():
                return h.get("value", "")
        return ""

    def _extract_body(self, payload: dict[str, Any]) -> str:
        text_parts: list[str] = []

        def walk(part: dict[str, Any]) -> None:
            mime_type = part.get("mimeType", "")
            body = part.get("body", {})
            data = body.get("data")

            if data and mime_type in {"text/plain", "text/html"}:
                decoded = self._decode_base64(data)
                if mime_type == "text/html":
                    decoded = re.sub(r"<[^>]+>", " ", decoded)
                text_parts.append(decoded)

            for child in part.get("parts", []) or []:
                walk(child)

        walk(payload)
        return "\n".join(p.strip() for p in text_parts if p.strip())

    @staticmethod
    def _decode_base64(data: str) -> str:
        padded = data + "=" * (-len(data) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return raw.decode("utf-8", errors="ignore")
