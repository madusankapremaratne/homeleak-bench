## Task: Activity Understanding

## Question

What high-level household activity is best supported by the context below?

## Household context

{narrative}

## Allowed labels

{labels}

## Instructions

Choose exactly one label from the allowed labels above. This task
measures whether context minimization preserves useful activity
understanding, so answer as accurately as the given context allows.

Respond with a single JSON object matching this shape:

```json
{{
  "activity_state": "<one of the allowed labels>",
  "confidence": <float between 0 and 1>,
  "abstain": <true|false>,
  "evidence": ["<short quote or paraphrase from the context>", "..."]
}}
```
