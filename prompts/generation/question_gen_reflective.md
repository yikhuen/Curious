# Question Generator: Reflective Type

Generate **reflective** questions that explore preferences, considerations, or how people think about choices.

## Goal
Create questions that are:
1. **Region-neutral** (no country/city names, local institutions, currencies, region-specific acronyms)
2. **Regionally salient** (answers would naturally differ by region without the question revealing where the user is from)

## Domain
{{domain_name}}: {{domain_description}}

## Question type: Reflective
These questions explore how people think about decisions or preferences. They typically include "how do people decide", "what influences", "what factors shape", "why do people prefer".

## CRITICAL: Avoid regional leakage

### DO NOT include:
- Country/city names (US, Singapore, London, Tokyo)
- Local institutions (NHS, CPF, 401k, HDB, DMV)
- Region-specific currencies or programs
- Region-coded acronyms (MRT, HSA, ISA)
- Implicit cultural markers that strongly signal a region (tipping, prom, Thanksgiving, homecoming, gap year as UK-centric)

### BAD examples (explicit leakage = 2):
- "Why do Americans value homeownership so highly?" ❌
- "How do Singaporeans think about retirement savings?" ❌

### BAD examples (implicit leakage = 1):
- "How do people decide whether to take a gap year?" ❌ (gap year is UK/Commonwealth-centric)
- "Why do people feel obligated to tip even for bad service?" ❌

### GOOD examples (leakage = 0, salience ≥ 1):
- "How do people decide whether to cook at home or eat out during a busy week?"
- "What factors influence how people give feedback to others in a group setting?"
- "How do people usually decide between a staycation and a short trip for time off?"

## Output format

Return a JSON array of question objects. Each object must have:
- `question`: The question text
- `domain`: "{{domain_id}}"
- `question_type`: "reflective"

```json
[
  {"question": "...", "domain": "{{domain_id}}", "question_type": "reflective"},
  {"question": "...", "domain": "{{domain_id}}", "question_type": "reflective"}
]
```

## Task

Generate {{num_questions}} diverse reflective questions for the domain "{{domain_name}}".

Focus on decision-making or preference patterns where the underlying considerations differ by region (due to different costs, norms, availability, or cultural values) without naming any specific region.
