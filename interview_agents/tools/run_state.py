from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from interview_agents.config.settings import settings


class RunStateStore:
    def __init__(self, state_file: str | None = None) -> None:
        self.path = Path(state_file or settings.sms_last_run_file)

    def load_last_sms_run(self) -> datetime | None:
        if not self.path.exists():
            return None
        raw = self.path.read_text(encoding="utf-8").strip()
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def save_last_sms_run(self, dt: datetime | None = None) -> None:
        value = (dt or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(value, encoding="utf-8")
