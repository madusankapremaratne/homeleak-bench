import pandas as pd
import pytest

from homeleakbench.benchmark.minimization import apply_minimization, load_context_levels
from homeleakbench.config import load_yaml
from homeleakbench.data.event_windowing import EventWindow
from homeleakbench.data.narrative_builder import build_narrative

CONFIG = load_yaml("configs/context_levels.yaml")
LEVELS = load_context_levels(CONFIG)


@pytest.fixture
def sample_window() -> EventWindow:
    events = pd.DataFrame(
        [
            {
                "session_id": "s1",
                "timestamp": pd.Timestamp("2024-01-01 22:40:00"),
                "resident_id": "B",
                "sensor_type": "motion",
                "room": "bedroom",
                "event_value": "ON",
                "event_id": "s1-0",
            },
            {
                "session_id": "s1",
                "timestamp": pd.Timestamp("2024-01-01 22:41:00"),
                "resident_id": "A",
                "sensor_type": "appliance",
                "room": "kitchen",
                "event_value": "ON",
                "event_id": "s1-1",
            },
        ]
    )
    return EventWindow(
        window_id="s1-w0",
        session_id="s1",
        start=events["timestamp"].min(),
        end=events["timestamp"].max(),
        events=events,
    )


def test_c0_retains_resident_labels(sample_window):
    narrative = build_narrative(sample_window)
    text = apply_minimization(
        narrative, LEVELS["C0"], CONFIG["room_categories"], CONFIG["time_periods"]
    )
    assert "Resident B" in text
    assert "Resident A" in text


def test_c1_removes_resident_identifiers(sample_window):
    narrative = build_narrative(sample_window)
    text = apply_minimization(
        narrative, LEVELS["C1"], CONFIG["room_categories"], CONFIG["time_periods"]
    )
    assert "Resident A" not in text
    assert "Resident B" not in text


def test_c2_coarsens_time(sample_window):
    narrative = build_narrative(sample_window)
    text = apply_minimization(
        narrative, LEVELS["C2"], CONFIG["room_categories"], CONFIG["time_periods"]
    )
    assert "22:4" not in text


def test_c3_coarsens_location(sample_window):
    narrative = build_narrative(sample_window)
    text = apply_minimization(
        narrative, LEVELS["C3"], CONFIG["room_categories"], CONFIG["time_periods"]
    )
    assert "bedroom" not in text
    assert "kitchen" not in text
    assert "private area" in text or "shared area" in text


def test_c4_is_aggregate_only(sample_window):
    narrative = build_narrative(sample_window)
    text = apply_minimization(
        narrative, LEVELS["C4"], CONFIG["room_categories"], CONFIG["time_periods"]
    )
    assert "bedroom" not in text
    assert "22:4" not in text
    assert "Multiple household members" in text
