#!/usr/bin/env python
"""Run the full benchmark (development + test splits) against configured models.

Usage:
    python scripts/run_models.py --config configs/benchmark.yaml \
        --models configs/models.yaml --output results/raw_generations/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from _run_common import load_labels, run_generation_for_items

from homeleakbench.config import load_yaml
from homeleakbench.reporting.run_manifest import create_run_manifest, write_run_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--models", required=True)
    parser.add_argument("--output", default="results/raw_generations/")
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["development", "test"],
        help="Which manifest splits to run (default: development test).",
    )
    args = parser.parse_args()

    config = load_yaml(args.config)
    models_config = load_yaml(args.models)
    labels = load_labels(config["output"]["privacy_labels"], config["output"]["utility_labels"])

    manifests = []
    for split in args.splits:
        path = config["output"]["manifest_files"][split]
        df = pd.read_csv(path)
        if df.empty:
            print(f"Warning: '{split}' manifest at {path} is empty; skipping.")
            continue
        manifests.append(df)

    if not manifests:
        print(
            "No non-empty manifests found. Run scripts/build_benchmark.py "
            "first to generate benchmark items from your local MuRAL data."
        )
        return

    manifest = pd.concat(manifests, ignore_index=True)
    model_ids = [m["id"] for m in models_config["models"]]

    run_manifest = create_run_manifest(
        run_id=pd.Timestamp.now("UTC").strftime("run-%Y%m%dT%H%M%SZ"),
        config_paths={"benchmark": args.config, "models": args.models},
        models=model_ids,
    )
    write_run_manifest(run_manifest, "results/run_manifests")

    print(f"Running {len(manifest)} items x {len(model_ids)} models (splits: {args.splits}) ...")
    run_generation_for_items(manifest, labels, config, models_config, args.output)
    print("Run complete.")


if __name__ == "__main__":
    main()
