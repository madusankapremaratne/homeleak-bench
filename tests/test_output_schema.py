import json
from pathlib import Path

from homeleakbench.llm.structured_output import parse_model_output

SCHEMA = json.loads(Path("prompts/output_schema.json").read_text())


def test_parse_valid_privacy_answer():
    text = '{"answer": "shared_area", "confidence": 0.8, "abstain": false, "evidence": ["e1"]}'
    parsed = parse_model_output(text, SCHEMA)
    assert parsed.valid_json
    assert parsed.schema_valid
    assert parsed.answer == "shared_area"
    assert parsed.confidence == 0.8
    assert not parsed.abstain


def test_parse_valid_activity_answer():
    text = '{"activity_state": "resting", "confidence": 0.6, "abstain": false}'
    parsed = parse_model_output(text, SCHEMA)
    assert parsed.schema_valid
    assert parsed.answer == "resting"


def test_parse_extracts_json_from_surrounding_text():
    text = (
        "Sure, here is the answer:\n"
        '{"answer": "unknown", "confidence": 0.1, "abstain": true}\nThanks.'
    )
    parsed = parse_model_output(text, SCHEMA)
    assert parsed.valid_json
    assert parsed.answer == "unknown"
    assert parsed.abstain


def test_parse_invalid_json_returns_abstain():
    parsed = parse_model_output("not json at all", SCHEMA)
    assert not parsed.valid_json
    assert parsed.abstain
    assert parsed.answer is None
