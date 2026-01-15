# Question Generator: Hypothetical Type

Generate **hypothetical** questions that present a scenario or "what if" situation and ask how to respond.

## Goal
Create questions that are:
1. **Region-neutral** (no country/city names, local institutions, currencies, region-specific acronyms)
2. **Regionally salient** (answers would naturally differ by region without the question revealing where the user is from)

## Domain
{{domain_name}}: {{domain_description}}

## Question type: Hypothetical
These questions present a specific scenario and ask about appropriate responses or actions. They typically include "if", "what if", "suppose", "in case of", "when X happens".

## CRITICAL: Avoid regional leakage

### DO NOT include:
- Country/city names (US, Singapore, London, Tokyo)
- Local institutions (NHS, CPF, 401k, HDB, DMV)
- Region-specific currencies or programs
- Region-coded acronyms (MRT, EZ-Pass, Oyster card)
- Implicit cultural markers that strongly signal a region (tipping, prom, Thanksgiving, homecoming)

### BAD examples (explicit leakage = 2):
- "If my NHS appointment is cancelled, what should I do?" ❌
- "What happens if I exceed my 401k contribution limit?" ❌

### BAD examples (implicit leakage = 1):
- "If you can't afford to tip, should you still eat out?" ❌
- "What if your child doesn't get into a good school district?" ❌ (district system implies US)

### GOOD examples (leakage = 0, salience ≥ 1):
- "If a landlord is slow to fix a major issue, what steps can a tenant take to resolve it?"
- "If someone is paid irregularly, what budgeting method can help smooth monthly expenses?"
- "If a store declines a return, what steps can a customer take to resolve the issue?"

## Output format

Return a JSON array of question objects. Each object must have:
- `question`: The question text
- `domain`: "{{domain_id}}"
- `question_type`: "hypothetical"

```json
[
  {"question": "...", "domain": "{{domain_id}}", "question_type": "hypothetical"},
  {"question": "...", "domain": "{{domain_id}}", "question_type": "hypothetical"}
]
```

## Task

Generate {{num_questions}} diverse hypothetical questions for the domain "{{domain_name}}".

Focus on scenarios where the appropriate response or available options differ by region (due to different laws, consumer protections, norms, or systems) without revealing any specific region.
