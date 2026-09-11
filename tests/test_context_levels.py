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
    # The functional category must not be the private_location task's own
    # label vocabulary. Recovering "private" vs "shared" from a functional
    # category (e.g. "sleeping area") requires background-knowledge
    # inference, not a string match against the narrative.
    assert "private area" not in text
    assert "shared area" not in text
    assert "sleeping area" in text or "food-preparation area" in text


def test_c4_is_aggregate_only(sample_window):
    narrative = build_narrative(sample_window)
    text = apply_minimization(
        narrative, LEVELS["C4"], CONFIG["room_categories"], CONFIG["time_periods"]
    )
    assert "bedroom" not in text
    assert "kitchen" not in text
    assert "22:4" not in text
    # Structural summary only: no resident-count language and no
    # room-category or activity-type language, since those are exactly
    # what occupancy_state, co_resident_activity, private_location, and
    # activity_understanding are derived from (see label_derivation.py).
    assert "resident" not in text.lower()
    assert "household member" not in text.lower()
    assert "resting" not in text.lower()
    assert "sensor event" in text


@pytest.mark.parametrize("level_name", ["C3", "C4"])
def test_no_privacy_label_vocabulary_leaks_into_narrative(level_name):
    """Regression test for the construct-validity bug found in review:
    earlier versions of C3/C4 embedded the private_location, occupancy_state,
    and co_resident_activity labels almost verbatim in the narrative text,
    making those tasks recoverable by string match rather than inference.
    This checks the actual label vocabulary never appears, across both a
    single-resident and a multi-resident synthetic window.
    """
    label_vocabulary = {
        "private_area",
        "private area",
        "shared_area",
        "shared area",
        "multiple_residents_active",
        "one_resident_active",
        "resting",
    }

    def make_window(resident_ids: list[str]) -> EventWindow:
        rows = []
        for i, rid in enumerate(resident_ids):
            rows.append(
                {
                    "session_id": "s1",
                    "timestamp": pd.Timestamp("2024-01-01 22:40:00") + pd.Timedelta(minutes=i),
                    "resident_id": rid,
                    "sensor_type": "motion",
                    "room": "bedroom",
                    "event_value": "ON",
                    "event_id": f"s1-{i}",
                }
            )
        events = pd.DataFrame(rows)
        return EventWindow(
            window_id="s1-w0",
            session_id="s1",
            start=events["timestamp"].min(),
            end=events["timestamp"].max(),
            events=events,
        )

    for resident_ids in (["A"], ["A", "B"]):
        window = make_window(resident_ids)
        narrative = build_narrative(window)
        text = apply_minimization(
            narrative, LEVELS[level_name], CONFIG["room_categories"], CONFIG["time_periods"]
        )
        text_l = text.lower()
        leaked = {term for term in label_vocabulary if term in text_l}
        assert not leaked, f"{level_name} narrative leaked label vocabulary {leaked}: {text!r}"
