# Threat Model

## In scope

- An LLM receiving natural-language smart-home context (via a cloud API or
  local inference) that infers a privacy-sensitive household attribute
  (identity, occupancy, location privacy, routine, co-presence) beyond what
  the context's minimization level was intended to reveal.
- Measuring leakage across the C0-C4 minimization spectrum to quantify
  whether coarsening context actually reduces leakage.
- Measuring whether leakage reduction costs activity-understanding utility.

## Out of scope

- Prompt injection or adversarial manipulation of the household context
  itself.
- Endpoint/infrastructure compromise (API key theft, MITM, log exfiltration).
- Raw audio/video/biometric leakage — MuRAL and this benchmark use
  discrete sensor events only.
- Cross-session re-identification via stylometry or long-term behavioral
  fingerprinting.
- Any claim that a benchmark inference is true about a real person.

## Adversary model

The "adversary" here is the LLM's inference process itself under normal,
non-adversarial use (e.g. a household assistant summarizing sensor logs)
— not a human attacker crafting prompts. This benchmark measures
incidental/emergent inference, not intentional privacy attacks against the
model.
