import pytest

from interview_agents.tools.llm_utils import extract_json_object


def test_extract_json_object_with_plain_json() -> None:
    text = '{"company": "Acme", "role": "Backend Engineer"}'
    assert extract_json_object(text) == {"company": "Acme", "role": "Backend Engineer"}


def test_extract_json_object_with_wrapped_json() -> None:
    text = "Here is the result:\n```json\n{\"company\": \"Acme\", \"role\": \"SWE\"}\n```"
    assert extract_json_object(text) == {"company": "Acme", "role": "SWE"}


def test_extract_json_object_raises_without_json() -> None:
    with pytest.raises(ValueError):
        extract_json_object("no object here")
