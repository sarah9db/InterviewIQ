from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from interview_agents.config.settings import settings
from interview_agents.models import EmailInfo, FilterResult, SheetRow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

HEADERS = [
    "id",
    "sender_name",
    "sender_email",
    "company",
    "role",
    "interview_datetime",
    "meeting_link",
    "subject",
    "snippet",
    "prep_doc",
    "created_at",
    "updated_at",
]


class SheetsClient:
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
            self._service = build("sheets", "v4", credentials=creds)
        return self._service

    def ensure_headers(self) -> None:
        values = self._get_values("A1:L1")
        if values:
            return
        self._update_values("A1:L1", [HEADERS])

    def append_email(self, email: EmailInfo, message_id: str | None = None) -> str:
        now = datetime.now(timezone.utc).isoformat()
        row_id = message_id or email.gmail_message_id or f"manual-{int(datetime.now().timestamp())}"
        row = SheetRow(
            id=row_id,
            sender_name=email.sender_name,
            sender_email=email.sender_email,
            company=email.company,
            role=email.role,
            interview_datetime=email.interview_datetime,
            meeting_link=email.meeting_link,
            subject=email.subject,
            snippet=email.snippet,
            prep_doc=None,
            created_at=now,
            updated_at=now,
        )
        self._append_values("A:L", [self._row_to_values(row)])
        return row_id

    def update_prep_doc(self, row_id: str, prep_doc: str) -> bool:
        rows = self.get_all_rows()
        for idx, row in enumerate(rows, start=2):
            if row.get("id") == row_id:
                row["prep_doc"] = prep_doc
                row["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._update_values(f"A{idx}:L{idx}", [self._dict_to_values(row)])
                return True
        return False

    def get_all_rows(self) -> list[dict[str, str]]:
        values = self._get_values("A1:L")
        if not values:
            return []

        headers = values[0]
        rows: list[dict[str, str]] = []
        for raw in values[1:]:
            padded = raw + [""] * (len(headers) - len(raw))
            rows.append(dict(zip(headers, padded)))
        return rows

    def row_exists(self, row_id: str) -> bool:
        return any(r.get("id") == row_id for r in self.get_all_rows())

    def get_recent_rows(self, hours: int = 24) -> list[dict[str, str]]:
        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent: list[dict[str, str]] = []
        for row in self.get_all_rows():
            created = self._parse_iso(row.get("created_at", ""))
            updated = self._parse_iso(row.get("updated_at", ""))
            if (created and created >= threshold) or (updated and updated >= threshold):
                recent.append(row)
        return recent

    def get_rows_since(self, since: datetime) -> list[dict[str, str]]:
        since_utc = since.astimezone(timezone.utc)
        recent: list[dict[str, str]] = []
        for row in self.get_all_rows():
            created = self._parse_iso(row.get("created_at", ""))
            updated = self._parse_iso(row.get("updated_at", ""))
            if (created and created >= since_utc) or (updated and updated >= since_utc):
                recent.append(row)
        return recent

    def _sheet_range(self, rng: str) -> str:
        return f"{settings.google_sheet_name}!{rng}"

    @staticmethod
    def _require_sheet_id() -> str:
        if not settings.google_sheet_id:
            raise ValueError(
                "GOOGLE_SHEET_ID is empty. Set it in .env (or environment) before running."
            )
        return settings.google_sheet_id

    def _get_values(self, rng: str) -> list[list[str]]:
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self._require_sheet_id(), range=self._sheet_range(rng))
            .execute()
        )
        return result.get("values", [])

    def _append_values(self, rng: str, values: list[list[str]]) -> None:
        self.service.spreadsheets().values().append(
            spreadsheetId=self._require_sheet_id(),
            range=self._sheet_range(rng),
            valueInputOption="RAW",
            body={"values": values},
        ).execute()

    def _update_values(self, rng: str, values: list[list[str]]) -> None:
        self.service.spreadsheets().values().update(
            spreadsheetId=self._require_sheet_id(),
            range=self._sheet_range(rng),
            valueInputOption="RAW",
            body={"values": values},
        ).execute()

    @staticmethod
    def _parse_iso(value: str) -> datetime | None:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            return None

    def append_filter_log(self, result: FilterResult) -> None:
        sheet_range = f"{settings.filter_log_sheet_name}!A:O"
        row = [
            result.timestamp,
            result.subject or "",
            result.sender_email or "",
            str(result.score),
            str(result.company_role_points),
            str(result.strong_phrase_points),
            str(result.context_term_points),
            str(result.meeting_signal_points),
            str(result.negative_signal_points),
            str(result.blocked_sender_points),
            str(result.strong_confirmation),
            str(result.accepted),
            result.rejection_reason or "",
            ", ".join(result.matched_strong_phrases),
            ", ".join(result.matched_negative_signals),
        ]
        self.service.spreadsheets().values().append(
            spreadsheetId=self._require_sheet_id(),
            range=sheet_range,
            valueInputOption="RAW",
            body={"values": [row]},
        ).execute()

    @staticmethod
    def _row_to_values(row: SheetRow) -> list[str]:
        return [
            row.id,
            row.sender_name or "",
            row.sender_email or "",
            row.company or "",
            row.role or "",
            row.interview_datetime or "",
            row.meeting_link or "",
            row.subject or "",
            row.snippet or "",
            row.prep_doc or "",
            row.created_at,
            row.updated_at,
        ]

    @staticmethod
    def _dict_to_values(row: dict[str, Any]) -> list[str]:
        return [str(row.get(h, "") or "") for h in HEADERS]
