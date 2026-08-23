#!/usr/bin/env python
"""Build C0-C4 benchmark items and manifests from a local MuRAL export.

Usage:
    python scripts/build_benchmark.py --config configs/benchmark.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd

from homeleakbench.benchmark.label_derivation import derive_all_labels
from homeleakbench.benchmark.minimization import apply_minimization, load_context_levels
from homeleakbench.config import load_yaml
from homeleakbench.data.event_windowing import build_windows
from homeleakbench.data.mural_parser import (
    discover_mural_session_dirs,
    load_mural_dataset,
    load_raw_events,
)
from homeleakbench.data.narrative_builder import build_narrative
from homeleakbench.data.split_builder import hash_id, split_sessions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_yaml(args.config)
    context_config = load_yaml(config["context_levels"])
    levels = load_context_levels(context_config)
    room_categories = context_config["room_categories"]
    time_periods = context_config["time_periods"]

    raw_dir = config["data"]["raw_dir"]
    print(f"[1/6] Loading MuRAL source events from {raw_dir} ...")
    if discover_mural_session_dirs(raw_dir):
        events = load_mural_dataset(raw_dir)
    else:
        events = load_raw_events(raw_dir, config["data"]["column_map"])
    print(f"      Loaded {len(events)} events across {events['session_id'].nunique()} sessions.")

    print("[2/6] Building fixed-duration context windows ...")
    windows = build_windows(
        events,
        window_seconds=config["windowing"]["window_seconds"],
        stride_seconds=config["windowing"]["stride_seconds"],
        min_events_per_window=config["windowing"]["min_events_per_window"],
        max_events_per_window=config["windowing"]["max_events_per_window"],
    )
    print(f"      Built {len(windows)} windows.")

    print("[3/6] Assigning session splits ...")
    session_ids = [w.session_id for w in windows]
    split_map = split_sessions(
        session_ids, config["splits"]["ratios"], seed=config["splits"]["seed"]
    )

    print("[4/6] Building narratives and deriving labels ...")
    privacy_records: list[dict] = []
    utility_records: list[dict] = []
    manifest_rows: list[dict] = []

    for window in windows:
        narrative = build_narrative(window)
        labels = derive_all_labels(window)
        split = split_map[window.session_id]
        source_hash = hash_id(window.session_id)

        for level_key, level_cfg in levels.items():
            minimized_text = apply_minimization(narrative, level_cfg, room_categories, time_periods)

            for task, label in labels.items():
                item_id = f"{window.window_id}-{task}-{level_key}"
                record = {
                    "item_id": item_id,
                    "session_id": source_hash,
                    "window_id": window.window_id,
                    "context_level": level_key,
                    "task": task,
                    "label": label,
                    "narrative": minimized_text,
                    "evidence_event_ids": (
                        window.events["event_id"].tolist()
                        if "event_id" in window.events.columns
                        else []
                    ),
                    "source_hash": source_hash,
                }
                if task == "activity_understanding":
                    utility_records.append(record)
                else:
                    privacy_records.append(record)

                manifest_rows.append(
                    {
                        "item_id": item_id,
                        "session_id": source_hash,
                        "window_id": window.window_id,
                        "context_level": level_key,
                        "task": task,
                        "split": split,
                    }
                )

    print(
        f"      Derived {len(privacy_records)} privacy labels and "
        f"{len(utility_records)} utility labels."
    )

    print("[5/6] Writing annotations ...")
    out = config["output"]
    Path(out["privacy_labels"]).parent.mkdir(parents=True, exist_ok=True)
    with open(out["privacy_labels"], "w", encoding="utf-8") as f:
        for r in privacy_records:
            f.write(json.dumps(r) + "\n")
    with open(out["utility_labels"], "w", encoding="utf-8") as f:
        for r in utility_records:
            f.write(json.dumps(r) + "\n")

    print("[6/6] Writing manifests ...")
    manifest_df = pd.DataFrame(manifest_rows)
    for split_name, path in out["manifest_files"].items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        manifest_df[manifest_df["split"] == split_name].to_csv(path, index=False)
        print(f"      {split_name}: {(manifest_df['split'] == split_name).sum()} items -> {path}")

    print("Done.")


if __name__ == "__main__":
    main()
