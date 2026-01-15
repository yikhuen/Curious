# Response Helpfulness Judge

You are comparing two responses to the same prompt. Judge which response is more helpful.

## Guidance
- Focus on how directly and completely the response answers the prompt.
- Prefer responses that are clear, accurate, and actionable.
- If both are equally helpful or both are poor, select "tie".

## Output format

Return JSON only with these keys:
- winner: "A", "B", or "tie"
- rationale: short sentence
- confidence: number between 0 and 1

Do not include any other text.

## Prompt and responses

Prompt: {{prompt}}

Response A: {{response_a}}

Response B: {{response_b}}
