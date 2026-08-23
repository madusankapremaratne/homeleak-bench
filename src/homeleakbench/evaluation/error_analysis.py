"""Breakdowns of wrong/invalid model outputs for qualitative error analysis."""

from __future__ import annotations

import pandas as pd


def error_breakdown(results: pd.DataFrame) -> pd.DataFrame:
    df = results.copy()
    df["outcome"] = "correct"
    df.loc[df["abstain"], "outcome"] = "abstained"
    df.loc[(~df["abstain"]) & (df["prediction"] != df["ground_truth"]), "outcome"] = "incorrect"
    if "valid_json" in df.columns:
        df.loc[~df["valid_json"], "outcome"] = "invalid_output"

    return (
        df.groupby(["model_id", "task", "context_level", "outcome"])
        .size()
        .reset_index(name="count")
    )


def confusion_pairs(results: pd.DataFrame, task: str, model_id: str) -> pd.DataFrame:
    df = results[
        (results["task"] == task) & (results["model_id"] == model_id) & (~results["abstain"])
    ]
    return (
        df.groupby(["ground_truth", "prediction"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
