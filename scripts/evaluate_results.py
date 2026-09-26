#!/usr/bin/env python
"""Compute all evaluation metrics from raw generations.

Usage:
    python scripts/evaluate_results.py --config configs/evaluation.yaml \
        --input results/raw_generations/ --output results/metrics/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd

from homeleakbench.config import load_yaml
from homeleakbench.evaluation.abstention import abstention_rate, unsupported_inference_rate
from homeleakbench.evaluation.calibration import expected_calibration_error, reliability_bins
from homeleakbench.evaluation.error_analysis import error_breakdown
from homeleakbench.evaluation.privacy_metrics import (
    _is_correct,
    high_confidence_leakage_rate,
    privacy_leakage_rate,
)
from homeleakbench.evaluation.statistics import cluster_bootstrap_metric_by_group
from homeleakbench.evaluation.utility_metrics import activity_utility, utility_retention

MIN_SESSIONS_FOR_CLUSTER_BOOTSTRAP = 5


def load_generations(input_dir: str) -> pd.DataFrame:
    frames = []
    for path in sorted(Path(input_dir).rglob("generations.jsonl")):
        frames.append(pd.read_json(path, lines=True))
    if not frames:
        raise FileNotFoundError(
            f"No generations.jsonl files found under {input_dir}. "
            "Run scripts/run_models.py (or run_pilot.py) first."
        )
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    config = load_yaml(args.config)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = load_generations(args.input)
    print(f"Loaded {len(results)} model responses.")

    tau = config["confidence_threshold"]
    sentinel_labels = set(config["abstention"]["sentinel_labels"])
    n_bins = config["calibration"]["n_bins"]
    reference_level = config["utility"]["reference_level"]

    privacy_results = results[results["task"] != "activity_understanding"]

    plr = privacy_leakage_rate(privacy_results, sentinel_labels)
    plr.to_csv(out_dir / "privacy_leakage.csv", index=False)

    hclr = high_confidence_leakage_rate(privacy_results, sentinel_labels, tau=tau)
    hclr.to_csv(out_dir / "privacy_leakage_high_confidence.csv", index=False)

    utility = activity_utility(results)
    utility = utility_retention(utility, reference_level=reference_level)
    utility.to_csv(out_dir / "utility_scores.csv", index=False)

    uir = unsupported_inference_rate(results, sentinel_labels)
    abst = abstention_rate(results, sentinel_labels)
    abst.to_csv(out_dir / "abstention.csv", index=False)
    uir.to_csv(out_dir / "unsupported_inference.csv", index=False)

    ece = expected_calibration_error(results, n_bins=n_bins)
    bins = reliability_bins(results, n_bins=n_bins)
    ece.to_csv(out_dir / "calibration.csv", index=False)
    bins.to_csv(out_dir / "calibration_bins.csv", index=False)

    errors = error_breakdown(results)
    errors.to_csv(out_dir / "error_analysis.csv", index=False)

    # Session-cluster bootstrap CI for PLR by context level, pooling all
    # models in this input directory together. Benchmark items are not
    # independent draws (a handful of source sessions, and a share of
    # items render to byte-identical prompts at high minimization
    # levels), so this resamples whole sessions rather than individual
    # items -- the standard cluster-bootstrap correction. `reliable=False`
    # flags context levels with too few distinct sessions for the
    # resampling distribution to be meaningful (e.g. the 2-session
    # Ollama Cloud pilot), rather than silently reporting a
    # narrow-looking interval that isn't actually informative.
    plr_df = privacy_results.copy()
    plr_df["correct"] = plr_df.apply(_is_correct, axis=1, sentinel_labels=sentinel_labels)
    cluster_ci = cluster_bootstrap_metric_by_group(
        plr_df, "correct", ["context_level"], n_samples=2000, seed=42
    )
    cluster_ci["reliable"] = cluster_ci["n_sessions"] >= MIN_SESSIONS_FOR_CLUSTER_BOOTSTRAP
    cluster_ci.to_csv(out_dir / "plr_cluster_bootstrap.csv", index=False)

    print(f"Metrics written to {out_dir}/")


if __name__ == "__main__":
    main()
