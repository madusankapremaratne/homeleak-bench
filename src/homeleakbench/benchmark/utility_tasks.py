"""Utility-task metadata used to build model prompts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UtilityTaskSpec:
    task_id: str
    question: str
    labels: tuple[str, ...]
    abstain_label: str


UTILITY_TASKS: dict[str, UtilityTaskSpec] = {
    "activity_understanding": UtilityTaskSpec(
        task_id="activity_understanding",
        question="What high-level household activity is best supported by the context?",
        labels=(
            "cooking_or_meal_preparation",
            "resting",
            "cleaning_or_housework",
            "leaving_or_returning",
        ),
        abstain_label="uncertain",
    ),
}
