from datetime import datetime

from interview_agents.models import SheetRow
from interview_agents.tools.sheets_client import HEADERS, SheetsClient


def test_row_to_values_maps_fields_in_header_order() -> None:
    row = SheetRow(
        id="abc123",
        sender_name="Jane Doe",
        sender_email="jane@example.com",
        company="Acme",
        role="Backend Engineer",
        interview_datetime="2026-03-01T17:00:00+00:00",
        meeting_link="https://meet.example.com/123",
        subject="Interview Invite",
        snippet="Let's schedule a call.",
        prep_doc="# Prep",
        created_at="2026-03-01T00:00:00+00:00",
        updated_at="2026-03-01T00:00:00+00:00",
    )

    values = SheetsClient._row_to_values(row)

    assert len(values) == len(HEADERS)
    assert values[0] == "abc123"
    assert values[3] == "Acme"
    assert values[9] == "# Prep"


def test_dict_to_values_handles_missing_fields() -> None:
    values = SheetsClient._dict_to_values({"id": "id-1", "company": "Acme"})

    assert len(values) == len(HEADERS)
    assert values[0] == "id-1"
    assert values[3] == "Acme"
    assert values[4] == ""


def test_parse_iso_accepts_naive_and_offset_datetimes() -> None:
    naive = SheetsClient._parse_iso("2026-03-01T12:30:00")
    aware = SheetsClient._parse_iso("2026-03-01T12:30:00+00:00")

    assert isinstance(naive, datetime)
    assert isinstance(aware, datetime)
