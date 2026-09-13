#!/usr/bin/env python
"""Render LaTeX tables from computed metrics.

Usage:
    python scripts/generate_tables.py --input results/metrics/ --output results/tables/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd

from homeleakbench.reporting.tables import (
    benchmark_composition_table,
    calibration_and_abstention_table,
    leakage_by_model_table,
    minimization_tradeoff_table,
    relabel_for_display,
    write_latex_table,
)


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
    ece = pd.read_csv(metrics_dir / "calibration.csv")
    abstention = pd.read_csv(metrics_dir / "abstention.csv")

    manifest_paths = list(Path("data/manifests").glob("*.csv"))
    if manifest_paths:
        items = pd.concat((pd.read_csv(p) for p in manifest_paths), ignore_index=True)
        write_latex_table(
            relabel_for_display(benchmark_composition_table(items)),
            out_dir / "benchmark_composition.tex",
            caption="Benchmark composition by split, task, and context level.",
            label="tab:benchmark-composition",
        )

    write_latex_table(
        relabel_for_display(leakage_by_model_table(plr)),
        out_dir / "leakage_by_model.tex",
        caption="Privacy Leakage Rate by model, task, and context level.",
        label="tab:leakage-by-model",
    )

    write_latex_table(
        relabel_for_display(minimization_tradeoff_table(plr, utility)),
        out_dir / "minimization_tradeoff.tex",
        caption="Privacy leakage vs. utility retention across context-minimization levels.",
        label="tab:minimization-tradeoff",
    )

    write_latex_table(
        relabel_for_display(calibration_and_abstention_table(ece, abstention)),
        out_dir / "calibration_and_abstention.tex",
        caption="Expected Calibration Error and abstention rate by model.",
        label="tab:calibration-and-abstention",
    )

    print(f"Tables written to {out_dir}/")


if __name__ == "__main__":
    main()
