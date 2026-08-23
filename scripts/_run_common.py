"""Shared logic for run_pilot.py and run_models.py."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from homeleakbench.benchmark.privacy_tasks import PRIVACY_TASKS
from homeleakbench.benchmark.utility_tasks import UTILITY_TASKS
from homeleakbench.config import load_yaml
from homeleakbench.llm.base_client import GenerationConfig, build_client
from homeleakbench.llm.response_cache import CachedLLMClient
from homeleakbench.llm.structured_output import parse_model_output

TASK_SPECS = {**PRIVACY_TASKS, **UTILITY_TASKS}


def load_labels(*paths: str) -> pd.DataFrame:
    records = []
    for path in paths:
        p = Path(path)
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return pd.DataFrame(records)


def build_prompt(record: dict, prompts_config: dict) -> tuple[str, str]:
    task = record["task"]
    task_cfg = prompts_config["tasks"][task]
    spec = TASK_SPECS[task]

    system_prompt = Path(prompts_config["system_prompt"]).read_text(encoding="utf-8")
    template = Path(task_cfg["template"]).read_text(encoding="utf-8")

    labels_block = "\n".join(f"- {label}" for label in spec.labels)
    user_prompt = template.format(
        task_name=task,
        question=spec.question,
        narrative=record["narrative"],
        labels=labels_block,
    )
    return system_prompt, user_prompt


def run_generation_for_items(
    manifest: pd.DataFrame,
    labels: pd.DataFrame,
    benchmark_config: dict,
    models_config: dict,
    output_dir: str,
) -> pd.DataFrame:
    prompts_config = load_yaml("configs/prompts.yaml")
    schema = json.loads(
        Path(prompts_config["tasks"]["activity_understanding"]["schema"]).read_text()
    )

    gen_cfg = GenerationConfig(**models_config["generation"])
    cache_dir = models_config["cache"]["path"]
    cache_enabled = models_config["cache"]["enabled"]

    merged = manifest.merge(
        labels[["item_id", "narrative", "label"]].rename(columns={"label": "ground_truth"}),
        on="item_id",
        how="inner",
    )

    all_rows = []
    for model_spec in models_config["models"]:
        client = build_client(model_spec, gen_cfg)
        cached_client = CachedLLMClient(client, cache_dir, enabled=cache_enabled)
        model_out_dir = Path(output_dir) / model_spec["id"]
        model_out_dir.mkdir(parents=True, exist_ok=True)

        rows = []
        for _, record in merged.iterrows():
            system_prompt, user_prompt = build_prompt(record.to_dict(), prompts_config)
            response_text, cache_hit = cached_client.generate(system_prompt, user_prompt)
            parsed = parse_model_output(response_text, schema)

            rows.append(
                {
                    "model_id": model_spec["id"],
                    "item_id": record["item_id"],
                    "session_id": record["session_id"],
                    "task": record["task"],
                    "context_level": record["context_level"],
                    "split": record["split"],
                    "ground_truth": record["ground_truth"],
                    "prediction": parsed.answer,
                    "confidence": parsed.confidence,
                    "abstain": parsed.abstain,
                    "valid_json": parsed.valid_json,
                    "schema_valid": parsed.schema_valid,
                    "cache_hit": cache_hit,
                    "raw_response": parsed.raw_text,
                }
            )

        df = pd.DataFrame(rows)
        out_path = model_out_dir / "generations.jsonl"
        df.to_json(out_path, orient="records", lines=True)
        print(f"  {model_spec['id']}: wrote {len(df)} generations -> {out_path}")
        all_rows.append(df)

    return pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
