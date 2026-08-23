# Annotation Guidelines

HomeLeakBench labels are derived deterministically from MuRAL's structured
sensor/activity annotations rather than hand-labeled by new annotators —
see `src/homeleakbench/benchmark/label_derivation.py` for the exact rules
per task.

## Principles

1. **Ground truth comes from structured data, not narrative text.** Labels
   must not change across C0-C4 variants of the same window, since
   minimization only changes what's *said*, not the underlying facts.
2. **Abstention labels are first-class.** `unknown`/`uncertain` are valid
   ground-truth labels when the source data itself does not support a
   confident single-resident or single-room determination.
3. **No labels beyond observable state.** Do not derive health, emotional,
   or relationship labels from MuRAL annotations — see
   `docs/ethical_considerations.md`.

## Reviewing derived labels

Run `scripts/validate_annotations.py` after `scripts/build_benchmark.py`
to check that every derived record matches
`data/annotations/annotation_schema.json`. Spot-check a sample of
`data/annotations/privacy_labels.jsonl` and `utility_labels.jsonl` against
the corresponding MuRAL session before trusting a new derivation rule.
