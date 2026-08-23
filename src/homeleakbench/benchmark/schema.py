"""Pydantic models for benchmark items and label records."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

ContextLevel = Literal["C0", "C1", "C2", "C3", "C4"]

PrivacyTask = Literal[
    "resident_identity",
    "occupancy_state",
    "private_location",
    "routine_inference",
    "co_resident_activity",
]
UtilityTask = Literal["activity_understanding"]
Task = PrivacyTask | UtilityTask


class LabelRecord(BaseModel):
    item_id: str
    session_id: str
    window_id: str
    context_level: ContextLevel
    task: Task
    label: str
    narrative: str
    evidence_event_ids: list[str] = []
    source_hash: str


class BenchmarkItem(BaseModel):
    item_id: str
    session_id: str
    window_id: str
    context_level: ContextLevel
    task: Task
    split: Literal["development", "pilot", "test"]
