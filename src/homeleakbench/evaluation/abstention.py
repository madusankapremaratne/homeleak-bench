"""Unsupported Inference Rate (UIR) and abstention-rate metrics."""

from __future__ import annotations

import pandas as pd


def _is_abstain(df: pd.DataFrame, sentinel_labels: set[str]) -> pd.Series:
    """True abstain flag, or a prediction of unknown/uncertain (etc.) that does
    NOT match the ground truth -- i.e. a genuine hedge, not a legitimate
    correct-or-incorrect answer that happens to be spelled the same as a
    sentinel label (e.g. "unknown" is a valid ground-truth class for
    resident_identity when a window has multiple residents).
    """
    sentinel_and_wrong = df["prediction"].isin(sentinel_labels) & (
        df["prediction"] != df["ground_truth"]
    )
    return df["abstain"] | sentinel_and_wrong


def unsupported_inference_rate(results: pd.DataFrame, sentinel_labels: set[str]) -> pd.DataFrame:
    """Rate of non-abstaining answers that are wrong and not a sentinel label."""
    df = results.copy()
    df["unsupported"] = (~_is_abstain(df, sentinel_labels)) & (
        df["prediction"] != df["ground_truth"]
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
    df["is_abstain"] = _is_abstain(df, sentinel_labels)

    grouped = (
        df.groupby(["model_id", "task", "context_level"])
        .agg(n_abstain=("is_abstain", "sum"), n_answers=("is_abstain", "count"))
        .reset_index()
    )
    grouped["abstention_rate"] = grouped["n_abstain"] / grouped["n_answers"]
    return grouped.drop(columns=["n_abstain"])
