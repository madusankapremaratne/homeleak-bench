#!/usr/bin/env python
"""Validate a JSONL annotation file against data/annotations/annotation_schema.json.

Usage:
    python scripts/validate_annotations.py --input data/annotations/privacy_labels.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import jsonschema

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "annotations" / "annotation_schema.json"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--schema", default=str(SCHEMA_PATH))
    args = parser.parse_args()

    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))

    n_ok = 0
    n_bad = 0
    errors: list[str] = []

    with open(args.input, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                n_bad += 1
                errors.append(f"line {lineno}: invalid JSON ({e})")
                continue

            try:
                jsonschema.validate(record, schema)
                n_ok += 1
            except jsonschema.ValidationError as e:
                n_bad += 1
                errors.append(f"line {lineno}: {e.message}")

    print(f"Validated {args.input}: {n_ok} valid, {n_bad} invalid.")
    for err in errors[:20]:
        print(f"  - {err}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more.")

    if n_bad > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
