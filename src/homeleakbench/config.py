"""Small helpers for loading YAML configs used across the pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_path(base_config_path: str | Path, relative: str) -> Path:
    """Resolve a path found inside a config file relative to the repo root.

    Config files store paths relative to the repository root (matching the
    `python scripts/*.py --config configs/...` invocation style), not
    relative to the config file itself.
    """
    return Path(relative)
