# Obtaining MuRAL

HomeLeakBench does not redistribute the MuRAL dataset. Obtain it directly
from the official project page and comply with its license.

## Steps

1. Visit the MuRAL project page: https://mural.imag.fr/
2. Download the dataset export (a `MuRAL.zip` archive).
3. Extract it so that `data/raw/mural/` directly contains the per-session
   folders and top-level metadata files, e.g.:

   ```text
   data/raw/mural/
   ├── 01/
   │   ├── data.csv
   │   └── context.json
   ├── 02/
   │   ├── data.csv
   │   └── context.json
   ├── ...
   ├── sensors.json
   ├── activities.json
   └── floorplan.png
   ```

   (If the archive extracts into an intermediate `MuRAL/` directory, move
   its contents up one level so `data/raw/mural/01/data.csv` etc. is a
   direct child.)

## Native format

`src/homeleakbench/data/mural_parser.py::load_mural_dataset()` parses this
layout directly — no column mapping is needed for the official export.

- **`<session>/data.csv`** — one row per sensor event, columns:
  `uid, time, sensor, action, Subject, Description, activity`.
  - `time` is `HH:MM:SS` with no date; the parser assigns each session a
    synthetic distinct base date and rolls the date forward on any
    midnight wraparound within a session, purely to keep timestamps
    orderable.
  - `sensor` packs `"<room> <sensor description>"` (e.g. `"bedroom_1
    door"`, `"dining room chair_1 contact"`, `"main door"`); the parser
    splits this into `room` and infers a coarse `sensor_type`
    (`door`/`motion`/`appliance`/`contact`/`other`).
  - `Subject` may list multiple residents for a shared action (e.g.
    `"A, B"`); the parser explodes these into one row per resident.
  - `activity` is a numeric id resolved against the dataset-wide
    `activities.json`.
- **`<session>/context.json`** — session metadata (`start time`, `day`,
  `resident number`, `roles`, `scenario`). Not currently consumed by the
  pipeline beyond session discovery, but useful for manual QA.
- **`sensors.json`** — sensor metadata (not required by the parser).

## If your export is shaped differently

If you obtain a MuRAL export in a different (flat CSV/Parquet) shape,
`load_raw_events()` in the same module is a generic fallback driven by
`configs/benchmark.yaml -> data.column_map`. `scripts/build_benchmark.py`
automatically uses the native loader when it finds `NN/data.csv` +
`NN/context.json` session directories, and falls back to the generic
loader otherwise.

## Data policy reminders

- Do not commit anything under `data/raw/` to version control (already
  covered by `.gitignore`).
- Hash source session/resident identifiers before publishing any derived
  benchmark artifact (`split_builder.py` does this automatically — see
  `configs/benchmark.yaml`).
- Comply with MuRAL's license terms for any redistribution of derived
  narratives or labels.
