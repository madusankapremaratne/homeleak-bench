# Data Card: HomeLeakBench

## Source

Derived entirely from the **MuRAL** dataset (Chen, Cumin, Ramparany, and
Vaufreydaz), obtained separately by each user under MuRAL's own license —
see `data/source_instructions/mural_download.md`. This repository
redistributes only benchmark manifests, derived (pseudonymous) labels, and
generated narrative text — never raw MuRAL sensor exports.

## Composition

- 21+ hours of multi-resident smart-home sensor sessions.
- Windows of `windowing.window_seconds` (default 300s) built per session.
- 5 context-minimization variants (C0-C4) per window per task.
- 6 tasks: 5 privacy-inference tasks + 1 utility task.
- 3 splits: development, pilot, test — split by session, not by window, to
  avoid leakage between splits.

## Identifiers

Session and resident identifiers from MuRAL are salted-hashed
(`data/split_builder.py::hash_id`) before being written into any committed
artifact. Resident labels used in narratives (`Resident A`, `Resident B`)
are arbitrary per-session pseudonyms, not stable across sessions.

## Known limitations

See `README.md -> Limitations` and `docs/threat_model.md`.
