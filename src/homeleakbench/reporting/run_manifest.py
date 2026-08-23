"""Records provenance for a benchmark run: config, models, timestamps."""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RunManifest:
    run_id: str
    started_at: str
    config_paths: dict[str, str]
    models: list[str]
    git_commit: str | None = None
    python_version: str = field(default_factory=platform.python_version)
    notes: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def _current_git_commit() -> str | None:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        return None


def create_run_manifest(
    run_id: str, config_paths: dict[str, str], models: list[str]
) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        started_at=datetime.now(timezone.utc).isoformat(),
        config_paths=config_paths,
        models=models,
        git_commit=_current_git_commit(),
    )


def write_run_manifest(manifest: RunManifest, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{manifest.run_id}.json"
    path.write_text(manifest.to_json(), encoding="utf-8")
    return path
