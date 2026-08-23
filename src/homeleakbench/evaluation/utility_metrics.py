"""Activity Utility and Utility Retention metrics."""

from __future__ import annotations

import pandas as pd


def activity_utility(results: pd.DataFrame) -> pd.DataFrame:
    df = results[results["task"] == "activity_understanding"].copy()
    df["correct"] = (~df["abstain"]) & (df["prediction"] == df["ground_truth"])

    grouped = (
        df.groupby(["model_id", "context_level"])["correct"].agg(["sum", "count"]).reset_index()
    )
    grouped["activity_utility"] = grouped["sum"] / grouped["count"]
    return grouped.drop(columns=["sum"]).rename(columns={"count": "n_questions"})


def utility_retention(utility_df: pd.DataFrame, reference_level: str = "C0") -> pd.DataFrame:
    df = utility_df.copy()
    ref = df[df["context_level"] == reference_level].set_index("model_id")["activity_utility"]

    df["reference_activity_utility"] = df["model_id"].map(ref)
    df["utility_retention"] = df["activity_utility"] / df["reference_activity_utility"]
    return df
