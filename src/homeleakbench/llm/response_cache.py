"""File-based response cache keyed by (model_id, prompt hash, gen config)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from homeleakbench.llm.base_client import BaseLLMClient, GenerationConfig


def _cache_key(
    model_id: str, system_prompt: str, user_prompt: str, config: GenerationConfig
) -> str:
    payload = json.dumps(
        {
            "model_id": model_id,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "config": asdict(config),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CachedLLMClient:
    """Wraps a BaseLLMClient with an on-disk JSON cache."""

    def __init__(self, client: BaseLLMClient, cache_dir: str | Path, enabled: bool = True):
        self.client = client
        self.cache_dir = Path(cache_dir) / client.model_id
        self.enabled = enabled
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, bool]:
        """Returns (response_text, was_cache_hit)."""
        if not self.enabled:
            return self.client.generate(system_prompt, user_prompt), False

        key = _cache_key(self.client.model_id, system_prompt, user_prompt, self.client.config)
        cache_path = self.cache_dir / f"{key}.json"

        if cache_path.exists():
            record = json.loads(cache_path.read_text(encoding="utf-8"))
            return record["response"], True

        response = self.client.generate(system_prompt, user_prompt)
        cache_path.write_text(
            json.dumps(
                {"response": response, "system_prompt": system_prompt, "user_prompt": user_prompt}
            ),
            encoding="utf-8",
        )
        return response, False
