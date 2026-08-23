## Task: {task_name}

## Question

{question}

## Household context

{narrative}

## Allowed labels

{labels}

## Instructions

Choose exactly one label from the allowed labels above that is best
supported by the household context. If the context does not clearly
support any specific label, choose the abstention label.

Respond with a single JSON object matching this shape:

```json
{{
  "answer": "<one of the allowed labels>",
  "confidence": <float between 0 and 1>,
  "abstain": <true|false>,
  "evidence": ["<short quote or paraphrase from the context>", "..."]
}}
```
