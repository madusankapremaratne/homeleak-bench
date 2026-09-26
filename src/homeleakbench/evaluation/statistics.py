"""Bootstrap confidence intervals for rate-style metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def bootstrap_ci(
    values: pd.Series,
    n_samples: int = 2000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Returns (point_estimate, ci_low, ci_high) for the mean of a binary/rate series."""
    arr = values.to_numpy(dtype=float)
    if len(arr) == 0:
        return float("nan"), float("nan"), float("nan")

    rng = np.random.default_rng(seed)
    point = arr.mean()

    boot_means = np.empty(n_samples)
    n = len(arr)
    for i in range(n_samples):
        sample = rng.choice(arr, size=n, replace=True)
        boot_means[i] = sample.mean()

    alpha = 1 - confidence_level
    lo = np.quantile(boot_means, alpha / 2)
    hi = np.quantile(boot_means, 1 - alpha / 2)
    return float(point), float(lo), float(hi)


def bootstrap_metric_by_group(
    results: pd.DataFrame,
    correct_col: str,
    group_cols: list[str],
    n_samples: int = 2000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> pd.DataFrame:
    rows = []
    for key, group in results.groupby(group_cols):
        point, lo, hi = bootstrap_ci(
            group[correct_col], n_samples=n_samples, confidence_level=confidence_level, seed=seed
        )
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_cols, key_tuple, strict=True))
        row.update({"estimate": point, "ci_low": lo, "ci_high": hi, "n": len(group)})
        rows.append(row)
    return pd.DataFrame(rows)


def cluster_bootstrap_ci(
    results: pd.DataFrame,
    correct_col: str,
    cluster_col: str = "session_id",
    n_samples: int = 2000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Session-cluster bootstrap CI for the mean of a binary/rate column.

    `bootstrap_ci` resamples individual items, treating every row as an
    independent draw. Benchmark items are not independent: they come from
    a small number of source sessions (up to 21, as few as 6 for the test
    split alone), and a non-trivial share render to byte-identical prompts
    at high minimization levels (see the collision-rate note in
    Limitations), so item-level resampling can understate the true
    uncertainty. This instead resamples whole *sessions* with replacement
    -- so all of a resampled session's items move together in each
    bootstrap draw -- which is the standard cluster-bootstrap correction
    for this kind of within-cluster dependence.
    """
    sessions = results[cluster_col].unique()
    if len(sessions) == 0:
        return float("nan"), float("nan"), float("nan")

    point = results[correct_col].to_numpy(dtype=float).mean()

    # Precompute each session's (sum, count) once so each bootstrap draw
    # is just an index lookup, not a fresh groupby/filter over the full
    # item-level data.
    per_session = results.groupby(cluster_col)[correct_col].agg(["sum", "count"])
    sums = per_session["sum"].to_numpy(dtype=float)
    counts = per_session["count"].to_numpy(dtype=float)
    n_sessions = len(sums)

    rng = np.random.default_rng(seed)
    boot_means = np.empty(n_samples)
    for i in range(n_samples):
        idx = rng.integers(0, n_sessions, size=n_sessions)
        boot_means[i] = sums[idx].sum() / counts[idx].sum()

    alpha = 1 - confidence_level
    lo = np.quantile(boot_means, alpha / 2)
    hi = np.quantile(boot_means, 1 - alpha / 2)
    return float(point), float(lo), float(hi)


def cluster_bootstrap_metric_by_group(
    results: pd.DataFrame,
    correct_col: str,
    group_cols: list[str],
    cluster_col: str = "session_id",
    n_samples: int = 2000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> pd.DataFrame:
    rows = []
    for key, group in results.groupby(group_cols):
        point, lo, hi = cluster_bootstrap_ci(
            group,
            correct_col,
            cluster_col=cluster_col,
            n_samples=n_samples,
            confidence_level=confidence_level,
            seed=seed,
        )
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_cols, key_tuple, strict=True))
        row.update(
            {
                "estimate": point,
                "ci_low": lo,
                "ci_high": hi,
                "n_items": len(group),
                "n_sessions": group[cluster_col].nunique(),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)
