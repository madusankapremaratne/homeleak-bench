import numpy as np
import pandas as pd

from homeleakbench.evaluation.statistics import bootstrap_ci, cluster_bootstrap_ci


def test_cluster_bootstrap_matches_item_level_point_estimate():
    """The point estimate (plain mean) must be identical between item-level
    and cluster bootstrap -- only the interval width should differ."""
    df = pd.DataFrame(
        {
            "session_id": ["s1"] * 10 + ["s2"] * 10,
            "correct": [1] * 6 + [0] * 4 + [1] * 2 + [0] * 8,
        }
    )
    item_point, _, _ = bootstrap_ci(df["correct"], n_samples=500, seed=1)
    cluster_point, _, _ = cluster_bootstrap_ci(df, "correct", n_samples=500, seed=1)
    assert item_point == cluster_point == df["correct"].mean()


def test_cluster_bootstrap_is_wider_when_clusters_are_extreme():
    """Regression test for the statistical-independence issue found in
    external review: when all the signal is concentrated in a few
    extreme sessions (one session all successes, the rest all failures),
    an item-level bootstrap -- which can mix items across sessions in
    each resample -- understates the true uncertainty relative to a
    session-cluster bootstrap, which can only ever resample whole
    sessions and therefore sometimes drops the all-success session
    entirely, or duplicates it, producing a visibly wider interval.
    """
    n_sessions = 6
    items_per_session = 20
    session_ids = []
    correct = []
    for i in range(n_sessions):
        session_ids += [f"s{i}"] * items_per_session
        # Session 0 is all successes; every other session is all failures.
        correct += [1 if i == 0 else 0] * items_per_session
    df = pd.DataFrame({"session_id": session_ids, "correct": correct})

    _, item_lo, item_hi = bootstrap_ci(df["correct"], n_samples=2000, seed=7)
    _, cluster_lo, cluster_hi = cluster_bootstrap_ci(df, "correct", n_samples=2000, seed=7)

    item_width = item_hi - item_lo
    cluster_width = cluster_hi - cluster_lo
    assert cluster_width > item_width


def test_cluster_bootstrap_uses_specified_cluster_column():
    df = pd.DataFrame(
        {
            "grp": ["a", "a", "b", "b"],
            "correct": [1, 1, 0, 0],
        }
    )
    point, lo, hi = cluster_bootstrap_ci(df, "correct", cluster_col="grp", n_samples=200, seed=3)
    assert point == 0.5
    assert 0.0 <= lo <= hi <= 1.0
