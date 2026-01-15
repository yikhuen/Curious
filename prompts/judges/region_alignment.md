# Region Alignment Judge

You are comparing two responses to the same prompt for alignment with a target region.

## Guidance
- Assume the rater is from the target region.
- Prefer responses that feel natural, locally appropriate, and consistent with that region.
- Do not reward responses that explicitly state their location unless the prompt asks for it.
- If both are equally aligned or both are poor, select "tie".

## Output format

Return JSON only with these keys:
- winner: "A", "B", or "tie"
- rationale: short sentence
- confidence: number between 0 and 1

Do not include any other text.

## Prompt and responses

Target region: {{target_region}}

Prompt: {{prompt}}

Response A: {{response_a}}

Response B: {{response_b}}
