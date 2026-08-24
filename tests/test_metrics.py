import pandas as pd

from homeleakbench.evaluation.abstention import abstention_rate, unsupported_inference_rate
from homeleakbench.evaluation.calibration import expected_calibration_error
from homeleakbench.evaluation.privacy_metrics import (
    high_confidence_leakage_rate,
    privacy_leakage_rate,
)
from homeleakbench.evaluation.utility_metrics import activity_utility, utility_retention


def _results():
    return pd.DataFrame(
        [
            {
                "model_id": "m1",
                "task": "occupancy_state",
                "context_level": "C0",
                "ground_truth": "one_resident_active",
                "prediction": "one_resident_active",
                "confidence": 0.9,
                "abstain": False,
            },
            {
                "model_id": "m1",
                "task": "occupancy_state",
                "context_level": "C0",
                "ground_truth": "multiple_residents_active",
                "prediction": "one_resident_active",
                "confidence": 0.6,
                "abstain": False,
            },
            {
                "model_id": "m1",
                "task": "occupancy_state",
                "context_level": "C4",
                "ground_truth": "one_resident_active",
                "prediction": "uncertain",
                "confidence": 0.3,
                "abstain": True,
            },
        ]
    )


def test_privacy_leakage_rate():
    plr = privacy_leakage_rate(_results())
    c0 = plr[(plr["model_id"] == "m1") & (plr["context_level"] == "C0")]
    assert c0["privacy_leakage_rate"].iloc[0] == 0.5


def test_high_confidence_leakage_rate():
    hclr = high_confidence_leakage_rate(_results(), tau=0.7)
    c0 = hclr[(hclr["model_id"] == "m1") & (hclr["context_level"] == "C0")]
    assert c0["hclr_tau_0.7"].iloc[0] == 0.5


def test_abstention_rate():
    abst = abstention_rate(_results(), sentinel_labels={"unknown", "uncertain"})
    c4 = abst[abst["context_level"] == "C4"]
    assert c4["abstention_rate"].iloc[0] == 1.0


def test_unsupported_inference_rate():
    uir = unsupported_inference_rate(_results(), sentinel_labels={"unknown", "uncertain"})
    c0 = uir[uir["context_level"] == "C0"]
    assert c0["unsupported_inference_rate"].iloc[0] == 0.5


def test_sentinel_label_matching_ground_truth_is_not_abstention():
    # "unknown" is a legitimate ground-truth class for some tasks (e.g.
    # resident_identity in a multi-resident window). A model that predicts
    # "unknown" without abstaining and is actually correct must not be
    # miscounted as an abstention or an unsupported inference.
    df = pd.DataFrame(
        [
            {
                "model_id": "m1",
                "task": "resident_identity",
                "context_level": "C1",
                "ground_truth": "unknown",
                "prediction": "unknown",
                "confidence": 0.8,
                "abstain": False,
            },
            {
                "model_id": "m1",
                "task": "resident_identity",
                "context_level": "C1",
                "ground_truth": "resident_A",
                "prediction": "unknown",
                "confidence": 0.5,
                "abstain": False,
            },
        ]
    )
    abst = abstention_rate(df, sentinel_labels={"unknown", "uncertain"})
    uir = unsupported_inference_rate(df, sentinel_labels={"unknown", "uncertain"})
    # Only the second row (predicted "unknown" but truth was "resident_A")
    # is a genuine hedge; the first is a real, correct, non-abstaining answer.
    assert abst["abstention_rate"].iloc[0] == 0.5
    assert uir["unsupported_inference_rate"].iloc[0] == 0.0


def test_activity_utility_and_retention():
    df = pd.DataFrame(
        [
            {
                "model_id": "m1",
                "task": "activity_understanding",
                "context_level": "C0",
                "ground_truth": "resting",
                "prediction": "resting",
                "confidence": 0.8,
                "abstain": False,
            },
            {
                "model_id": "m1",
                "task": "activity_understanding",
                "context_level": "C4",
                "ground_truth": "resting",
                "prediction": "cleaning_or_housework",
                "confidence": 0.8,
                "abstain": False,
            },
        ]
    )
    utility = activity_utility(df)
    retained = utility_retention(utility, reference_level="C0")
    c4 = retained[retained["context_level"] == "C4"]
    assert c4["utility_retention"].iloc[0] == 0.0


def test_expected_calibration_error_runs():
    ece = expected_calibration_error(_results(), n_bins=5)
    assert "ece" in ece.columns
    assert (ece["ece"] >= 0).all()
