"""Parse a locally downloaded MuRAL export into a normalized event table.

MuRAL is not redistributed with this repository (see
data/source_instructions/mural_download.md). The official export layout is
one directory per session (e.g. `01/`, `02/`, ...) under `data/raw/mural/`,
each containing:

    data.csv      -- uid, time, sensor, action, Subject, Description, activity
    context.json  -- start time, day, resident number, roles, scenario

plus dataset-wide `sensors.json` (sensor metadata) and `activities.json`
(activity id -> name mapping) at the top level.

`load_mural_dataset()` parses that native layout directly. A generic
`load_raw_events()` (CSV/Parquet + column mapping) is kept as a fallback
for differently-shaped exports — configure `data.column_map` in
configs/benchmark.yaml if you need it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

CANONICAL_COLUMNS = [
    "session_id",
    "timestamp",
    "resident_id",
    "sensor_type",
    "room",
    "event_value",
    "activity_label",
]

# Known multi-word room prefixes in MuRAL's `sensor` field (checked before
# falling back to a single-token room name).
_MULTI_WORD_ROOMS = ["dining room", "living room"]

_SENSOR_TYPE_PATTERNS = [
    (re.compile(r"\bdoor\b"), "door"),
    (re.compile(r"\bmov\b"), "motion"),
    (re.compile(r"\bwattmeter\b"), "appliance"),
    (re.compile(r"\bcontact\b"), "contact"),
]


def _split_room_and_sensor(sensor_field: str) -> tuple[str, str]:
    """Split MuRAL's packed `"<room> <sensor description>"` string.

    Examples: "bedroom_1 door" -> ("bedroom_1", "door"),
    "dining room chair_1 contact" -> ("dining room", "chair_1 contact"),
    "main door" -> ("entrance", "main door").
    """
    sensor_field = (sensor_field or "").strip()
    if not sensor_field:
        return "unspecified", "unknown"

    if sensor_field == "main door":
        return "entrance", sensor_field

    for room in _MULTI_WORD_ROOMS:
        if sensor_field.startswith(room + " "):
            return room.replace(" ", "_"), sensor_field[len(room) + 1 :]

    parts = sensor_field.split(" ", 1)
    room = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    return room, rest


def _sensor_type_from_description(description: str) -> str:
    for pattern, sensor_type in _SENSOR_TYPE_PATTERNS:
        if pattern.search(description):
            return sensor_type
    return "other"


def _load_activity_map(raw_dir: Path) -> dict[int, str]:
    path = raw_dir / "activities.json"
    if not path.exists():
        return {}
    records = json.loads(path.read_text(encoding="utf-8"))
    return {r["id"]: r["name"] for r in records}


def discover_mural_session_dirs(raw_dir: str | Path) -> list[Path]:
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        return []
    return sorted(
        p.parent for p in raw_dir.glob("*/data.csv") if (p.parent / "context.json").exists()
    )


def load_mural_dataset(raw_dir: str | Path) -> pd.DataFrame:
    """Parse MuRAL's native per-session directory layout into an event table."""
    raw_dir = Path(raw_dir)
    session_dirs = discover_mural_session_dirs(raw_dir)
    if not session_dirs:
        raise FileNotFoundError(
            f"No MuRAL session directories (NN/data.csv + NN/context.json) found "
            f"under '{raw_dir}'. Follow data/source_instructions/mural_download.md "
            "to obtain and place the dataset there before running build_benchmark.py."
        )

    activity_map = _load_activity_map(raw_dir)
    frames = []

    for i, session_dir in enumerate(session_dirs):
        session_id = session_dir.name
        # context.json (start time, day, resident number, roles, scenario) is
        # available under session_dir for manual QA but not consumed here.
        df = pd.read_csv(session_dir / "data.csv", dtype=str).fillna("")

        rooms, sensor_types = [], []
        for sensor_field in df["sensor"]:
            room, rest = _split_room_and_sensor(sensor_field)
            rooms.append(room)
            sensor_types.append(_sensor_type_from_description(rest))

        df["room"] = rooms
        df["sensor_type"] = sensor_types
        df["event_value"] = df["action"]
        df["activity_label"] = (
            pd.to_numeric(df["activity"], errors="coerce").map(activity_map).fillna("")
        )
        df["session_id"] = session_id

        # A synthetic, session-unique base date keeps timestamps orderable and
        # comparable without implying any real calendar date.
        base_date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=i)
        parsed_time = pd.to_timedelta(df["time"], errors="coerce")
        df["timestamp"] = base_date + parsed_time
        # MuRAL session clocks can wrap past midnight; detect decreases and
        # roll the date forward so ordering stays monotonic within a session.
        wrapped = (parsed_time.diff().dt.total_seconds() < 0).cumsum()
        df["timestamp"] = df["timestamp"] + pd.to_timedelta(wrapped.fillna(0), unit="D")

        df["Subject"] = df["Subject"].str.strip()
        exploded = df.assign(resident_id=df["Subject"].str.split(",")).explode("resident_id")
        exploded["resident_id"] = exploded["resident_id"].str.strip()
        exploded = exploded[exploded["resident_id"] != ""]

        frames.append(
            exploded[
                [
                    "session_id",
                    "timestamp",
                    "resident_id",
                    "sensor_type",
                    "room",
                    "event_value",
                    "activity_label",
                ]
            ]
        )

    events = pd.concat(frames, ignore_index=True)
    events = events.sort_values(["session_id", "timestamp"]).reset_index(drop=True)
    events["event_id"] = events["session_id"].astype(str) + "-" + events.index.astype(str)
    return events


