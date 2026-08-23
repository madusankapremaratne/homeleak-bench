"""Matplotlib figures summarizing benchmark results."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def privacy_utility_frontier(tradeoff: pd.DataFrame, out_path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    for model_id, group in tradeoff.groupby("model_id"):
        group = group.sort_values("context_level")
        ax.plot(
            group["privacy_leakage_rate"], group["utility_retention"], marker="o", label=model_id
        )
        for _, row in group.iterrows():
            ax.annotate(
                row["context_level"], (row["privacy_leakage_rate"], row["utility_retention"])
            )

    ax.set_xlabel("Privacy Leakage Rate")
    ax.set_ylabel("Utility Retention")
    ax.set_title("Privacy-Utility Frontier across Context-Minimization Levels")
    ax.legend()
    _save(fig, out_path)


def leakage_by_privacy_target(plr: pd.DataFrame, out_path: str | Path) -> None:
    pivot = plr.pivot_table(index="task", columns="model_id", values="privacy_leakage_rate")
    fig, ax = plt.subplots(figsize=(7, 5))
    pivot.plot(kind="bar", ax=ax)
    ax.set_ylabel("Privacy Leakage Rate")
    ax.set_title("Leakage by Privacy-Inference Target")
    _save(fig, out_path)


def calibration_plot(reliability: pd.DataFrame, out_path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="perfect calibration")
    for model_id, group in reliability.groupby("model_id"):
        group = group.sort_values("bin_mean_confidence")
        ax.plot(group["bin_mean_confidence"], group["bin_accuracy"], marker="o", label=model_id)
    ax.set_xlabel("Mean predicted confidence")
    ax.set_ylabel("Empirical accuracy")
    ax.set_title("Calibration")
    ax.legend()
    _save(fig, out_path)


def _save(fig, out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
