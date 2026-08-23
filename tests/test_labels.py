import pandas as pd
import pytest

from homeleakbench.benchmark.label_derivation import (
    derive_all_labels,
    derive_co_resident_activity,
    derive_occupancy_state,
    derive_resident_identity,
)
from homeleakbench.data.event_windowing import EventWindow


def _window(rows: list[dict]) -> EventWindow:
    events = pd.DataFrame(rows)
    return EventWindow(
        window_id="w0",
        session_id="s1",
        start=events["timestamp"].min(),
        end=events["timestamp"].max(),
        events=events,
    )


@pytest.fixture
def single_resident_window():
    return _window(
        [
            {
                "timestamp": pd.Timestamp("2024-01-01 08:00:00"),
                "resident_id": "A",
                "sensor_type": "motion",
                "room": "kitchen",
                "activity_label": None,
            }
        ]
    )


@pytest.fixture
def multi_resident_window():
    return _window(
        [
            {
                "timestamp": pd.Timestamp("2024-01-01 20:00:00"),
                "resident_id": "A",
                "sensor_type": "appliance",
                "room": "kitchen",
                "activity_label": None,
            },
            {
                "timestamp": pd.Timestamp("2024-01-01 20:01:00"),
                "resident_id": "B",
                "sensor_type": "motion",
                "room": "bedroom",
                "activity_label": None,
            },
        ]
    )


def test_resident_identity_single(single_resident_window):
    assert derive_resident_identity(single_resident_window) == "resident_A"


def test_occupancy_state_single_vs_multi(single_resident_window, multi_resident_window):
    assert derive_occupancy_state(single_resident_window) == "one_resident_active"
    assert derive_occupancy_state(multi_resident_window) == "multiple_residents_active"


def test_co_resident_activity(single_resident_window, multi_resident_window):
    assert derive_co_resident_activity(single_resident_window) == "no"
    assert derive_co_resident_activity(multi_resident_window) == "yes"


def test_derive_all_labels_returns_all_tasks(single_resident_window):
    labels = derive_all_labels(single_resident_window)
    assert set(labels.keys()) == {
        "resident_identity",
        "occupancy_state",
        "private_location",
        "routine_inference",
        "co_resident_activity",
        "activity_understanding",
    }
