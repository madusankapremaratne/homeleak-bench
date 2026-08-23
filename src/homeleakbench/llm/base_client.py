"""Provider-agnostic LLM client interface and adapters.

Every client must implement `generate(system_prompt, user_prompt) -> str`
and return the raw text response. Structured-output parsing/validation
happens in `structured_output.py`, and response caching wraps whichever
client is selected — see `response_cache.py`.
"""

from __future__ import annotations

import json
import os
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class GenerationConfig:
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 300
    retries: int = 2
    seed: int = 42
    timeout_seconds: int = 60


class BaseLLMClient(ABC):
    def __init__(self, model_id: str, config: GenerationConfig):
        self.model_id = model_id
        self.config = config

    @abstractmethod
    def _call(self, system_prompt: str, user_prompt: str) -> str: ...

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        attempts = max(1, self.config.retries + 1)

        @retry(stop=stop_after_attempt(attempts), wait=wait_exponential(multiplier=1, max=10))
        def _run():
            return self._call(system_prompt, user_prompt)

        return _run()


class MockEchoClient(BaseLLMClient):
    """Deterministic, offline client for tests, dry runs, and CI.

    Picks the first non-abstention label deterministically from whatever
    label list appears in the prompt's "## Allowed labels" section, so the
    pipeline is fully runnable without any API keys.
    """

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        labels = self._extract_labels(user_prompt)
        is_activity = "activity_state" in user_prompt or "Activity Understanding" in user_prompt
        rng = random.Random(hash(user_prompt) % (2**32))
        answer = labels[0] if labels else "unknown"

        payload = {
            "confidence": round(0.5 + rng.random() * 0.4, 2),
            "abstain": False,
            "evidence": ["mock evidence"],
        }
        if is_activity:
            payload["activity_state"] = answer
        else:
            payload["answer"] = answer
        return json.dumps(payload)

    @staticmethod
    def _extract_labels(user_prompt: str) -> list[str]:
        if "## Allowed labels" not in user_prompt:
            return []
        section = user_prompt.split("## Allowed labels", 1)[1]
        section = section.split("##", 1)[0]
        return [line.strip("- ").strip() for line in section.splitlines() if line.strip()]


class AnthropicClient(BaseLLMClient):
    def __init__(
        self, model_id: str, config: GenerationConfig, api_key_env: str = "ANTHROPIC_API_KEY"
    ):
        super().__init__(model_id, config)
        self._api_key_env = api_key_env

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        import anthropic  # imported lazily so the base package has no hard dep

        api_key = os.environ.get(self._api_key_env)
        if not api_key:
            raise RuntimeError(f"Set {self._api_key_env} to call {self.model_id}.")

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=self.model_id,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class OpenAIClient(BaseLLMClient):
    def __init__(
        self, model_id: str, config: GenerationConfig, api_key_env: str = "OPENAI_API_KEY"
    ):
        super().__init__(model_id, config)
        self._api_key_env = api_key_env

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        from openai import OpenAI  # imported lazily so the base package has no hard dep

        api_key = os.environ.get(self._api_key_env)
        if not api_key:
            raise RuntimeError(f"Set {self._api_key_env} to call {self.model_id}.")

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=self.model_id,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_tokens=self.config.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""


class LocalOpenAICompatClient(BaseLLMClient):
    """For self-hosted/open-weight models exposed via an OpenAI-compatible endpoint."""

    def __init__(self, model_id: str, config: GenerationConfig, endpoint: str):
        super().__init__(model_id, config)
        self._endpoint = endpoint

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key="not-needed", base_url=self._endpoint)
        response = client.chat.completions.create(
            model=self.model_id,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_tokens=self.config.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""


def build_client(model_spec: dict, config: GenerationConfig) -> BaseLLMClient:
    provider = model_spec["provider"]
    model_id = model_spec["id"]

    if provider == "mock":
        return MockEchoClient(model_id, config)
    if provider == "anthropic":
        return AnthropicClient(model_id, config, model_spec.get("env_key", "ANTHROPIC_API_KEY"))
    if provider == "openai":
        return OpenAIClient(model_id, config, model_spec.get("env_key", "OPENAI_API_KEY"))
    if provider == "local":
        return LocalOpenAICompatClient(model_id, config, model_spec["endpoint"])

    raise ValueError(f"Unknown provider '{provider}' for model '{model_id}'.")
