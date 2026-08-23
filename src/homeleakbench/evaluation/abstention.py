"""Unsupported Inference Rate (UIR) and abstention-rate metrics."""

from __future__ import annotations

import pandas as pd


def unsupported_inference_rate(results: pd.DataFrame, sentinel_labels: set[str]) -> pd.DataFrame:
    """Rate of non-abstaining answers that are wrong and not a sentinel label."""
    df = results.copy()
    df["unsupported"] = (
        (~df["abstain"])
        & (~df["prediction"].isin(sentinel_labels))
        & (df["prediction"] != df["ground_truth"])
    )

    grouped = (
        df.groupby(["model_id", "task", "context_level"])
        .agg(unsupported=("unsupported", "sum"), n_answers=("unsupported", "count"))
        .reset_index()
    )
    grouped["unsupported_inference_rate"] = grouped["unsupported"] / grouped["n_answers"]
    return grouped.drop(columns=["unsupported"])


def abstention_rate(results: pd.DataFrame, sentinel_labels: set[str]) -> pd.DataFrame:
    df = results.copy()
    df["is_abstain"] = df["abstain"] | df["prediction"].isin(sentinel_labels)

    grouped = (
        df.groupby(["model_id", "task", "context_level"])
        .agg(n_abstain=("is_abstain", "sum"), n_answers=("is_abstain", "count"))
        .reset_index()
    )
    grouped["abstention_rate"] = grouped["n_abstain"] / grouped["n_answers"]
    return grouped.drop(columns=["n_abstain"])
