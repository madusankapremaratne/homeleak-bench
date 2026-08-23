"""Parse and validate model JSON output against prompts/output_schema.json."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import jsonschema

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class ParsedOutput:
    raw_text: str
    valid_json: bool
    schema_valid: bool
    answer: str | None
    confidence: float | None
    abstain: bool
    evidence: list[str]
    error: str | None = None


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = _JSON_OBJECT_RE.search(text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def parse_model_output(raw_text: str, schema: dict) -> ParsedOutput:
    obj = _extract_json(raw_text)
    if obj is None:
        return ParsedOutput(
            raw_text=raw_text,
            valid_json=False,
            schema_valid=False,
            answer=None,
            confidence=None,
            abstain=True,
            evidence=[],
            error="Could not extract a JSON object from the model response.",
        )

    schema_valid = True
    error = None
    try:
        jsonschema.validate(obj, schema)
    except jsonschema.ValidationError as e:
        schema_valid = False
        error = str(e.message)

    answer = obj.get("answer") or obj.get("activity_state")
    confidence = obj.get("confidence")
    abstain = bool(obj.get("abstain", False))
    evidence = obj.get("evidence", []) or []

    return ParsedOutput(
        raw_text=raw_text,
        valid_json=True,
        schema_valid=schema_valid,
        answer=answer,
        confidence=confidence,
        abstain=abstain,
        evidence=evidence,
        error=error,
    )
