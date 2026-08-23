# data/

- `raw/` — local, uncommitted copy of MuRAL. See `source_instructions/mural_download.md`.
- `processed/` — intermediate parquet/CSV produced by `scripts/build_benchmark.py`.
- `manifests/` — `development.csv`, `pilot.csv`, `test.csv` benchmark item manifests (committed).
- `annotations/` — derived privacy/utility labels and the JSON schema they validate against.

Only `manifests/`, `annotations/`, and this documentation are meant to be
committed. `raw/` and `processed/` are git-ignored.