# --- generic fallback loader (CSV/Parquet + explicit column mapping) -------

_READERS = {
    ".csv": pd.read_csv,
    ".parquet": pd.read_parquet,
    ".tsv": lambda p: pd.read_csv(p, sep="\t"),
}


def discover_source_files(raw_dir: str | Path) -> list[Path]:
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        return []
    return sorted(p for p in raw_dir.rglob("*") if p.is_file() and p.suffix.lower() in _READERS)


def _read_one(path: Path) -> pd.DataFrame:
    reader = _READERS[path.suffix.lower()]
    return reader(path)


def load_raw_events(raw_dir: str | Path, column_map: dict[str, str]) -> pd.DataFrame:
    """Load and concatenate flat CSV/Parquet MuRAL-like exports.

    Prefer `load_mural_dataset()` for the official MuRAL directory layout.
    This generic loader is a fallback for differently-shaped exports.
    """
    files = discover_source_files(raw_dir)
    if not files:
        raise FileNotFoundError(
            f"No MuRAL source files found under '{raw_dir}'. Follow "
            "data/source_instructions/mural_download.md to obtain the "
            "dataset and place it there before running build_benchmark.py."
        )

    frames = []
    for path in files:
        df = _read_one(path)
        missing = [src_col for src_col in column_map.values() if src_col not in df.columns]
        if missing:
            raise ValueError(
                f"{path} is missing expected column(s) {missing}. Update "
                "configs/benchmark.yaml -> data.column_map to match your "
                "local MuRAL export's column names."
            )
        renamed = df.rename(columns={v: k for k, v in column_map.items()})
        frames.append(renamed)

    events = pd.concat(frames, ignore_index=True)
    events = events[[c for c in CANONICAL_COLUMNS if c in events.columns]]

    if "activity_label" not in events.columns:
        events["activity_label"] = None

    events["timestamp"] = pd.to_datetime(events["timestamp"], utc=False, errors="coerce")
    if events["timestamp"].isna().any():
        bad = int(events["timestamp"].isna().sum())
        raise ValueError(f"{bad} event(s) have unparsable timestamps after loading MuRAL.")

    events = events.sort_values(["session_id", "timestamp"]).reset_index(drop=True)
    events["event_id"] = events["session_id"].astype(str) + "-" + events.index.astype(str)
    return events
