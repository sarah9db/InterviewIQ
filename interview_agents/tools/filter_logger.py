from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from interview_agents.models import FilterResult

_DEFAULT_LOG_FILE = os.path.join(
    Path(__file__).resolve().parents[2], "logs", "filter_decisions.jsonl"
)

_logger: logging.Logger | None = None


def _get_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    log_file = os.environ.get("FILTER_LOG_FILE", _DEFAULT_LOG_FILE)
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)

    _logger = logging.getLogger("filter_decisions")
    _logger.setLevel(logging.INFO)
    _logger.propagate = False

    # Remove any stale handlers (e.g. from a previous configuration).
    for old in _logger.handlers[:]:
        old.close()
        _logger.removeHandler(old)

    handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)

    return _logger


def log_filter_result(result: FilterResult) -> None:
    logger = _get_logger()
    logger.info(json.dumps(result.model_dump(), default=str))
