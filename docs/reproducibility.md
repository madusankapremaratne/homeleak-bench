# Reproducibility

## Determinism controls

- `configs/benchmark.yaml -> splits.seed` fixes session-split assignment.
- `configs/models.yaml -> generation` fixes `temperature=0`, `top_p`,
  `max_tokens`, and `seed` for every model call.
- `configs/evaluation.yaml -> statistics.bootstrap_seed` fixes bootstrap
  confidence-interval resampling.
- All model responses are cached under `results/cached_outputs/<model_id>/`
  keyed by a hash of `(model_id, system_prompt, user_prompt, generation
  config)` — re-running a script never silently re-queries a model for a
  prompt it has already answered under the same config.

## End-to-end reproduction

```bash
python scripts/build_benchmark.py --config configs/benchmark.yaml
python scripts/validate_annotations.py --input data/annotations/privacy_labels.jsonl
python scripts/run_pilot.py --config configs/benchmark.yaml --models configs/models.yaml
python scripts/run_models.py --config configs/benchmark.yaml --models configs/models.yaml --output results/raw_generations/
python scripts/evaluate_results.py --config configs/evaluation.yaml --input results/raw_generations/ --output results/metrics/
python scripts/generate_tables.py --input results/metrics/ --output results/tables/
python scripts/generate_figures.py --input results/metrics/ --output results/figures/
```

Each `run_models.py` invocation also writes a manifest to
`results/run_manifests/<run_id>.json` recording the exact config paths,
model roster, git commit, and timestamp for that run.

## What is NOT reproducible without external access

- Exact MuRAL source data (must be obtained independently; see
  `data/source_instructions/mural_download.md`).
- Cloud model responses if the underlying API model version changes after
  your run (log the exact model id/version from `results/run_manifests/`).
