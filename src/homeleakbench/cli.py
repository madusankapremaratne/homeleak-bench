"""Thin CLI wrapper delegating to the scripts/ entry points."""

from __future__ import annotations

import runpy
import sys

import click

_SCRIPTS = {
    "build-benchmark": "scripts/build_benchmark.py",
    "validate-annotations": "scripts/validate_annotations.py",
    "run-pilot": "scripts/run_pilot.py",
    "run-models": "scripts/run_models.py",
    "evaluate": "scripts/evaluate_results.py",
    "tables": "scripts/generate_tables.py",
    "figures": "scripts/generate_figures.py",
}


@click.group()
def main() -> None:
    """HomeLeakBench command-line interface."""


def _make_command(name: str, script_path: str):
    @click.command(
        name=name,
        context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
    )
    @click.pass_context
    def _cmd(ctx: click.Context) -> None:
        sys.argv = [script_path, *ctx.args]
        runpy.run_path(script_path, run_name="__main__")

    return _cmd


for _name, _path in _SCRIPTS.items():
    main.add_command(_make_command(_name, _path))
