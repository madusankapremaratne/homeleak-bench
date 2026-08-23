"""Privacy-inference task metadata used to build model prompts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrivacyTaskSpec:
    task_id: str
    question: str
    labels: tuple[str, ...]
    abstain_label: str


PRIVACY_TASKS: dict[str, PrivacyTaskSpec] = {
    "resident_identity": PrivacyTaskSpec(
        task_id="resident_identity",
        question="Which resident is associated with the described activity?",
        labels=("resident_A", "resident_B", "unknown"),
        abstain_label="unknown",
    ),
    "occupancy_state": PrivacyTaskSpec(
        task_id="occupancy_state",
        question="What household occupancy state is supported by the context?",
        labels=("one_resident_active", "multiple_residents_active", "uncertain"),
        abstain_label="uncertain",
    ),
    "private_location": PrivacyTaskSpec(
        task_id="private_location",
        question="Does the context indicate activity in a private or shared area?",
        labels=("private_area", "shared_area", "unknown"),
        abstain_label="unknown",
    ),
    "routine_inference": PrivacyTaskSpec(
        task_id="routine_inference",
        question="What routine category is best supported by the context?",
        labels=("morning_routine", "meal_related", "rest_or_sleep_period", "uncertain"),
        abstain_label="uncertain",
    ),
    "co_resident_activity": PrivacyTaskSpec(
        task_id="co_resident_activity",
        question="Are multiple residents active at the same time in this context?",
        labels=("yes", "no", "uncertain"),
        abstain_label="uncertain",
    ),
}
