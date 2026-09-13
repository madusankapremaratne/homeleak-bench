"""Render metrics DataFrames to LaTeX tables for the paper/ directory."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Short, readable labels for the raw model_id / task strings that appear
# in the metrics CSVs. Keeps generated tables narrow enough to fit a
# single-column page (e.g. Elsevier cas-sc, Springer LNCS) without manual
# per-venue editing, and avoids underscores that otherwise need the
# `underscore` LaTeX package to render safely.
MODEL_LABELS = {
    "llama3.2:latest": "Llama 3.2",
    "phi3.5:latest": "Phi-3.5",
    "qwen3-local:latest": "Qwen3",
    "gpt-oss:120b": "GPT-OSS-120B (Cloud)",
    "gemma4:31b": "Gemma4:31B",
    "openai/gpt-oss-120b": "GPT-OSS-120B (NVIDIA)",
    "deepseek-ai/deepseek-v4-flash-0731": "DeepSeek-V4-Flash",
}

TASK_LABELS = {
    "co_resident_activity": "co-resident activity",
    "occupancy_state": "occupancy state",
    "private_location": "private location",
    "resident_identity": "resident identity",
    "routine_inference": "routine inference",
    "activity_understanding": "activity understanding",
}

# Column-header labels for the metric/grouping fields that appear across
# the generated tables (as opposed to MODEL_LABELS/TASK_LABELS, which
# relabel cell *values*). Keeps every table's headers underscore-free and
# consistent, rather than leaking raw CSV column names like
# "privacy_leakage_rate" into the paper.
COLUMN_LABELS = {
    "model_id": "Model",
    "task": "Task",
    "context_level": "Context Level",
    "privacy_leakage_rate": "PLR",
    "utility_retention": "Utility Retention",
    "abstention_rate": "Abstention",
    "n_bins": "Bins",
    "ece": "ECE",
    "split": "Split",
    "n_items": "Items",
}


def relabel_for_display(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "model_id" in df.columns:
        df["model_id"] = df["model_id"].replace(MODEL_LABELS)
    if "task" in df.columns:
        df["task"] = df["task"].replace(TASK_LABELS)
    df.columns = [TASK_LABELS.get(c, c) if isinstance(c, str) else c for c in df.columns]
    df = df.rename(columns=COLUMN_LABELS)
    return df


def write_latex_table(df: pd.DataFrame, path: str | Path, caption: str, label: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    latex = df.to_latex(index=False, float_format="%.3f", caption=caption, label=label)
    # Force a placement hint so the float lands near wherever it's first
    # \ref{}'d in the surrounding prose rather than drifting to whatever
    # the document class's default float placement happens to choose
    # (which can push it well before any text explains it).
    latex = latex.replace("\\begin{table}", "\\begin{table}[!htb]", 1)
    # Shrink the tabular to fit the page width only if it's actually wider
    # than the page (e.g. a per-task-per-level breakdown with many
    # columns); a table that already fits is left at its natural size, so
    # it renders at the surrounding body-text font size rather than being
    # stretched up to fill \linewidth regardless of how few columns it has
    # (an unconditional \resizebox does that, and was the previous bug).
    latex = latex.replace(
        "\\begin{tabular}",
        "\\setbox0=\\hbox{\\begin{tabular}",
    ).replace(
        "\\end{tabular}",
        "\\end{tabular}}%\n"
        "\\ifdim\\wd0>\\linewidth\\resizebox{\\linewidth}{!}{\\copy0}\\else\\copy0\\fi",
    )
    path.write_text(latex, encoding="utf-8")


def benchmark_composition_table(items: pd.DataFrame) -> pd.DataFrame:
    """Summarize benchmark composition per split.

    Every (task, context_level) cell within a split has the same item
    count by construction (each level is a rendering of the same
    underlying windows), so a full split x task x level cross-tabulation
    is a long, uninformative table (e.g. 3 splits x 6 tasks x 5 levels =
    90 rows) that overflows a single-column page in a plain, non-breaking
    tabular. Report the per-split totals and the constant per-cell count
    instead; a reader who wants the full breakdown can regenerate it from
    the manifest files directly.
    """
    per_cell = items.groupby(["split", "task", "context_level"]).size()
    n_tasks = items["task"].nunique()
    n_levels = items["context_level"].nunique()
    summary = (
        items.groupby("split")
        .size()
        .reset_index(name="Items")
        .assign(
            Tasks=n_tasks,
            Levels=n_levels,
            **{"Items per (task, level)": lambda d: d["Items"] // (n_tasks * n_levels)},
        )
        .rename(columns={"split": "Split"})
    )
    # Sanity-check the "constant per cell" assumption rather than silently
    # hiding a real imbalance if the benchmark construction ever changes.
    if per_cell.groupby(level="split").nunique().gt(1).any():
        raise ValueError(
            "benchmark_composition_table: item counts per (task, context_level) "
            "cell are not constant within at least one split; the compact "
            "summary would misrepresent the actual composition."
        )
    return summary


def leakage_by_model_table(plr: pd.DataFrame) -> pd.DataFrame:
    table = plr.pivot_table(
        index=["model_id", "task"], columns="context_level", values="privacy_leakage_rate"
    ).reset_index()
    return table


def minimization_tradeoff_table(plr: pd.DataFrame, utility_retention: pd.DataFrame) -> pd.DataFrame:
    leakage_avg = (
        plr.groupby(["model_id", "context_level"])["privacy_leakage_rate"].mean().reset_index()
    )
    table = leakage_avg.merge(
        utility_retention[["model_id", "context_level", "utility_retention"]],
        on=["model_id", "context_level"],
        how="left",
    )
    return table


def calibration_and_abstention_table(ece: pd.DataFrame, abstention: pd.DataFrame) -> pd.DataFrame:
    abstention_avg = abstention.groupby("model_id")["abstention_rate"].mean().reset_index()
    table = ece.merge(abstention_avg, on="model_id", how="left")
    return table
