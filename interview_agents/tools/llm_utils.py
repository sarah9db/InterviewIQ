from __future__ import annotations

import json
import re
from typing import Any

from interview_agents.config.settings import settings


def make_llm():
    from langchain_ollama import OllamaLLM

    return OllamaLLM(model=settings.ollama_model)


def extract_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    candidate = _find_first_balanced_json_object(text)
    if candidate is None:
        raise ValueError("No JSON object found in model response")

    return json.loads(candidate)


def _find_first_balanced_json_object(text: str) -> str | None:
    start = text.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]

        start = text.find("{", start + 1)

    return None
