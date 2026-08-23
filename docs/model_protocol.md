# Model Evaluation Protocol

All models are evaluated under identical conditions to keep comparisons
valid — enforced by `configs/models.yaml -> generation` and
`src/homeleakbench/llm/base_client.py`.

## Controls

| Control | Where enforced |
|---|---|
| Identical system prompt | `prompts/system_prompt.md`, loaded once per run |
| Identical task prompts | `prompts/privacy_inference.md`, `prompts/activity_utility.md` |
| Identical JSON output schema | `prompts/output_schema.json`, validated in `structured_output.py` |
| `temperature = 0`, fixed `top_p`/`max_tokens` | `configs/models.yaml -> generation` |
| Logged model id + provider | Every row in `generations.jsonl` carries `model_id` |
| Response caching | `llm/response_cache.py`, keyed on (model, prompt, config) hash |
| Retries are logged, not silent | `base_client.py` uses `tenacity` with bounded retries; cache records the final response only, so re-running with `--output` intact will not re-call a model that already produced a cached answer |
| Run provenance | `reporting/run_manifest.py` records config paths, git commit, model roster, and start time per run |

## Adding a model

1. Add an entry to `configs/models.yaml -> models` with an exact versioned
   `id` and a `provider` matching one supported in
   `llm/base_client.py::build_client` (`mock`, `anthropic`, `openai`, or
   `local` for any OpenAI-compatible endpoint).
2. Set the corresponding API key environment variable (see `env_key`).
3. Re-run `scripts/run_pilot.py` before a full `scripts/run_models.py` run.
