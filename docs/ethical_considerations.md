# Ethical Considerations

HomeLeakBench measures whether LLMs infer privacy-sensitive *but
observable* household states (occupancy, room use, routine, co-presence)
from smart-home context. It intentionally excludes:

- Health condition inference.
- Family/relationship inference.
- Emotional or personality trait inference.
- Real-identity re-identification.

If you extend the task set, keep new tasks grounded in attributes that are
directly derivable from MuRAL's own structured annotations
(`label_derivation.py`), not speculative attributes an LLM might merely
*claim* to infer. Do not use benchmark predictions as evidence about real
people — see the "Scope limitation" section of the root `README.md`.

## Responsible extension checklist

- [ ] New label is derived deterministically from source structured data.
- [ ] New label does not fall into a prohibited category (see README).
- [ ] Source identifiers remain hashed in any released artifact.
- [ ] Narrative generation does not leak raw resident/session identifiers
      at C1 and above.
