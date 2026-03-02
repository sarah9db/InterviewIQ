from interview_agents.agents.sms_agent import build_sms_body


def test_build_sms_body_includes_core_fields() -> None:
    rows = [
        {
            "role": "ML Engineer",
            "company": "Acme",
            "interview_datetime": "2026-03-01T18:00:00+00:00",
            "meeting_link": "https://meet.example.com/abc",
            "prep_doc": "# Prep",
        }
    ]

    body = build_sms_body(rows)

    assert "Today's interview updates:" in body
    assert "1) ML Engineer at Acme - 2026-03-01T18:00:00+00:00" in body
    assert "Meeting: https://meet.example.com/abc" in body
    assert "Prep: Available in sheet" in body


def test_build_sms_body_uses_defaults_when_fields_missing() -> None:
    body = build_sms_body([{}])

    assert "Unknown role at Unknown company - TBD" in body
    assert "Meeting: N/A" in body
