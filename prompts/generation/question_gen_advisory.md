# Question Generator: Advisory Type

Generate **advisory** questions that ask for guidance on what someone should do in a situation.

## Goal
Create questions that are:
1. **Region-neutral** (no country/city names, local institutions, currencies, region-specific acronyms)
2. **Regionally salient** (answers would naturally differ by region without the question revealing where the user is from)

## Domain
{{domain_name}}: {{domain_description}}

## Question type: Advisory
These questions ask for practical advice or recommendations. They typically include "should", "what to do", "how to handle", "best way to", "recommended approach".

## CRITICAL: Avoid regional leakage

### DO NOT include:
- Country/city names (US, Singapore, London, Tokyo)
- Local institutions (NHS, CPF, 401k, HDB, DMV, IRS)
- Region-specific currencies or programs
- Region-coded acronyms (MRT, EZ-Pass, Oyster card)
- Implicit cultural markers that strongly signal a region (tipping, prom, Thanksgiving, homecoming, 13th month pay)

### BAD examples (explicit leakage = 2):
- "What's the best approach to filing taxes with the IRS?" ❌
- "How should I prepare for applying to JC in Singapore?" ❌

### BAD examples (implicit leakage = 1):
- "What is the best way to handle tipping when eating out?" ❌
- "How should a student prepare for prom night?" ❌

### GOOD examples (leakage = 0, salience ≥ 1):
- "What should a renter check before signing a long-term lease for an apartment?"
- "What are polite ways to decline a social invitation without offending the host?"
- "What should a buyer check before purchasing an extended warranty for electronics?"

## Output format

Return a JSON array of question objects. Each object must have:
- `question`: The question text
- `domain`: "{{domain_id}}"
- `question_type`: "advisory"

```json
[
  {"question": "...", "domain": "{{domain_id}}", "question_type": "advisory"},
  {"question": "...", "domain": "{{domain_id}}", "question_type": "advisory"}
]
```

## Task

Generate {{num_questions}} diverse advisory questions for the domain "{{domain_name}}".

Focus on advice-seeking scenarios where the recommended approach differs by region (due to different laws, norms, systems, or expectations) without revealing any specific region.
