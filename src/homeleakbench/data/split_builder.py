"""Split sessions into development/pilot/test partitions and hash IDs."""

from __future__ import annotations

import hashlib
import random


def hash_id(raw_id: str, salt: str = "homeleakbench") -> str:
    """Salted, truncated hash used to pseudonymize source identifiers."""
    digest = hashlib.sha256(f"{salt}:{raw_id}".encode()).hexdigest()
    return digest[:16]


def split_sessions(
    session_ids: list[str],
    ratios: dict[str, float],
    seed: int = 42,
) -> dict[str, str]:
    """Assign each session id to exactly one split, by ratio, deterministically."""
    total = sum(ratios.values())
    normalized = {k: v / total for k, v in ratios.items()}

    rng = random.Random(seed)
    shuffled = sorted(set(session_ids))
    rng.shuffle(shuffled)

    n = len(shuffled)
    assignment: dict[str, str] = {}
    cursor = 0
    items = list(normalized.items())
    for i, (split_name, ratio) in enumerate(items):
        if i == len(items) - 1:
            count = n - cursor
        else:
            count = round(ratio * n)
        for session_id in shuffled[cursor : cursor + count]:
            assignment[session_id] = split_name
        cursor += count

    return assignment
