from pathlib import Path

import pandas as pd
import pytest

from homeleakbench.data.mural_parser import discover_source_files, load_raw_events


def _write_csv(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def test_discover_source_files_empty(tmp_path):
    assert discover_source_files(tmp_path / "missing") == []


def test_load_raw_events_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_raw_events(tmp_path / "empty", {"session_id": "session_id"})


def test_load_raw_events_missing_column_raises(tmp_path):
    _write_csv(tmp_path / "a.csv", [{"session_id": "s1"}])
    with pytest.raises(ValueError):
        load_raw_events(tmp_path, {"session_id": "session_id", "timestamp": "ts"})


def test_load_raw_events_happy_path(tmp_path):
    _write_csv(
        tmp_path / "a.csv",
        [
            {
                "session_id": "s1",
                "ts": "2024-01-01T08:00:00",
                "resident": "A",
                "sensor": "motion",
                "room": "kitchen",
                "value": "ON",
            },
            {
                "session_id": "s1",
                "ts": "2024-01-01T08:05:00",
                "resident": "A",
                "sensor": "appliance",
                "room": "kitchen",
                "value": "ON",
            },
        ],
    )
    column_map = {
        "session_id": "session_id",
        "timestamp": "ts",
        "resident_id": "resident",
        "sensor_type": "sensor",
        "room": "room",
        "event_value": "value",
    }
    events = load_raw_events(tmp_path, column_map)
    assert len(events) == 2
    assert list(events["session_id"]) == ["s1", "s1"]
    assert events["timestamp"].is_monotonic_increasing
    assert "event_id" in events.columns
