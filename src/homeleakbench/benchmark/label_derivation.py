"""Deterministically derive ground-truth labels for each task from a window.

Labels are derived from the *structured* event data (resident ids, rooms,
timestamps, activity labels), not from the minimized narrative text, so the
same ground truth applies across all C0-C4 variants of an item.
"""

from __future__ import annotations

from homeleakbench.data.event_windowing import EventWindow

ROOM_CATEGORIES_DEFAULT = {
    "private_area": {"bedroom", "bedroom_1", "bedroom_2", "bathroom", "office", "study"},
    "shared_area": {"kitchen", "living_room", "dining_room", "hallway", "entrance", "garage"},
}

ROUTINE_KEYWORDS = {
    "morning_routine": {"07", "08", "09"},
    "meal_related": set(),  # derived from sensor_type == appliance in kitchen
    "rest_or_sleep_period": {"22", "23", "00", "01", "02", "03"},
}

ACTIVITY_LABEL_MAP = {
    "preparing breakfast": "cooking_or_meal_preparation",
    "preparing dinner": "cooking_or_meal_preparation",
    "preparing drinks": "cooking_or_meal_preparation",
    "having breakfast": "cooking_or_meal_preparation",
    "having dinner": "cooking_or_meal_preparation",
    "grabing food": "cooking_or_meal_preparation",
    "having fruits": "cooking_or_meal_preparation",
    "drinking water": "cooking_or_meal_preparation",
    "resting on the couch": "resting",
    "watching tv": "resting",
    "reading books": "resting",
    "bedroom personal activity": "resting",
    "chatting": "resting",
    "playing": "resting",
    "cleaning appartment": "cleaning_or_housework",
    "washing dishes": "cleaning_or_housework",
    "clearing table": "cleaning_or_housework",
    "grabing tableware": "cleaning_or_housework",
    "getting out of the apartment": "leaving_or_returning",
    "coming into the apartment": "leaving_or_returning",
}


def derive_resident_identity(window: EventWindow) -> str:
    residents = window.resident_ids
    if len(residents) == 1:
        return f"resident_{residents[0]}"
    return "unknown"


def derive_occupancy_state(window: EventWindow) -> str:
    residents = window.resident_ids
    if len(residents) >= 2:
        return "multiple_residents_active"
    if len(residents) == 1:
        return "one_resident_active"
    return "uncertain"


def derive_private_location(
    window: EventWindow, room_categories: dict[str, set[str]] = ROOM_CATEGORIES_DEFAULT
) -> str:
    rooms = {r.lower() for r in window.rooms}
    is_private = bool(rooms & room_categories["private_area"])
    is_shared = bool(rooms & room_categories["shared_area"])
    if is_private and not is_shared:
        return "private_area"
    if is_shared and not is_private:
        return "shared_area"
    return "unknown"


def derive_routine(window: EventWindow) -> str:
    events = window.events
    hours = {ts.strftime("%H") for ts in events["timestamp"]}

    if hours & ROUTINE_KEYWORDS["morning_routine"]:
        return "morning_routine"

    is_meal = (events["sensor_type"].str.lower() == "appliance").any() and (
        events["room"].str.lower() == "kitchen"
    ).any()
    if is_meal:
        return "meal_related"

    if hours & ROUTINE_KEYWORDS["rest_or_sleep_period"]:
        return "rest_or_sleep_period"

    return "meal_related"


def derive_co_resident_activity(window: EventWindow) -> str:
    return "yes" if len(window.resident_ids) >= 2 else "no"


def derive_activity_understanding(window: EventWindow) -> str:
    events = window.events
    if "activity_label" in events.columns:
        labels = [str(v).lower() for v in events["activity_label"].dropna().unique()]
        for raw in labels:
            for key, mapped in ACTIVITY_LABEL_MAP.items():
                if key in raw:
                    return mapped

    is_meal = (events["sensor_type"].str.lower() == "appliance").any() and (
        events["room"].str.lower() == "kitchen"
    ).any()
    if is_meal:
        return "cooking_or_meal_preparation"

    long_inactive = (events["sensor_type"].str.lower() == "motion").any() and len(events) <= 2
    if long_inactive:
        return "resting"

    if (events["sensor_type"].str.lower() == "door").any():
        return "leaving_or_returning"

    return "cleaning_or_housework"


DERIVERS = {
    "resident_identity": derive_resident_identity,
    "occupancy_state": derive_occupancy_state,
    "private_location": derive_private_location,
    "routine_inference": derive_routine,
    "co_resident_activity": derive_co_resident_activity,
    "activity_understanding": derive_activity_understanding,
}


def derive_all_labels(window: EventWindow) -> dict[str, str]:
    return {task: fn(window) for task, fn in DERIVERS.items()}
