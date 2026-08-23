"""Confidence calibration: reliability bins and Expected Calibration Error."""

from __future__ import annotations

import numpy as np
import pandas as pd


def reliability_bins(results: pd.DataFrame, n_bins: int = 10) -> pd.DataFrame:
    df = results.dropna(subset=["confidence"]).copy()
    df["correct"] = (~df["abstain"]) & (df["prediction"] == df["ground_truth"])
    df["confidence"] = df["confidence"].clip(0, 1)

    bin_edges = np.linspace(0, 1, n_bins + 1)
    df["bin"] = pd.cut(df["confidence"], bins=bin_edges, include_lowest=True)

    rows = []
    for (model_id, task, bin_), group in df.groupby(["model_id", "task", "bin"], observed=True):
        if len(group) == 0:
            continue
        rows.append(
            {
                "model_id": model_id,
                "task": task,
                "bin": str(bin_),
                "bin_mean_confidence": group["confidence"].mean(),
                "bin_accuracy": group["correct"].mean(),
                "n_samples": len(group),
            }
        )
    return pd.DataFrame(rows)


def expected_calibration_error(results: pd.DataFrame, n_bins: int = 10) -> pd.DataFrame:
    bins = reliability_bins(results, n_bins=n_bins)
    rows = []
    for model_id, group in bins.groupby("model_id"):
        total = group["n_samples"].sum()
        ece = (
            (group["n_samples"] / total)
            * (group["bin_mean_confidence"] - group["bin_accuracy"]).abs()
        ).sum()
        rows.append({"model_id": model_id, "n_bins": n_bins, "ece": ece})
    return pd.DataFrame(rows)
