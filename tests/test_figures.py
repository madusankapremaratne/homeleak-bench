import pandas as pd

from homeleakbench.reporting.figures import _pool_reliability_across_tasks


def test_pool_reliability_across_tasks_weights_by_sample_count():
    """Regression test for the calibration-plot bug found in external
    review: reliability_bins() returns one row per (model, task, bin), so
    a plain groupby("model_id") over its output has multiple rows per bin
    (one per task) and connecting them draws a line that jumps between
    unrelated tasks' calibration summaries. Pooling must collapse to one
    row per bin, weighted by each task's sample count, not just averaged
    or concatenated.
    """
    # Two tasks share bin "b1": task A has 90 samples at (conf=0.9, acc=0.9),
    # task B has 10 samples at (conf=0.5, acc=0.1). The sample-weighted mean
    # must be much closer to task A's values than a plain unweighted mean.
    group = pd.DataFrame(
        [
            {
                "model_id": "m1",
                "task": "taskA",
                "bin": "b1",
                "bin_mean_confidence": 0.9,
                "bin_accuracy": 0.9,
                "n_samples": 90,
            },
            {
                "model_id": "m1",
                "task": "taskB",
                "bin": "b1",
                "bin_mean_confidence": 0.5,
                "bin_accuracy": 0.1,
                "n_samples": 10,
            },
            {
                "model_id": "m1",
                "task": "taskA",
                "bin": "b2",
                "bin_mean_confidence": 0.3,
                "bin_accuracy": 0.2,
                "n_samples": 5,
            },
        ]
    )
    pooled = _pool_reliability_across_tasks(group)

    assert len(pooled) == 2  # one row per bin, not per (task, bin)

    b1 = pooled[pooled["bin"] == "b1"].iloc[0]
    assert b1["n_samples"] == 100
    # Sample-weighted mean, not a plain average of 0.9 and 0.5 (which
    # would incorrectly give 0.7).
    assert abs(b1["bin_mean_confidence"] - 0.86) < 1e-9
    assert abs(b1["bin_accuracy"] - 0.82) < 1e-9

    b2 = pooled[pooled["bin"] == "b2"].iloc[0]
    assert b2["n_samples"] == 5
    assert abs(b2["bin_mean_confidence"] - 0.3) < 1e-9
