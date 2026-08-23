"""Build a natural-language narrative (C0) from a windowed event sequence.

Downstream minimization (C1-C4) is applied on top of the structured
sentence list this module produces — see benchmark/minimization.py.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from homeleakbench.data.event_windowing import EventWindow


@dataclass
class NarrativeSentence:
    resident_id: str | None
    room: str | None
    sensor_type: str | None
    timestamp: pd.Timestamp
    duration_seconds: float | None
    text: str


@dataclass
class Narrative:
    window_id: str
    session_id: str
    sentences: list[NarrativeSentence]

    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in self.sentences)


def _format_time(ts: pd.Timestamp) -> str:
    return f"at {ts.strftime('%H:%M')}"


def _format_duration(seconds: float) -> str:
    minutes = round(seconds / 60)
    if minutes <= 0:
        return "briefly"
    if minutes == 1:
        return "1 minute"
    return f"{minutes} minutes"


def _sentence_for_event(row: pd.Series, duration_seconds: float | None) -> str:
    resident = (
        f"Resident {row['resident_id']}" if pd.notna(row.get("resident_id")) else "A resident"
    )
    room = row.get("room") or "an unspecified area"
    time_phrase = _format_time(row["timestamp"])
    sensor = str(row.get("sensor_type") or "").lower()

    if sensor == "motion" and duration_seconds and duration_seconds > 600:
        return (
            f"{resident} remained inactive in the {room} for {_format_duration(duration_seconds)}."
        )
    if sensor == "appliance" and room == "kitchen":
        return f"{resident} prepared food in the {room} {time_phrase}."
    if sensor == "door":
        state = str(row.get("event_value") or "").upper()
        verb = "entered" if state in {"OPEN", "1", "TRUE"} else "left"
        return f"{resident} {verb} the {room} {time_phrase}."

    return f"{resident} was active in the {room} {time_phrase}."


def build_narrative(window: EventWindow) -> Narrative:
    sentences: list[NarrativeSentence] = []
    events = window.events.sort_values("timestamp").reset_index(drop=True)

    for i, row in events.iterrows():
        duration = None
        if i + 1 < len(events):
            duration = (events.loc[i + 1, "timestamp"] - row["timestamp"]).total_seconds()

        text = _sentence_for_event(row, duration)
        sentences.append(
            NarrativeSentence(
                resident_id=row.get("resident_id"),
                room=row.get("room"),
                sensor_type=row.get("sensor_type"),
                timestamp=row["timestamp"],
                duration_seconds=duration,
                text=text,
            )
        )

    return Narrative(window_id=window.window_id, session_id=window.session_id, sentences=sentences)
