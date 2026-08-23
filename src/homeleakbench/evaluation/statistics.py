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
