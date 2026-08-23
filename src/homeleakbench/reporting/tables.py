"""Render metrics DataFrames to LaTeX tables for the paper/ directory."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_latex_table(df: pd.DataFrame, path: str | Path, caption: str, label: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    latex = df.to_latex(index=False, float_format="%.3f", caption=caption, label=label)
    path.write_text(latex, encoding="utf-8")


def benchmark_composition_table(items: pd.DataFrame) -> pd.DataFrame:
    return items.groupby(["split", "task", "context_level"]).size().reset_index(name="n_items")


def leakage_by_model_table(plr: pd.DataFrame) -> pd.DataFrame:
    return plr.pivot_table(
        index=["model_id", "task"], columns="context_level", values="privacy_leakage_rate"
    ).reset_index()


def minimization_tradeoff_table(plr: pd.DataFrame, utility_retention: pd.DataFrame) -> pd.DataFrame:
    leakage_avg = (
        plr.groupby(["model_id", "context_level"])["privacy_leakage_rate"].mean().reset_index()
    )
    return leakage_avg.merge(
        utility_retention[["model_id", "context_level", "utility_retention"]],
        on=["model_id", "context_level"],
        how="left",
    )


def calibration_and_abstention_table(ece: pd.DataFrame, abstention: pd.DataFrame) -> pd.DataFrame:
    abstention_avg = abstention.groupby("model_id")["abstention_rate"].mean().reset_index()
    return ece.merge(abstention_avg, on="model_id", how="left")
