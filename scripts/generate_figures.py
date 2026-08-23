#!/usr/bin/env python
"""Render figures from computed metrics.

Usage:
    python scripts/generate_figures.py --input results/metrics/ --output results/figures/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd

from homeleakbench.reporting.figures import (
    calibration_plot,
    leakage_by_privacy_target,
    privacy_utility_frontier,
)
from homeleakbench.reporting.tables import minimization_tradeoff_table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    metrics_dir = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    plr = pd.read_csv(metrics_dir / "privacy_leakage.csv")
    utility = pd.read_csv(metrics_dir / "utility_scores.csv")
    bins = pd.read_csv(metrics_dir / "calibration_bins.csv")

    tradeoff = minimization_tradeoff_table(plr, utility)
    privacy_utility_frontier(tradeoff, out_dir / "privacy_utility_frontier.pdf")
    leakage_by_privacy_target(plr, out_dir / "leakage_by_privacy_target.pdf")
    calibration_plot(bins, out_dir / "calibration_plot.pdf")

    print(f"Figures written to {out_dir}/")


if __name__ == "__main__":
    main()
