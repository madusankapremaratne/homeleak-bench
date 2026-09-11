"""Apply the C0-C4 context-minimization transforms to a narrative."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from homeleakbench.data.narrative_builder import Narrative, NarrativeSentence


@dataclass
class ContextLevelConfig:
    name: str
    remove_identity: bool
    coarsen_time: bool
    coarsen_location: bool
    aggregate_only: bool


def load_context_levels(config: dict) -> dict[str, ContextLevelConfig]:
    levels = {}
    for key, spec in config["levels"].items():
        levels[key] = ContextLevelConfig(
            name=spec["name"],
            remove_identity=spec["remove_identity"],
            coarsen_time=spec["coarsen_time"],
            coarsen_location=spec["coarsen_location"],
            aggregate_only=spec["aggregate_only"],
        )
    return levels


def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h) % 24, int(m))


def _time_period(ts_time: time, periods: list[dict]) -> str:
    for period in periods:
        start = _parse_hhmm(period["start"])
        end = _parse_hhmm(period["end"])
        if start <= end:
            if start <= ts_time < end:
                return period["name"]
        else:  # wraps past midnight
            if ts_time >= start or ts_time < end:
                return period["name"]
    return "unspecified period"


def _room_category(room: str | None, room_categories: dict[str, list[str]]) -> str:
    if room is None:
        return "an unspecified area"
    room_l = room.lower()
    for category, rooms in room_categories.items():
        if room_l in rooms:
            return category.replace("_", " ")
    return "an unspecified area"


def _resident_phrase(resident_id: str | None, seen: set[str], level: ContextLevelConfig) -> str:
    if not level.remove_identity:
        return f"Resident {resident_id}" if resident_id else "A resident"
    if resident_id is None or resident_id not in seen:
        if resident_id is not None:
            seen.add(resident_id)
        return "A resident" if not seen or len(seen) <= 1 else "A household member"
    return "Another resident"


def apply_minimization(
    narrative: Narrative,
    level: ContextLevelConfig,
    room_categories: dict[str, list[str]],
    time_periods: list[dict],
) -> str:
    """Return the minimized natural-language context string for one level."""
    if level.aggregate_only:
        return _aggregate_state_sentence(narrative)

    seen_residents: set[str] = set()
    sentences: list[str] = []

    for sentence in narrative.sentences:
        resident_phrase = _resident_phrase(sentence.resident_id, seen_residents, level)

        room_text = sentence.room or "an unspecified area"
        if level.coarsen_location:
            room_text = _room_category(sentence.room, room_categories)

        if level.coarsen_time:
            time_text = _time_period(sentence.timestamp.time(), time_periods)
            time_phrase = f"during the {time_text}" if "period" not in time_text else time_text
        else:
            time_phrase = f"at {sentence.timestamp.strftime('%H:%M')}"

        verb = _infer_verb(sentence)
        loc_prefix = "in the" if not level.coarsen_location else "in a"
        sentences.append(f"{resident_phrase} {verb} {loc_prefix} {room_text} {time_phrase}.")

    return " ".join(sentences)


def _infer_verb(sentence: NarrativeSentence) -> str:
    sensor = str(sentence.sensor_type or "").lower()
    if sensor == "motion" and sentence.duration_seconds and sentence.duration_seconds > 600:
        return "remained inactive"
    if sensor == "appliance":
        return "was active"
    return "was active"


def _aggregate_state_sentence(narrative: Narrative) -> str:
    """Return a structural summary of the window for C4.

    Deliberately reports only counts and durations computable from the
    narrative's sentence list, never resident count or a room-category
    classification directly: those are exactly the quantities
    label_derivation.py uses to derive occupancy_state,
    co_resident_activity, and private_location, so writing them into the
    sentence (even paraphrased) makes the corresponding label recoverable
    by string match rather than by inference. See the C4 config comment
    in context_levels.yaml and docs/annotation_guidelines.md.
    """
    n_events = len(narrative.sentences)
    if n_events == 0:
        return "No sensor activity was recorded in this period."

    rooms_touched = len({s.room for s in narrative.sentences if s.room})
    sensor_types = len({s.sensor_type for s in narrative.sentences if s.sensor_type})
    timestamps = [s.timestamp for s in narrative.sentences]
    span_minutes = max(1, round((max(timestamps) - min(timestamps)).total_seconds() / 60))

    def _plural(n: int, noun: str) -> str:
        return f"{n} {noun}" if n == 1 else f"{n} {noun}s"

    return (
        f"The home recorded {_plural(n_events, 'sensor event')} "
        f"across {_plural(max(rooms_touched, 1), 'room')} "
        f"and {_plural(max(sensor_types, 1), 'sensor type')} "
        f"over a {span_minutes}-minute period."
    )
