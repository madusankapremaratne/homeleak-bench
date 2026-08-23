#!/usr/bin/env python
"""Run the benchmark's pilot split against the configured models.

Usage:
    python scripts/run_pilot.py --config configs/benchmark.yaml --models configs/models.yaml
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--models", required=True)
    parser.add_argument("--output", default="results/raw_generations/pilot")
    args = parser.parse_args()

    config = load_yaml(args.config)
    models_config = load_yaml(args.models)

    manifest = pd.read_csv(config["output"]["manifest_files"]["pilot"])
    labels = load_labels(config["output"]["privacy_labels"], config["output"]["utility_labels"])

    if manifest.empty:
        print(
            "Pilot manifest is empty. Run scripts/build_benchmark.py first "
            "to generate benchmark items from your local MuRAL data."
        )
        return

    print(f"Running pilot: {len(manifest)} items x {len(models_config['models'])} models ...")
    run_generation_for_items(manifest, labels, config, models_config, args.output)
    print("Pilot run complete.")


if __name__ == "__main__":
    main()
