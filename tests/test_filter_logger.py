from __future__ import annotations

import json
import os

from interview_agents.models import FilterResult
from interview_agents.tools import filter_logger


def _make_result(accepted: bool = True) -> FilterResult:
    return FilterResult(
        subject="Interview at Acme",
        sender_email="recruiter@acme.com",
        score=6,
        company_role_points=2,
        strong_phrase_points=3,
        context_term_points=1,
        meeting_signal_points=0,
        negative_signal_points=0,
        blocked_sender_points=0,
        strong_confirmation=True,
        accepted=accepted,
        rejection_reason=None if accepted else "below threshold",
        matched_strong_phrases=["congratulations"],
        matched_context_terms=["interview"],
        matched_negative_signals=[],
        timestamp="2026-03-12T00:00:00+00:00",
    )


def test_log_filter_result_writes_jsonl(tmp_path, monkeypatch) -> None:
    log_file = str(tmp_path / "test_filter.jsonl")
    monkeypatch.setenv("FILTER_LOG_FILE", log_file)
    # Reset the cached logger so it picks up the new env var.
    monkeypatch.setattr(filter_logger, "_logger", None)

    result = _make_result(accepted=True)
    filter_logger.log_filter_result(result)

    # Flush handlers.
    logger = filter_logger._get_logger()
    for handler in logger.handlers:
        handler.flush()

    assert os.path.exists(log_file)
    with open(log_file) as f:
        lines = f.readlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["accepted"] is True
    assert data["score"] == 6
    assert data["subject"] == "Interview at Acme"
    assert data["matched_strong_phrases"] == ["congratulations"]


def test_log_filter_result_appends_multiple(tmp_path, monkeypatch) -> None:
    log_file = str(tmp_path / "test_multi.jsonl")
    monkeypatch.setenv("FILTER_LOG_FILE", log_file)
    monkeypatch.setattr(filter_logger, "_logger", None)

    filter_logger.log_filter_result(_make_result(accepted=True))
    filter_logger.log_filter_result(_make_result(accepted=False))

    logger = filter_logger._get_logger()
    for handler in logger.handlers:
        handler.flush()

    with open(log_file) as f:
        lines = f.readlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["accepted"] is True
    assert json.loads(lines[1])["accepted"] is False


def test_log_filter_result_valid_json(tmp_path, monkeypatch) -> None:
    log_file = str(tmp_path / "test_valid.jsonl")
    monkeypatch.setenv("FILTER_LOG_FILE", log_file)
    monkeypatch.setattr(filter_logger, "_logger", None)

    filter_logger.log_filter_result(_make_result())

    logger = filter_logger._get_logger()
    for handler in logger.handlers:
        handler.flush()

    with open(log_file) as f:
        for line in f:
            data = json.loads(line)
            assert "score" in data
            assert "accepted" in data
            assert "timestamp" in data
            assert "rejection_reason" in data
